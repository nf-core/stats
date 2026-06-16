"""Backfill historical strict syntax data from strict-syntax-health JSON files."""

import json
from pathlib import Path


def load_history_backfill(lint_results_dir: str) -> list[dict]:
    """Load history JSON files exported from nf-core/strict-syntax-health."""
    base = Path(lint_results_dir)
    rows: list[dict] = []

    mapping = {
        "pipelines_history.json": "pipelines",
        "modules_history.json": "modules",
        "subworkflows_history.json": "subworkflows",
    }

    for filename, component_type in mapping.items():
        path = base / filename
        if not path.exists():
            continue
        history = json.loads(path.read_text())
        for entry in history:
            rows.append(
                {
                    "date": entry["date"],
                    "component_type": component_type,
                    "nextflow_version": entry.get("nextflow_version", "unknown"),
                    "nextflow_sha": entry.get("nextflow_sha", "unknown"),
                    "total": entry["total"],
                    "parse_errors": entry["parse_errors"],
                    "errors_zero": entry["errors_zero"],
                    "errors_low": entry["errors_low"],
                    "errors_high": entry["errors_high"],
                    "warnings_zero": entry["warnings_zero"],
                    "warnings_low": entry["warnings_low"],
                    "warnings_high": entry["warnings_high"],
                    "total_errors": entry.get("total_errors"),
                    "total_warnings": entry.get("total_warnings"),
                    "prints_help_pass": entry.get("prints_help_pass"),
                    "prints_help_fail": entry.get("prints_help_fail"),
                    "workflow_output_pass": entry.get("workflow_output_pass"),
                    "workflow_output_warn": entry.get("workflow_output_warn"),
                    "workflow_output_error": entry.get("workflow_output_error"),
                }
            )

    return rows
