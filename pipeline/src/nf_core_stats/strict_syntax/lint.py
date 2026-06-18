import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .._logging import logger

WORKFLOW_OUTPUT_RE = re.compile(r"^output\s*\{", re.MULTILINE)
PUBLISHDIR_RE = re.compile(r"\bpublishDir\b")
_MAX_REPORT_MATCHES = 200


def _scan_lines(repo_path: Path, patterns: tuple[str, ...], regex: re.Pattern) -> list[tuple[str, int, str]]:
    matches: list[tuple[str, int, str]] = []
    seen: set[Path] = set()
    for pattern in patterns:
        for src_file in repo_path.rglob(pattern):
            if src_file in seen:
                continue
            seen.add(src_file)
            try:
                source_lines = src_file.read_text().splitlines()
            except (OSError, UnicodeDecodeError):
                continue
            rel = str(src_file.relative_to(repo_path))
            for line_num, line in enumerate(source_lines, start=1):
                if regex.search(line):
                    matches.append((rel, line_num, line.strip()))
    matches.sort(key=lambda item: (item[0], item[1]))
    return matches


def find_workflow_output_matches(repo_path: Path) -> list[tuple[str, int, str]]:
    return _scan_lines(repo_path, ("*.nf",), WORKFLOW_OUTPUT_RE)


def find_publishdir_matches(repo_path: Path) -> list[tuple[str, int, str]]:
    return _scan_lines(repo_path, ("*.nf", "*.config"), PUBLISHDIR_RE)


def detect_workflow_output(repo_path: Path) -> bool:
    return bool(find_workflow_output_matches(repo_path))


def detect_publishdir(repo_path: Path) -> bool:
    return bool(find_publishdir_matches(repo_path))


def _format_matches(matches: list[tuple[str, int, str]]) -> list[str]:
    if not matches:
        return ["- No matches found"]

    lines = [f"- `{filename}:{line_num}`: `{line}`" for filename, line_num, line in matches[:_MAX_REPORT_MATCHES]]
    if len(matches) > _MAX_REPORT_MATCHES:
        lines.append(f"- ... {len(matches) - _MAX_REPORT_MATCHES} more matches omitted")
    return lines


def generate_workflow_output_report(
    *,
    repo_name: str,
    nextflow_version: str,
    workflow_output_matches: list[tuple[str, int, str]],
    publishdir_matches: list[tuple[str, int, str]],
) -> str:
    now = datetime.now(timezone.utc).isoformat()
    workflow_output_count = len(workflow_output_matches)
    publishdir_count = len(publishdir_matches)
    if workflow_output_count and not publishdir_count:
        state = "Fully migrated"
    elif workflow_output_count:
        state = "In progress"
    else:
        state = "Not started"

    lines = [
        "# Workflow outputs migration report",
        "",
        f"- Pipeline: {repo_name}",
        f"- Generated: {now}",
        f"- Nextflow version: {nextflow_version}",
        f"- Status: {state}",
        f"- `output {{}}` matches: {workflow_output_count}",
        f"- `publishDir` matches: {publishdir_count}",
        "",
        "## `output {}` matches",
        "",
        *_format_matches(workflow_output_matches),
        "",
        "## `publishDir` matches",
        "",
        *_format_matches(publishdir_matches),
    ]
    return "\n".join(lines)


def workflow_output_state(result: dict) -> str | None:
    has_output = result.get("workflow_output")
    has_publishdir = result.get("publishdir")
    if has_output is None or has_publishdir is None:
        return None
    if has_output and has_publishdir:
        return "warn"
    if has_output:
        return "pass"
    return "error"


def lint_component(repo_path: Path, target_path: Path | None = None) -> dict:
    if target_path:
        try:
            relative_path = target_path.relative_to(repo_path)
        except ValueError:
            relative_path = target_path
        cmd = ["nextflow", "lint", str(relative_path), "-o", "json"]
    else:
        cmd = ["nextflow", "lint", ".", "-o", "json"]

    result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)

    try:
        lint_result = json.loads(result.stdout)
        lint_result["parse_error"] = False
        return lint_result
    except json.JSONDecodeError:
        name = target_path.name if target_path else repo_path.name
        logger.warning("Failed to parse lint output for %s", name)
        return {"summary": {"errors": 0}, "errors": [], "warnings": [], "parse_error": True}


