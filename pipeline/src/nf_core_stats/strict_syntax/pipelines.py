import subprocess
from pathlib import Path

from .._logging import logger
from .git_utils import get_local_commit_hash, get_remote_head_sha
from .lint import (
    detect_publishdir,
    detect_workflow_output,
    generate_markdown_from_issues,
    lint_component,
    test_prints_help,
)
from .paths import PIPELINES_DIR


def clone_pipeline(pipeline: dict, pipelines_dir: Path = PIPELINES_DIR) -> Path:
    repo_path = pipelines_dir / pipeline["name"]

    if repo_path.exists():
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
        logger.info("Cloning %s...", pipeline["full_name"])
        pipelines_dir.mkdir(parents=True, exist_ok=True)
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


def _cached_pipeline_row(pipeline: dict, cached: dict, commit: str) -> dict:
    return {
        "name": pipeline["name"],
        "full_name": pipeline["full_name"],
        "html_url": pipeline["html_url"],
        "commit_sha": commit,
        "errors": cached["errors"],
        "warnings": cached["warnings"],
        "parse_error": cached.get("parse_error", False),
        "prints_help": cached.get("prints_help"),
        "workflow_output": cached.get("workflow_output"),
        "publishdir": cached.get("publishdir"),
        "lint_output": cached.get("lint_output"),
    }


def _needs_reprocess(cached: dict) -> bool:
    needs_prints_help = (
        cached.get("errors", 0) == 0
        and not cached.get("parse_error", False)
        and cached.get("prints_help") is None
    )
    needs_output_detection = cached.get("workflow_output") is None or cached.get("publishdir") is None
    return needs_prints_help or needs_output_detection


def lint_pipelines(
    pipelines: list[dict],
    *,
    snapshot: dict[str, dict],
    nextflow_version: str,
    no_cache: bool = False,
) -> tuple[list[dict], dict[str, dict]]:
    """Lint pipelines, reusing snapshot entries when remote commit is unchanged."""
    updated_snapshot = dict(snapshot)
    results: list[dict] = []
    skipped = 0
    linted = 0

    for pipeline in pipelines:
        name = pipeline["name"]
        cached = updated_snapshot.get(name)
        remote_commit = get_remote_head_sha(pipeline["html_url"])

        if (
            not no_cache
            and cached
            and remote_commit
            and remote_commit == cached.get("commit_sha")
            and not _needs_reprocess(cached)
        ):
            row = _cached_pipeline_row(pipeline, cached, remote_commit)
            results.append(row)
            skipped += 1
            continue

        logger.info("Linting pipeline %s...", name)
        try:
            repo_path = clone_pipeline(pipeline)
            commit_hash = get_local_commit_hash(repo_path)
            lint_result = lint_component(repo_path)
            error_count = lint_result.get("summary", {}).get("errors", 0)
            warning_count = len(lint_result.get("warnings", []))
            parse_error = lint_result.get("parse_error", False)
            workflow_output = detect_workflow_output(repo_path)
            publishdir = detect_publishdir(repo_path)

            prints_help = None
            help_output = None
            if not parse_error and error_count == 0:
                prints_help, help_output = test_prints_help(repo_path)

            lint_output = None
            if not parse_error:
                lint_output = generate_markdown_from_issues(
                    lint_result.get("errors", []),
                    lint_result.get("warnings", []),
                    nextflow_version,
                    repo_path,
                )

            row = {
                "name": name,
                "full_name": pipeline["full_name"],
                "html_url": pipeline["html_url"],
                "commit_sha": commit_hash,
                "errors": error_count,
                "warnings": warning_count,
                "parse_error": parse_error,
                "prints_help": prints_help,
                "workflow_output": workflow_output,
                "publishdir": publishdir,
                "lint_output": lint_output,
                "help_output": help_output,
            }
            linted += 1
        except subprocess.CalledProcessError as exc:
            logger.error("Failed to process %s: %s", name, exc)
            row = {
                "name": name,
                "full_name": pipeline["full_name"],
                "html_url": pipeline["html_url"],
                "commit_sha": remote_commit,
                "errors": 0,
                "warnings": 0,
                "parse_error": True,
                "prints_help": None,
                "workflow_output": None,
                "publishdir": None,
                "lint_output": None,
                "help_output": None,
            }
            linted += 1

        updated_snapshot[name] = {key: value for key, value in row.items() if key != "name"}
        results.append(row)

    logger.info("Pipelines: skipped %d unchanged, linted %d", skipped, linted)
    return results, updated_snapshot
