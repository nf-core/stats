"""DLT pipeline for Nextflow strict syntax linting across nf-core."""

from collections.abc import Iterator
from datetime import datetime, timezone
from typing import Annotated

import dlt

from ._logging import log_pipeline_stats, logger
from .strict_syntax.fetch import fetch_pipelines
from .strict_syntax.history import create_history_entry
from .strict_syntax.lint import workflow_output_state
from .strict_syntax.modules import (
    discover_modules,
    discover_subworkflows,
    lint_modules,
    lint_subworkflows,
    prepare_modules_repo,
)
from .strict_syntax.nextflow import get_nextflow_sha, get_nextflow_version
from .strict_syntax.pipelines import lint_pipelines


def _history_row(
    *,
    component_type: str,
    date: str,
    nextflow_version: str,
    nextflow_sha: str,
    entry: dict,
) -> dict:
    return {
        "date": date,
        "component_type": component_type,
        "nextflow_version": nextflow_version,
        "nextflow_sha": nextflow_sha,
        **entry,
    }


@dlt.resource(write_disposition="replace", primary_key=["pipeline_name"])
def strict_syntax_pipelines_resource(
    rows: list[dict],
    *,
    nextflow_version: str,
    nextflow_sha: str,
) -> Iterator[dict]:
    now = datetime.now(timezone.utc).isoformat()
    for row in rows:
        yield {
            "pipeline_name": row["name"],
            "full_name": row["full_name"],
            "html_url": row["html_url"],
            "parse_error": row.get("parse_error", False),
            "errors": row.get("errors") if not row.get("parse_error") else None,
            "warnings": row.get("warnings") if not row.get("parse_error") else None,
            "prints_help": row.get("prints_help"),
            "workflow_output": row.get("workflow_output"),
            "publishdir": row.get("publishdir"),
            "workflow_output_state": workflow_output_state(row),
            "commit_sha": row.get("commit_sha"),
            "nextflow_sha": nextflow_sha,
            "nextflow_version": nextflow_version,
            "lint_output": row.get("lint_output"),
            "help_output": row.get("help_output"),
            "updated_at": now,
        }


@dlt.resource(write_disposition="replace", primary_key=["module_name"])
def strict_syntax_modules_resource(
    rows: list[dict],
    *,
    nextflow_version: str,
    nextflow_sha: str,
    repo_commit: str | None,
) -> Iterator[dict]:
    now = datetime.now(timezone.utc).isoformat()
    for row in rows:
        yield {
            "module_name": row["name"],
            "html_url": row["html_url"],
            "parse_error": row.get("parse_error", False),
            "errors": row.get("errors") if not row.get("parse_error") else None,
            "warnings": row.get("warnings") if not row.get("parse_error") else None,
            "commit_sha": repo_commit,
            "nextflow_sha": nextflow_sha,
            "nextflow_version": nextflow_version,
            "lint_output": row.get("lint_output"),
            "updated_at": now,
        }


@dlt.resource(write_disposition="replace", primary_key=["subworkflow_name"])
def strict_syntax_subworkflows_resource(
    rows: list[dict],
    *,
    nextflow_version: str,
    nextflow_sha: str,
    repo_commit: str | None,
) -> Iterator[dict]:
    now = datetime.now(timezone.utc).isoformat()
    for row in rows:
        yield {
            "subworkflow_name": row["name"],
            "html_url": row["html_url"],
            "parse_error": row.get("parse_error", False),
            "errors": row.get("errors") if not row.get("parse_error") else None,
            "warnings": row.get("warnings") if not row.get("parse_error") else None,
            "commit_sha": repo_commit,
            "nextflow_sha": nextflow_sha,
            "nextflow_version": nextflow_version,
            "lint_output": row.get("lint_output"),
            "updated_at": now,
        }


@dlt.resource(write_disposition="merge", primary_key=["date", "component_type"])
def strict_syntax_history_resource(history_rows: list[dict]) -> Iterator[dict]:
    yield from history_rows


