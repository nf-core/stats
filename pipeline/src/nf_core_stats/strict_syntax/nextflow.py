import subprocess

from .._logging import logger
from .paths import NEXTFLOW_REPO


def get_nextflow_sha() -> str:
    result = subprocess.run(
        ["git", "ls-remote", NEXTFLOW_REPO, "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.split()[0]


def get_nextflow_version() -> str:
    try:
        result = subprocess.run(["nextflow", "-version"], capture_output=True, text=True, check=False)
        for line in result.stdout.split("\n"):
            if "version" in line.lower():
                parts = line.split()
                for index, part in enumerate(parts):
                    if part.lower() == "version" and index + 1 < len(parts):
                        return parts[index + 1]
    except FileNotFoundError:
        logger.warning("Nextflow not found in PATH")
    return "unknown"
