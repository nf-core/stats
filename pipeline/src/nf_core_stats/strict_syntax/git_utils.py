import subprocess
from pathlib import Path

from .._logging import logger
from .paths import MODULES_REPO_URL


def get_remote_commit_hash(repo_url: str, branch: str = "HEAD") -> str | None:
    """Get the latest commit hash from a remote repository without cloning."""
    try:
        result = subprocess.run(
            ["git", "ls-remote", repo_url, branch],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        if result.stdout.strip():
            return result.stdout.split()[0]
        return None
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None


def get_local_commit_hash(repo_path: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def get_remote_head_sha(repo_url: str) -> str | None:
    """Prefer dev branch, fall back to default branch HEAD."""
    sha = get_remote_commit_hash(repo_url, "refs/heads/dev")
    if sha:
        return sha
    return get_remote_commit_hash(repo_url, "HEAD")


def clone_modules_repo(modules_dir: Path) -> str:
    if modules_dir.exists():
        logger.info("Updating nf-core/modules repository...")
        subprocess.run(
            ["git", "-C", str(modules_dir), "fetch", "--quiet", "origin", "master"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(modules_dir), "checkout", "--quiet", "master"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(modules_dir), "pull", "--quiet"],
            check=True,
            capture_output=True,
        )
    else:
        logger.info("Cloning nf-core/modules repository...")
        subprocess.run(
            ["git", "clone", "--quiet", "--depth", "1", MODULES_REPO_URL, str(modules_dir)],
            check=True,
            capture_output=True,
        )

    commit_hash = get_local_commit_hash(modules_dir)
    logger.info("nf-core/modules ready at %s (%s)", modules_dir, commit_hash[:8])
    return commit_hash
