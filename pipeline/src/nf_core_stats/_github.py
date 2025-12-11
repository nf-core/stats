from datetime import datetime, timezone

import dlt
import requests
from dlt.sources.helpers.requests import Client

from ._logging import logger

# Configure DLT requests client with retry settings
# This client automatically retries 429 errors and respects Retry-After headers
http_client = Client(
    request_timeout=60,
    request_max_attempts=5,
    request_backoff_factor=1,
    request_max_retry_delay=300,
    raise_for_status=False,  # We'll handle status codes manually for better error messages
)


def get_github_headers(api_token: str = dlt.secrets["sources.github_pipeline.github.api_token"]) -> dict:
    """Get GitHub API headers with authentication"""
    if not api_token:
        raise ValueError(
            "GitHub API token is not configured. Please set SOURCES__GITHUB_PIPELINE__GITHUB__API_TOKEN in your secrets."
        )
    return {"Authorization": f"token {api_token}", "Accept": "application/vnd.github.v3+json"}


def check_rate_limit(headers: dict, min_remaining: int = 100) -> dict:
    """Check GitHub API rate limit status

    Args:
        headers: GitHub API headers
        min_remaining: Minimum requests that should remain

    Returns:
        dict with 'remaining', 'limit', 'reset' keys
    """
    response = http_client.get("https://api.github.com/rate_limit", headers=headers)
    response.raise_for_status()
    rate_limit = response.json()["resources"]["core"]

    remaining = rate_limit["remaining"]
    limit = rate_limit["limit"]
    reset_time = rate_limit["reset"]
    reset_datetime = datetime.fromtimestamp(reset_time, tz=timezone.utc)

    logger.info(f"Rate limit: {remaining}/{limit} remaining (resets at {reset_datetime})")

    if remaining < min_remaining:
        logger.warning(f"Low rate limit: only {remaining} requests remaining (minimum: {min_remaining})")

    return {"remaining": remaining, "limit": limit, "reset": reset_time}


def github_request(url: str, headers: dict) -> requests.Response:
    """Make GitHub API request with rate limit handling using DLT's retry-enabled client

    The http_client automatically:
    - Retries 429 (rate limit) errors with exponential backoff
    - Respects Retry-After headers from GitHub
    - Retries transient network errors and 5xx server errors
    - Uses configurable backoff (1s, 2s, 4s, 8s, 16s)

    Note: For actual rate limit exhaustion (403 with X-RateLimit-Remaining: 0),
    we fail fast to let DLT's incremental loading resume on the next run.
    """
    response = http_client.get(url, headers=headers)

    # Check for rate limit exhaustion using GitHub-specific headers
    # 403 with X-RateLimit-Remaining: 0 indicates true rate limit exhaustion
    if response.status_code == 403:
        remaining = response.headers.get("X-RateLimit-Remaining")
        reset_time = response.headers.get("X-RateLimit-Reset")

        # Only fail fast if we're truly rate limited (remaining = 0)
        # Other 403s (permissions, etc.) will be handled by raise_for_status
        if remaining is not None and int(remaining) == 0:
            reset_datetime = datetime.fromtimestamp(int(reset_time), tz=timezone.utc) if reset_time else "unknown"
            logger.error(f"Rate limit exhausted. Resets at {reset_datetime}. Failing fast to resume on next run.")
            raise requests.HTTPError(
                f"GitHub API rate limit exhausted. Resets at {reset_datetime}. Pipeline will resume on next scheduled run.",
                response=response,
            )

    # DLT client handles 429 automatically with retries, but if it still fails after retries, we should fail fast
    if response.status_code == 429:
        reset_time = response.headers.get("X-RateLimit-Reset", response.headers.get("Retry-After", "0"))
        reset_datetime = (
            datetime.fromtimestamp(int(reset_time), tz=timezone.utc) if reset_time.isdigit() else reset_time
        )
        logger.error(f"Rate limit hit after retries. Resets at {reset_datetime}. Failing fast.")
        raise requests.HTTPError(
            f"GitHub API rate limit hit after automatic retries. Resets at {reset_datetime}.",
            response=response,
        )

    response.raise_for_status()
    return response


def get_paginated_data(url: str, headers: dict):
    """Get all paginated results from GitHub API"""
    all_results = []

    while url:
        response = github_request(url, headers)
        data = response.json()

        # Handle different response formats
        if isinstance(data, dict) and "items" in data:
            all_results.extend(data["items"])
        elif isinstance(data, list):
            all_results.extend(data)
        else:
            return data  # Non-paginated response

        url = response.links.get("next", {}).get("url")

    return all_results


def get_file_contents(owner: str, repo: str, path: str, headers: dict, ref: str | None = None) -> str:
    """Get the contents of a file from a GitHub repository

    Args:
        owner: Repository owner (e.g., 'nf-core')
        repo: Repository name (e.g., 'rnaseq')
        path: Path to the file in the repository (e.g., 'nextflow.config')
        headers: GitHub API headers
        ref: Git reference (branch, tag, or commit SHA). If None, uses the repository's default branch

    Returns:
        The decoded file contents as a string

    Raises:
        requests.HTTPError: If the file is not found or other API errors
    """
    import base64

    # If no ref specified, get the repository's default branch
    if ref is None:
        repo_url = f"https://api.github.com/repos/{owner}/{repo}"
        repo_response = http_client.get(repo_url, headers=headers)
        repo_response.raise_for_status()
        ref = repo_response.json()["default_branch"]
        logger.debug(f"Using default branch '{ref}' for {owner}/{repo}")

    # Remove leading slash if present
    path = path.lstrip("/")

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    params = {"ref": ref}

    response = http_client.get(url, headers=headers, params=params)
    response.raise_for_status()

    data = response.json()

    # GitHub returns base64-encoded content
    if "content" in data:
        content = base64.b64decode(data["content"]).decode("utf-8")
        return content
    else:
        raise ValueError(f"No content found in response for {owner}/{repo}/{path}")