@dlt.source(name="strict_syntax")
def strict_syntax_source(
    *,
    pipelines_filter: list[str] | None = None,
    modules_filter: list[str] | None = None,
    subworkflows_filter: list[str] | None = None,
    skip_pipelines: bool = False,
    skip_modules: bool = False,
    skip_subworkflows: bool = False,
    no_cache: bool = False,
):
    """Collect strict syntax lint results for nf-core pipelines, modules, and subworkflows."""
    state = dlt.current.source_state()
    nf_version = get_nextflow_version()
    nf_sha = get_nextflow_sha()
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    logger.info("Nextflow version: %s (sha: %s)", nf_version, nf_sha[:8])

    resources = []
    history_rows: list[dict] = []

    if not skip_pipelines:
        pipelines = fetch_pipelines()
        if pipelines_filter:
            pipelines = [row for row in pipelines if row["name"] in pipelines_filter]
            logger.info("Filtered to %d pipelines", len(pipelines))

        pipeline_snapshot = state.setdefault("pipelines_snapshot", {})
        pipeline_rows, pipeline_snapshot = lint_pipelines(
            pipelines,
            snapshot=pipeline_snapshot,
            nextflow_version=nf_version,
            no_cache=no_cache,
        )
        state["pipelines_snapshot"] = pipeline_snapshot

        resources.append(
            strict_syntax_pipelines_resource(pipeline_rows, nextflow_version=nf_version, nextflow_sha=nf_sha)
        )
        if not pipelines_filter:
            entry = create_history_entry(pipeline_rows, include_prints_help=True)
            history_rows.append(
                _history_row(
                    component_type="pipelines",
                    date=date,
                    nextflow_version=nf_version,
                    nextflow_sha=nf_sha,
                    entry=entry,
                )
            )

    if not skip_modules or not skip_subworkflows:
        modules_snapshot = state.setdefault("modules_snapshot", {})
        repo_unchanged, repo_commit = prepare_modules_repo(
            snapshot=modules_snapshot,
            no_cache=no_cache,
            check_modules=not skip_modules,
            check_subworkflows=not skip_subworkflows,
        )

        if not skip_modules:
            if repo_unchanged and not modules_filter:
                discovered = discover_modules()
                module_rows = [
                    {
                        "name": item["name"],
                        "html_url": item["html_url"],
                        "errors": modules_snapshot.get("modules", {}).get(item["name"], {}).get("errors", 0),
                        "warnings": modules_snapshot.get("modules", {}).get(item["name"], {}).get("warnings", 0),
                        "parse_error": modules_snapshot.get("modules", {})
                        .get(item["name"], {})
                        .get("parse_error", False),
                        "lint_output": modules_snapshot.get("modules", {})
                        .get(item["name"], {})
                        .get("lint_output"),
                    }
                    for item in discovered
                ]
            else:
                modules = discover_modules()
                if modules_filter:
                    modules = [row for row in modules if row["name"] in modules_filter]
                module_rows, module_data = lint_modules(
                    modules,
                    snapshot=modules_snapshot.get("modules", {}),
                    nextflow_version=nf_version,
                    no_cache=no_cache or bool(modules_filter),
                )
                modules_snapshot["modules"] = module_data
                if repo_commit:
                    modules_snapshot["_repo_commit"] = repo_commit
                state["modules_snapshot"] = modules_snapshot

            resources.append(
                strict_syntax_modules_resource(
                    module_rows,
                    nextflow_version=nf_version,
                    nextflow_sha=nf_sha,
                    repo_commit=modules_snapshot.get("_repo_commit"),
                )
            )
            if not modules_filter:
                entry = create_history_entry(module_rows)
                history_rows.append(
                    _history_row(
                        component_type="modules",
                        date=date,
                        nextflow_version=nf_version,
                        nextflow_sha=nf_sha,
                        entry=entry,
                    )
                )

        if not skip_subworkflows:
            if repo_unchanged and not subworkflows_filter:
                discovered = discover_subworkflows()
                subworkflow_rows = [
                    {
                        "name": item["name"],
                        "html_url": item["html_url"],
                        "errors": modules_snapshot.get("subworkflows", {}).get(item["name"], {}).get("errors", 0),
                        "warnings": modules_snapshot.get("subworkflows", {})
                        .get(item["name"], {})
                        .get("warnings", 0),
                        "parse_error": modules_snapshot.get("subworkflows", {})
                        .get(item["name"], {})
                        .get("parse_error", False),
                        "lint_output": modules_snapshot.get("subworkflows", {})
                        .get(item["name"], {})
                        .get("lint_output"),
                    }
                    for item in discovered
                ]
            else:
                subworkflows = discover_subworkflows()
                if subworkflows_filter:
                    subworkflows = [row for row in subworkflows if row["name"] in subworkflows_filter]
                subworkflow_rows, subworkflow_data = lint_subworkflows(
                    subworkflows,
                    snapshot=modules_snapshot.get("subworkflows", {}),
                    nextflow_version=nf_version,
                    no_cache=no_cache or bool(subworkflows_filter),
                )
                modules_snapshot["subworkflows"] = subworkflow_data
                if repo_commit:
                    modules_snapshot["_repo_commit"] = repo_commit
                state["modules_snapshot"] = modules_snapshot

            resources.append(
                strict_syntax_subworkflows_resource(
                    subworkflow_rows,
                    nextflow_version=nf_version,
                    nextflow_sha=nf_sha,
                    repo_commit=modules_snapshot.get("_repo_commit"),
                )
            )
            if not subworkflows_filter:
                entry = create_history_entry(subworkflow_rows)
                history_rows.append(
                    _history_row(
                        component_type="subworkflows",
                        date=date,
                        nextflow_version=nf_version,
                        nextflow_sha=nf_sha,
                        entry=entry,
                    )
                )

    if history_rows:
        resources.append(strict_syntax_history_resource(history_rows))

    return resources


