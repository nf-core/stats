"""DLT pipeline for strict-syntax linting of nf-core pipelines.

This pipeline:
1. Fetches the list of nf-core pipelines from nf-co.re
2. Clones each pipeline and runs `nextflow lint`
3. Stores results in MotherDuck for visualization in Evidence.dev
"""

import json
import subprocess
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

import dlt
import httpx

from ._logging import log_pipeline_stats, logger

PIPELINES_URL = "https://nf-co.re/pipelines.json"
PIPELINES_DIR = Path("pipelines")
NEXTFLOW_REPO = "https://github.com/nextflow-io/nextflow.git"


def get_nextflow_sha() -> str:
    """Get Nextflow HEAD commit SHA from remote."""
    result = subprocess.run(
        ["git", "ls-remote", NEXTFLOW_REPO, "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.split()[0]


def get_remote_head_sha(repo_url: str) -> str | None:
    """Get HEAD commit SHA from remote without cloning."""
    try:
        # Try dev branch first
        result = subprocess.run(
            ["git", "ls-remote", repo_url, "refs/heads/dev"],
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout.strip():
            return result.stdout.split()[0]
        # Fallback to default branch
        result = subprocess.run(
            ["git", "ls-remote", repo_url, "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.split()[0] if result.stdout.strip() else None
    except subprocess.CalledProcessError:
        return None


def get_nextflow_version() -> str:
    """Get the current nextflow version."""
    try:
        result = subprocess.run(["nextflow", "-version"], capture_output=True, text=True, check=False)
        for line in result.stdout.split("\n"):
            if "version" in line.lower():
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.lower() == "version" and i + 1 < len(parts):
                        return parts[i + 1]
    except FileNotFoundError:
        logger.warning("Nextflow not found in PATH")
    return "unknown"


def fetch_pipelines() -> list[dict]:
    """Fetch pipeline list from nf-co.re."""
    logger.info(f"Fetching pipelines from {PIPELINES_URL}")
    response = httpx.get(PIPELINES_URL, timeout=60)
    response.raise_for_status()
    data = response.json()

    pipelines = []
    for pipeline in data.get("remote_workflows", []):
        if pipeline.get("archived", False):
            continue
        pipelines.append({
            "name": pipeline["name"],
            "full_name": pipeline["full_name"],
            "html_url": f"https://github.com/{pipeline['full_name']}",
        })

    logger.info(f"Found {len(pipelines)} active pipelines")
    return pipelines


def clone_pipeline(pipeline: dict) -> Path:
    """Clone a pipeline repository, preferring the 'dev' branch."""
    repo_path = PIPELINES_DIR / pipeline["name"]

    if repo_path.exists():
        logger.debug(f"Pipeline already cloned: {pipeline['name']}")
        try:
            subprocess.run(
                ["git", "-C", str(repo_path), "fetch", "--quiet", "origin", "dev"],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(repo_path), "checkout", "--quiet", "dev"],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            pass
        subprocess.run(
            ["git", "-C", str(repo_path), "pull", "--quiet"],
            check=True,
            capture_output=True,
        )
    else:
        logger.info(f"Cloning {pipeline['full_name']}...")
        PIPELINES_DIR.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                ["git", "clone", "--quiet", "--depth", "1", "--branch", "dev", pipeline["html_url"], str(repo_path)],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            subprocess.run(
                ["git", "clone", "--quiet", "--depth", "1", pipeline["html_url"], str(repo_path)],
                check=True,
                capture_output=True,
            )

    return repo_path


def lint_pipeline(repo_path: Path) -> dict:
    """Run nextflow lint on a pipeline (JSON output for parsing)."""
    result = subprocess.run(
        ["nextflow", "lint", ".", "-o", "json"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=False,
    )

    try:
        lint_result = json.loads(result.stdout)
        lint_result["parse_error"] = False
        return lint_result
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse lint output for {repo_path.name}")
        logger.debug(f"stdout: {result.stdout}")
        logger.debug(f"stderr: {result.stderr}")
        return {"summary": {"errors": 0}, "errors": [], "warnings": [], "parse_error": True}


@dlt.source(name="strict_syntax")
def strict_syntax_source(pipelines_filter: list[str] | None = None):
    """DLT source for strict-syntax linting data."""
    logger.info("Initialized strict-syntax linting source")

    # Get dlt state for caching
    state = dlt.current.source_state()
    last_analyzed = state.setdefault("last_analyzed", {})

    nf_version = get_nextflow_version()
    nf_sha = get_nextflow_sha()
    logger.info(f"Nextflow version: {nf_version} (sha: {nf_sha[:8]})")

    pipelines = fetch_pipelines()
    if pipelines_filter:
        filter_set = set(pipelines_filter)
        pipelines = [p for p in pipelines if p["name"] in filter_set]
        logger.info(f"Filtered to {len(pipelines)} pipelines: {', '.join(p['name'] for p in pipelines)}")

    # Run linting and collect results
    results = []
    skipped = 0
    for pipeline in pipelines:
        name = pipeline["name"]
        repo_url = pipeline["html_url"]

        # Check if we can skip this pipeline
        pipeline_sha = get_remote_head_sha(repo_url)
        cached = last_analyzed.get(name, {})
        if (
            pipeline_sha
            and cached.get("nf_sha") == nf_sha
            and cached.get("pipeline_sha") == pipeline_sha
        ):
            logger.info(f"Skipping unchanged: {name}")
            skipped += 1
            continue

        logger.info(f"Processing {name}...")
        try:
            repo_path = clone_pipeline(pipeline)
            lint_result = lint_pipeline(repo_path)
            results.append({
                "name": name,
                "full_name": pipeline["full_name"],
                "html_url": repo_url,
                "errors": lint_result.get("summary", {}).get("errors", 0),
                "warnings": len(lint_result.get("warnings", [])),
                "parse_error": lint_result.get("parse_error", False),
                "commit_sha": pipeline_sha,
                "nextflow_sha": nf_sha,
            })
            # Update state on success
            last_analyzed[name] = {"nf_sha": nf_sha, "pipeline_sha": pipeline_sha}
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to process {name}: {e}")
            results.append({
                "name": name,
                "full_name": pipeline["full_name"],
                "html_url": repo_url,
                "errors": 0,
                "warnings": 0,
                "parse_error": True,
                "commit_sha": pipeline_sha,
                "nextflow_sha": nf_sha,
            })

    logger.info(f"Processed {len(results)} pipelines, skipped {skipped} unchanged")

    return [
        dlt.resource(strict_syntax_history(results, nf_version, nf_sha), name="strict_syntax_history"),
        dlt.resource(strict_syntax_pipelines(results), name="strict_syntax_pipelines"),
    ]


@dlt.resource(write_disposition="merge", primary_key=["date"])
def strict_syntax_history(results: list[dict], nf_version: str, nf_sha: str) -> Iterator[dict]:
    """Generate aggregated history entry from lint results."""
    valid_results = [r for r in results if not r.get("parse_error", False)]
    parse_error_count = sum(1 for r in results if r.get("parse_error", False))

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    yield {
        "date": today,
        "nextflow_version": nf_version,
        "nextflow_sha": nf_sha,
        "total_pipelines": len(results),
        "parse_errors": parse_error_count,
        "errors_zero": sum(1 for r in valid_results if r["errors"] == 0),
        "errors_low": sum(1 for r in valid_results if 0 < r["errors"] <= 5),
        "errors_high": sum(1 for r in valid_results if r["errors"] > 5),
        "warnings_zero": sum(1 for r in valid_results if r["warnings"] == 0),
        "warnings_low": sum(1 for r in valid_results if 0 < r["warnings"] <= 20),
        "warnings_high": sum(1 for r in valid_results if r["warnings"] > 20),
        "total_errors": sum(r["errors"] for r in valid_results),
        "total_warnings": sum(r["warnings"] for r in valid_results),
    }


@dlt.resource(write_disposition="replace", primary_key=["pipeline_name"])
def strict_syntax_pipelines(results: list[dict]) -> Iterator[dict]:
    """Generate per-pipeline lint results."""
    for r in results:
        yield {
            "pipeline_name": r["name"],
            "full_name": r["full_name"],
            "html_url": r["html_url"],
            "parse_error": r["parse_error"],
            "errors": r["errors"] if not r["parse_error"] else None,
            "warnings": r["warnings"] if not r["parse_error"] else None,
            "commit_sha": r.get("commit_sha"),
            "nextflow_sha": r.get("nextflow_sha"),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }


def main(
    *,
    destination: str = "motherduck",
    pipelines: Annotated[str | None, "Comma-separated list of pipelines to lint"] = None,
):
    """Run the strict-syntax linting pipeline.

    Args:
        destination: dlt backend. Use 'motherduck' for production. Can use 'duckdb' for local testing
        pipelines: Optional comma-separated list of pipeline names to lint (default: all)
    """
    logger.info("Starting strict-syntax linting pipeline...")

    pipelines_filter = None
    if pipelines:
        pipelines_filter = [p.strip() for p in pipelines.split(",") if p.strip()]

    pipeline = dlt.pipeline(
        pipeline_name="strict_syntax_pipeline",
        destination=destination,
        dataset_name="strict_syntax",
    )

    load_info = pipeline.run(strict_syntax_source(pipelines_filter))

    log_pipeline_stats(pipeline, load_info)

    logger.info("Strict-syntax linting pipeline completed successfully!")
