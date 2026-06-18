#!/usr/bin/env -S uv run python
"""Seed a local DuckDB database with strict syntax demo data."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

import duckdb


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _workflow_report(name: str, output_count: int, publishdir_count: int) -> str:
    return "\n".join(
        [
            "# Workflow outputs migration report",
            "",
            f"- Pipeline: {name}",
            "- Nextflow version: 26.04.3",
            f"- `output {{}}` matches: {output_count}",
            f"- `publishDir` matches: {publishdir_count}",
            "",
            "## `output {}` matches",
            "",
            "- `workflows/main.nf:1`: `output {}`" if output_count else "- No matches found",
            "",
            "## `publishDir` matches",
            "",
            "- `conf/modules.config:12`: `publishDir = ...`" if publishdir_count else "- No matches found",
        ]
    )


def _lint_output(name: str, errors: int, warnings: int) -> str:
    summary = "No issues found" if errors == 0 and warnings == 0 else f"{errors} errors, {warnings} warnings"
    return "\n".join(
        [
            "# Nextflow lint results",
            "",
            "- Nextflow version: 26.04.3",
            f"- Pipeline: {name}",
            f"- Summary: {summary}",
            "",
            "## Errors",
            "",
            "- `main.nf:42:1`: example strict syntax error" if errors else "- No errors found",
            "",
            "## Warnings",
            "",
            "- `modules.config:18:1`: example strict syntax warning" if warnings else "- No warnings found",
        ]
    )


def _history_rows(now: datetime) -> list[tuple]:
    today = now.date().isoformat()
    yesterday = (now - timedelta(days=1)).date().isoformat()
    return [
        (yesterday, "pipelines", "26.04.2", "demo-sha", 4, 0, 2, 1, 1, 1, 1, 2, 130, 520, 2, 1, 0, 1, 3),
        (today, "pipelines", "26.04.3", "demo-sha", 4, 0, 3, 0, 1, 1, 1, 2, 117, 1153, 2, 1, 1, 1, 2),
        (yesterday, "modules", "26.04.2", "demo-sha", 5, 0, 5, 0, 0, 3, 1, 1, 0, 10, 0, 0, None, None, None),
        (today, "modules", "26.04.3", "demo-sha", 5, 0, 5, 0, 0, 3, 2, 0, 0, 8, 0, 0, None, None, None),
        (yesterday, "subworkflows", "26.04.2", "demo-sha", 3, 0, 3, 0, 0, 1, 1, 1, 0, 22, 0, 0, None, None, None),
        (today, "subworkflows", "26.04.3", "demo-sha", 3, 0, 3, 0, 0, 1, 2, 0, 0, 16, 0, 0, None, None, None),
    ]


def seed(database: Path) -> None:
    now = _utc_now()
    database.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(database))
    conn.execute("CREATE SCHEMA IF NOT EXISTS strict_syntax")
    conn.execute(
        """
        CREATE OR REPLACE TABLE strict_syntax.strict_syntax_history (
            date DATE,
            component_type VARCHAR,
            nextflow_version VARCHAR,
            nextflow_sha VARCHAR,
            total INTEGER,
            parse_errors INTEGER,
            errors_zero INTEGER,
            errors_low INTEGER,
            errors_high INTEGER,
            warnings_zero INTEGER,
            warnings_low INTEGER,
            warnings_high INTEGER,
            total_errors INTEGER,
            total_warnings INTEGER,
            prints_help_pass INTEGER,
            prints_help_fail INTEGER,
            workflow_output_pass INTEGER,
            workflow_output_warn INTEGER,
            workflow_output_error INTEGER
        )
        """
    )
    conn.executemany(
        "INSERT INTO strict_syntax.strict_syntax_history VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        _history_rows(now),
    )

    pipeline_rows = [
        ("createpanelrefs", "nf-core/createpanelrefs", "https://github.com/nf-core/createpanelrefs", False, 0, 2, True, True, False, "pass", 1, 0),
        ("sarek", "nf-core/sarek", "https://github.com/nf-core/sarek", False, 0, 617, True, True, True, "warn", 1, 186),
        ("eager", "nf-core/eager", "https://github.com/nf-core/eager", False, 117, 367, None, False, True, "error", 0, 127),
        ("longraredisease", "nf-core/longraredisease", "https://github.com/nf-core/longraredisease", False, 0, 167, False, False, True, "error", 0, 76),
    ]
    conn.execute(
        """
        CREATE OR REPLACE TABLE strict_syntax.strict_syntax_pipelines (
            pipeline_name VARCHAR,
            full_name VARCHAR,
            html_url VARCHAR,
            parse_error BOOLEAN,
            errors INTEGER,
            warnings INTEGER,
            prints_help BOOLEAN,
            workflow_output BOOLEAN,
            publishdir BOOLEAN,
            workflow_output_state VARCHAR,
            workflow_output_count INTEGER,
            publishdir_count INTEGER,
            commit_sha VARCHAR,
            nextflow_sha VARCHAR,
            nextflow_version VARCHAR,
            lint_output VARCHAR,
            help_output VARCHAR,
            workflow_output_report VARCHAR,
            updated_at TIMESTAMP
        )
        """
    )
    conn.executemany(
        """
        INSERT INTO strict_syntax.strict_syntax_pipelines
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'demo-commit', 'demo-sha', '26.04.3', ?, ?, ?, ?)
        """,
        [
            (
                *row,
                _lint_output(row[0], row[4], row[5]),
                "$ NXF_SYNTAX_PARSER=v2 nextflow run . --help\n\nUsage: nextflow run nf-core/demo [options]\n"
                if row[6] is not None
                else None,
                _workflow_report(row[0], row[10], row[11]),
                now,
            )
            for row in pipeline_rows
        ],
    )

    conn.execute(
        """
        CREATE OR REPLACE TABLE strict_syntax.strict_syntax_modules (
            module_name VARCHAR,
            html_url VARCHAR,
            parse_error BOOLEAN,
            errors INTEGER,
            warnings INTEGER,
            commit_sha VARCHAR,
            nextflow_sha VARCHAR,
            nextflow_version VARCHAR,
            lint_output VARCHAR,
            updated_at TIMESTAMP
        )
        """
    )
    conn.executemany(
        "INSERT INTO strict_syntax.strict_syntax_modules VALUES (?, ?, ?, ?, ?, 'demo-commit', 'demo-sha', '26.04.3', ?, ?)",
        [
            ("bwa_mem", "https://github.com/nf-core/modules/tree/master/modules/nf-core/bwa/mem", False, 0, 0, _lint_output("bwa_mem", 0, 0), now),
            ("samtools_sort", "https://github.com/nf-core/modules/tree/master/modules/nf-core/samtools/sort", False, 0, 2, _lint_output("samtools_sort", 0, 2), now),
            ("fastqc", "https://github.com/nf-core/modules/tree/master/modules/nf-core/fastqc", False, 0, 6, _lint_output("fastqc", 0, 6), now),
            ("multiqc", "https://github.com/nf-core/modules/tree/master/modules/nf-core/multiqc", False, 0, 0, _lint_output("multiqc", 0, 0), now),
            ("salmon_quant", "https://github.com/nf-core/modules/tree/master/modules/nf-core/salmon/quant", False, 0, 0, _lint_output("salmon_quant", 0, 0), now),
        ],
    )

    conn.execute(
        """
        CREATE OR REPLACE TABLE strict_syntax.strict_syntax_subworkflows (
            subworkflow_name VARCHAR,
            html_url VARCHAR,
            parse_error BOOLEAN,
            errors INTEGER,
            warnings INTEGER,
            commit_sha VARCHAR,
            nextflow_sha VARCHAR,
            nextflow_version VARCHAR,
            lint_output VARCHAR,
            updated_at TIMESTAMP
        )
        """
    )
    conn.executemany(
        "INSERT INTO strict_syntax.strict_syntax_subworkflows VALUES (?, ?, ?, ?, ?, 'demo-commit', 'demo-sha', '26.04.3', ?, ?)",
        [
            ("bam_sort_stats_samtools", "https://github.com/nf-core/modules/tree/master/subworkflows/nf-core/bam_sort_stats_samtools", False, 0, 0, _lint_output("bam_sort_stats_samtools", 0, 0), now),
            ("fastq_align_bwa", "https://github.com/nf-core/modules/tree/master/subworkflows/nf-core/fastq_align_bwa", False, 0, 10, _lint_output("fastq_align_bwa", 0, 10), now),
            ("vcf_annotate", "https://github.com/nf-core/modules/tree/master/subworkflows/nf-core/vcf_annotate", False, 0, 6, _lint_output("vcf_annotate", 0, 6), now),
        ],
    )
    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "nf_core_stats_bot.duckdb",
        help="Path to the DuckDB database to create or replace.",
    )
    args = parser.parse_args()
    seed(args.database)
    print(f"Seeded strict syntax demo data in {args.database}")


if __name__ == "__main__":
    main()