def _split_csv(value: str | None) -> list[str] | None:
    if not value:
        return None
    items = [part.strip() for part in value.split(",") if part.strip()]
    return items or None


def main(
    *,
    destination: str = "motherduck",
    pipelines: Annotated[str | None, "Comma-separated pipeline names to lint"] = None,
    modules: Annotated[str | None, "Comma-separated module names to lint"] = None,
    subworkflows: Annotated[str | None, "Comma-separated subworkflow names to lint"] = None,
    skip_pipelines: Annotated[bool, "Skip linting pipelines"] = False,
    skip_modules: Annotated[bool, "Skip linting modules"] = False,
    skip_subworkflows: Annotated[bool, "Skip linting subworkflows"] = False,
    no_cache: Annotated[bool, "Ignore commit cache and re-lint everything"] = False,
    backfill_history: Annotated[str | None, "Path to strict-syntax-health lint_results directory"] = None,
):
    """Run strict syntax linting and load results into MotherDuck."""
    logger.info("Starting strict-syntax linting pipeline...")

    if backfill_history:
        from .strict_syntax.backfill import load_history_backfill

        history_rows = load_history_backfill(backfill_history)
        pipeline = dlt.pipeline(
            pipeline_name="strict_syntax_pipeline",
            destination=destination,
            dataset_name="strict_syntax",
        )
        load_info = pipeline.run(strict_syntax_history_resource(history_rows))
        log_pipeline_stats(pipeline, load_info)
        logger.info("History backfill completed!")
        return

    pipeline = dlt.pipeline(
        pipeline_name="strict_syntax_pipeline",
        destination=destination,
        dataset_name="strict_syntax",
    )

    load_info = pipeline.run(
        strict_syntax_source(
            pipelines_filter=_split_csv(pipelines),
            modules_filter=_split_csv(modules),
            subworkflows_filter=_split_csv(subworkflows),
            skip_pipelines=skip_pipelines,
            skip_modules=skip_modules,
            skip_subworkflows=skip_subworkflows,
            no_cache=no_cache,
        )
    )

    log_pipeline_stats(pipeline, load_info)
    logger.info("Strict-syntax linting pipeline completed successfully!")