def lint_directory_bulk(repo_path: Path, target_path: Path) -> dict:
    try:
        relative_path = target_path.relative_to(repo_path)
    except ValueError:
        relative_path = target_path

    result = subprocess.run(
        ["nextflow", "lint", str(relative_path), "-o", "json"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        logger.warning("Failed to parse bulk lint output for %s", target_path)
        return {"errors": [], "warnings": []}


def _extract_component_name_from_path(filepath: str, component_type: str) -> str | None:
    parts = Path(filepath).parts
    try:
        nf_core_idx = parts.index("nf-core")
    except ValueError:
        return None

    if component_type == "modules":
        if len(parts) > nf_core_idx + 2:
            return f"{parts[nf_core_idx + 1]}_{parts[nf_core_idx + 2]}"
    elif len(parts) > nf_core_idx + 1:
        return parts[nf_core_idx + 1]
    return None


def group_lint_results_by_component(lint_result: dict, component_type: str) -> dict[str, dict]:
    grouped: dict[str, dict] = {}
    for issue_type in ("errors", "warnings"):
        for issue in lint_result.get(issue_type, []):
            filename = issue.get("filename", "")
            name = _extract_component_name_from_path(filename, component_type)
            if not name:
                continue
            grouped.setdefault(name, {"errors": [], "warnings": []})
            grouped[name][issue_type].append(issue)
    return grouped


def _get_code_snippet(repo_path: Path, filename: str, line_num: int, column: int) -> str | None:
    try:
        file_path = repo_path / filename
        if not file_path.exists():
            return None
        source_lines = file_path.read_text().splitlines()
        if line_num < 1 or line_num > len(source_lines):
            return None
        source_line = source_lines[line_num - 1]
        caret_line = " " * (column - 1) + "^" * max(1, min(10, len(source_line) - column + 1))
        return f"    ```nextflow\n    {source_line}\n    {caret_line}\n    ```"
    except OSError:
        return None


def generate_markdown_from_issues(
    errors: list[dict],
    warnings: list[dict],
    nextflow_version: str,
    repo_path: Path | None = None,
) -> str:
    now = datetime.now(timezone.utc).isoformat()
    error_count = len(errors)
    warning_count = len(warnings)

    lines = [
        "# Nextflow lint results",
        "",
        f"- Generated: {now}",
        f"- Nextflow version: {nextflow_version}",
    ]

    if error_count == 0 and warning_count == 0:
        lines.append("- Summary: No issues found")
        return "\n".join(lines)

    summary_parts = []
    if error_count:
        summary_parts.append(f"{error_count} error{'s' if error_count != 1 else ''}")
    if warning_count:
        summary_parts.append(f"{warning_count} warning{'s' if warning_count != 1 else ''}")
    lines.append(f"- Summary: {', '.join(summary_parts)}")

    for section_title, issues in (("Errors", errors), ("Warnings", warnings)):
        if not issues:
            continue
        icon = ":x:" if section_title == "Errors" else ":warning:"
        lines.extend(["", f"## {icon} {section_title}", ""])
        for issue in issues:
            filename = issue.get("filename", "unknown")
            line_num = issue.get("startLine", 0)
            col = issue.get("startColumn", 0)
            message = issue.get("message", "")
            label = section_title[:-1]
            lines.append(f"- {label}: `{filename}:{line_num}:{col}`: {message}")
            lines.append("")
            if repo_path:
                snippet = _get_code_snippet(repo_path, filename, line_num, col)
                if snippet:
                    lines.extend([snippet, ""])

    return "\n".join(lines)


def test_prints_help(repo_path: Path) -> tuple[bool, str]:
    try:
        env = {**os.environ, "NXF_SYNTAX_PARSER": "v2"}
        result = subprocess.run(
            ["nextflow", "run", ".", "--help"],
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=120,
            env=env,
        )
        output = f"$ NXF_SYNTAX_PARSER=v2 nextflow run . --help\n\n{result.stdout}"
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "$ NXF_SYNTAX_PARSER=v2 nextflow run . --help\n\nError: Timeout after 120s\n"
    except OSError as exc:
        return False, f"$ NXF_SYNTAX_PARSER=v2 nextflow run . --help\n\nError: {exc}\n"
