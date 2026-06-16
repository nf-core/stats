from .._logging import logger


def create_history_entry(results: list[dict], *, include_prints_help: bool = False) -> dict:
    """Create a daily aggregated history entry from a full result snapshot."""
    valid_results = [row for row in results if not row.get("parse_error", False)]
    parse_error_results = [row for row in results if row.get("parse_error", False)]

    entry = {
        "total": len(results),
        "parse_errors": len(parse_error_results),
        "errors_zero": sum(1 for row in valid_results if row["errors"] == 0),
        "errors_low": sum(1 for row in valid_results if 0 < row["errors"] <= 5),
        "errors_high": sum(1 for row in valid_results if row["errors"] > 5),
        "warnings_zero": sum(1 for row in valid_results if row["warnings"] == 0),
        "warnings_low": sum(1 for row in valid_results if 0 < row["warnings"] <= 20),
        "warnings_high": sum(1 for row in valid_results if row["warnings"] > 20),
        "total_errors": sum(row["errors"] for row in valid_results),
        "total_warnings": sum(row["warnings"] for row in valid_results),
    }

    if include_prints_help:
        entry["prints_help_pass"] = sum(1 for row in valid_results if row.get("prints_help") is True)
        entry["prints_help_fail"] = sum(1 for row in valid_results if row.get("prints_help") is False)

        from .lint import workflow_output_state

        states = [workflow_output_state(row) for row in results]
        entry["workflow_output_pass"] = sum(1 for state in states if state == "pass")
        entry["workflow_output_warn"] = sum(1 for state in states if state == "warn")
        entry["workflow_output_error"] = sum(1 for state in states if state == "error")

    return entry


def merge_snapshot(existing: dict[str, dict], updates: list[dict], *, name_key: str = "name") -> dict[str, dict]:
    """Merge lint results into a name-keyed snapshot dict."""
    merged = dict(existing)
    for row in updates:
        name = row[name_key]
        merged[name] = {key: value for key, value in row.items() if key != name_key}
        merged[name]["name"] = name
    logger.info("Snapshot size after merge: %d", len(merged))
    return merged


def snapshot_to_list(snapshot: dict[str, dict]) -> list[dict]:
    return list(snapshot.values())
