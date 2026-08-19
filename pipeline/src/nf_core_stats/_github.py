from datetime import datetime, timezone

import dlt
import requests
from dlt.sources.helpers.requests import Client
from dlt.sources.helpers.rest_client import RESTClient
from dlt.sources.helpers.rest_client.paginators import HeaderLinkPaginator

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

rest_client = RESTClient(
    base_url="https://api.github.com",
    paginator=HeaderLinkPaginator(),
    session=http_client.session,
)


class RateLimitError(requests.HTTPError):
    """GitHub primary or secondary rate limit hit. Abort the run; dlt resumes next schedule."""


def find_rate_limit_error(exc: BaseException) -> RateLimitError | None:
    """Find a RateLimitError in an exception's cause chain.

    dlt wraps exceptions raised inside a resource generator as
    PipelineStepFailed -> ResourceExtractionError -> RateLimitError, so callers of
    `pipeline.run()` cannot catch RateLimitError directly.
    """
    seen = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        if isinstance(current, RateLimitError):
            return current
        seen.add(id(current))
        current = current.__cause__ or current.__context__
    return None


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
    response = github_request("https://api.github.com/rate_limit", headers)
    rate_limit = response.json()["resources"]["core"]

    remaining = rate_limit["remaining"]
    limit = rate_limit["limit"]
    reset_time = rate_limit["reset"]
    reset_datetime = datetime.fromtimestamp(reset_time, tz=timezone.utc)

    logger.info(f"Rate limit: {remaining}/{limit} remaining (resets at {reset_datetime})")

    if remaining < min_remaining:
        logger.warning(f"Low rate limit: only {remaining} requests remaining (minimum: {min_remaining})")

    return {"remaining": remaining, "limit": limit, "reset": reset_time}


def raise_for_github_errors(response: requests.Response) -> None:
    """Raise a diagnosable error for GitHub auth failures and rate limits.

    Rate-limit-shaped 403s and 429s raise `RateLimitError` so callers can abort the run
    instead of firing thousands of doomed requests. Other statuses are left alone for
    `raise_for_status()`.
    """
    if response.status_code == 401:
        logger.error(
            "GitHub API returned 401 Unauthorized - the API token is invalid, revoked, or expired. "
            "Rotate the GH_TOKEN_STATS_PAGE repository secret."
        )
        raise requests.HTTPError(
            "GitHub API authentication failed (401 Unauthorized). "
            "The token is invalid or expired - rotate the GH_TOKEN_STATS_PAGE repository secret.",
            response=response,
        )

    # 403 covers both primary quota exhaustion (X-RateLimit-Remaining: 0) and secondary
    # rate limits (bursty traffic), which carry Retry-After and/or a body marker and have
    # their own reset independent of the core bucket.
    if response.status_code == 403:
        remaining = response.headers.get("X-RateLimit-Remaining")
        reset_time = response.headers.get("X-RateLimit-Reset")
        resource = response.headers.get("X-RateLimit-Resource")
        retry_after = response.headers.get("Retry-After")

        is_rate_limited = remaining == "0" or retry_after is not None or "secondary rate limit" in response.text.lower()
        if is_rate_limited:
            reset_datetime = (
                datetime.fromtimestamp(int(reset_time), tz=timezone.utc)
                if reset_time and reset_time.isdigit()
                else "unknown"
            )
            message = (
                f"Rate limited (403). resource={resource} remaining={remaining} "
                f"reset={reset_datetime} retry_after={retry_after}. Aborting run; resumes next schedule."
            )
            logger.error(message)
            raise RateLimitError(message, response=response)

    # DLT client handles 429 automatically with retries, but if it still fails after retries, we should fail fast
    if response.status_code == 429:
        reset_time = response.headers.get("X-RateLimit-Reset", response.headers.get("Retry-After", "0"))
        reset_datetime = (
            datetime.fromtimestamp(int(reset_time), tz=timezone.utc) if reset_time.isdigit() else reset_time
        )
        logger.error(f"Rate limit hit after retries. Resets at {reset_datetime}. Failing fast.")
        raise RateLimitError(
            f"GitHub API rate limit hit after automatic retries. Resets at {reset_datetime}.",
            response=response,
        )


def github_request(url: str, headers: dict) -> requests.Response:
    """Make GitHub API request with rate limit handling using DLT's retry-enabled client

    The http_client automatically:
    - Retries 429 (rate limit) errors with exponential backoff
    - Respects Retry-After headers from GitHub
    - Retries transient network errors and 5xx server errors
    - Uses configurable backoff (1s, 2s, 4s, 8s, 16s)

    Note: For rate limit hits (403/429 with rate-limit markers), we fail fast with
    `RateLimitError` to let DLT's incremental loading resume on the next run.
    """
    response = http_client.get(url, headers=headers)
    raise_for_github_errors(response)
    response.raise_for_status()
    return response


def get_paginated_data(url: str, headers: dict):
    """Get all paginated results from GitHub API"""
    all_results = []

    try:
        for page in rest_client.paginate(url, headers=headers):
            if isinstance(page, list):
                all_results.extend(page)
            else:
                return page  # Non-paginated response
    except requests.HTTPError as e:
        if e.response is not None:
            raise_for_github_errors(e.response)
        raise

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
