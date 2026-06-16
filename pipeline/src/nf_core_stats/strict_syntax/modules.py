from pathlib import Path

from .._logging import logger
from .git_utils import clone_modules_repo, get_remote_commit_hash
from .lint import generate_markdown_from_issues, group_lint_results_by_component, lint_component, lint_directory_bulk
from .paths import MODULES_DIR


def discover_modules(modules_dir: Path = MODULES_DIR) -> list[dict]:
    modules_path = modules_dir / "modules" / "nf-core"
    if not modules_path.exists():
        logger.warning("Modules path not found: %s", modules_path)
        return []

    modules = []
    for tool_dir in sorted(modules_path.iterdir()):
        if not tool_dir.is_dir() or tool_dir.name.startswith("."):
            continue
        if (tool_dir / "main.nf").exists():
            component_dirs = [(tool_dir, tool_dir.name)]
        else:
            component_dirs = []
            for subcommand_dir in sorted(tool_dir.iterdir()):
                if not subcommand_dir.is_dir() or subcommand_dir.name.startswith("."):
                    continue
                if (subcommand_dir / "main.nf").exists():
                    component_dirs.append((subcommand_dir, f"{tool_dir.name}_{subcommand_dir.name}"))
        for path, name in component_dirs:
            modules.append(
                {
                    "name": name,
                    "path": path,
                    "html_url": (
                        f"https://github.com/nf-core/modules/tree/master/modules/nf-core/"
                        f"{path.relative_to(modules_path)}"
                    ),
                }
            )

    logger.info("Found %d modules", len(modules))
    return modules


def discover_subworkflows(modules_dir: Path = MODULES_DIR) -> list[dict]:
    subworkflows_path = modules_dir / "subworkflows" / "nf-core"
    if not subworkflows_path.exists():
        logger.warning("Subworkflows path not found: %s", subworkflows_path)
        return []

    subworkflows = []
    for subworkflow_dir in sorted(subworkflows_path.iterdir()):
        if not subworkflow_dir.is_dir() or subworkflow_dir.name.startswith("."):
            continue
        if (subworkflow_dir / "main.nf").exists():
            subworkflows.append(
                {
                    "name": subworkflow_dir.name,
                    "path": subworkflow_dir,
                    "html_url": (
                        f"https://github.com/nf-core/modules/tree/master/subworkflows/nf-core/{subworkflow_dir.name}"
                    ),
                }
            )

    logger.info("Found %d subworkflows", len(subworkflows))
    return subworkflows


def _lint_components_individual(
    items: list[dict],
    *,
    component_type: str,
    nextflow_version: str,
    modules_dir: Path,
) -> list[dict]:
    results = []
    for item in items:
        logger.info("Linting %s %s...", component_type[:-1], item["name"])
        try:
            lint_result = lint_component(modules_dir, item["path"])
            lint_output = generate_markdown_from_issues(
                lint_result.get("errors", []),
                lint_result.get("warnings", []),
                nextflow_version,
                modules_dir,
            )
            results.append(
                {
                    "name": item["name"],
                    "html_url": item["html_url"],
                    "errors": lint_result.get("summary", {}).get("errors", 0),
                    "warnings": len(lint_result.get("warnings", [])),
                    "parse_error": lint_result.get("parse_error", False),
                    "lint_output": lint_output,
                }
            )
        except OSError as exc:
            logger.error("Failed to lint %s: %s", item["name"], exc)
            results.append(
                {
                    "name": item["name"],
                    "html_url": item["html_url"],
                    "errors": 0,
                    "warnings": 0,
                    "parse_error": True,
                    "lint_output": None,
                }
            )
    return results


def _lint_components_bulk(
    items: list[dict],
    *,
    component_type: str,
    target_path: Path,
    nextflow_version: str,
    modules_dir: Path,
) -> list[dict]:
    logger.info("Running bulk lint on %d %s...", len(items), component_type)
    bulk_result = lint_directory_bulk(modules_dir, target_path)
    grouped = group_lint_results_by_component(bulk_result, component_type)

    results = []
    for item in items:
        component_issues = grouped.get(item["name"], {"errors": [], "warnings": []})
        errors = component_issues["errors"]
        warnings = component_issues["warnings"]
        lint_output = generate_markdown_from_issues(errors, warnings, nextflow_version, modules_dir)
        results.append(
            {
                "name": item["name"],
                "html_url": item["html_url"],
                "errors": len(errors),
                "warnings": len(warnings),
                "parse_error": False,
                "lint_output": lint_output,
            }
        )
    return results


def lint_modules(
    modules: list[dict],
    *,
    snapshot: dict[str, dict],
    nextflow_version: str,
    no_cache: bool = False,
    modules_dir: Path = MODULES_DIR,
) -> tuple[list[dict], dict[str, dict]]:
    if len(modules) <= 5:
        results = _lint_components_individual(
            modules,
            component_type="modules",
            nextflow_version=nextflow_version,
            modules_dir=modules_dir,
        )
    else:
        results = _lint_components_bulk(
            modules,
            component_type="modules",
            target_path=modules_dir / "modules" / "nf-core",
            nextflow_version=nextflow_version,
            modules_dir=modules_dir,
        )

    updated = {row["name"]: {key: value for key, value in row.items() if key != "name"} for row in results}
    return results, updated


def lint_subworkflows(
    subworkflows: list[dict],
    *,
    snapshot: dict[str, dict],
    nextflow_version: str,
    no_cache: bool = False,
    modules_dir: Path = MODULES_DIR,
) -> tuple[list[dict], dict[str, dict]]:
    if len(subworkflows) <= 5:
        results = _lint_components_individual(
            subworkflows,
            component_type="subworkflows",
            nextflow_version=nextflow_version,
            modules_dir=modules_dir,
        )
    else:
        results = _lint_components_bulk(
            subworkflows,
            component_type="subworkflows",
            target_path=modules_dir / "subworkflows" / "nf-core",
            nextflow_version=nextflow_version,
            modules_dir=modules_dir,
        )

    updated = {row["name"]: {key: value for key, value in row.items() if key != "name"} for row in results}
    return results, updated


def prepare_modules_repo(
    *,
    snapshot: dict[str, dict],
    no_cache: bool,
    check_modules: bool,
    check_subworkflows: bool,
    modules_dir: Path = MODULES_DIR,
) -> tuple[bool, str | None]:
    """Return (unchanged, remote_commit). Clone/update repo when changed."""
    remote_commit = get_remote_commit_hash("https://github.com/nf-core/modules.git", "refs/heads/master")
    if remote_commit is None:
        clone_modules_repo(modules_dir)
        return False, get_remote_commit_hash("https://github.com/nf-core/modules.git", "refs/heads/master")

    stored_commit = snapshot.get("_repo_commit")
    if not no_cache and stored_commit == remote_commit and (snapshot.get("modules") or snapshot.get("subworkflows")):
        logger.info("nf-core/modules unchanged at %s", remote_commit[:8])
        return True, remote_commit

    clone_modules_repo(modules_dir)
    return False, remote_commit
