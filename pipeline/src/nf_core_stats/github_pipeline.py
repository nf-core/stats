import io
import logging
import zipfile
from collections.abc import Iterator
from datetime import date, datetime, timedelta, timezone
from typing import Literal

import dlt
import requests

from ._github import (
    RateLimitError,
    check_rate_limit,
    find_rate_limit_error,
    get_github_headers,
    get_paginated_data,
    github_graphql,
    github_request,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dlt.source(name="github")
def github_source(organization: str = "nf-core", api_token: str = dlt.secrets.value):
    """GitHub data source"""
    headers = get_github_headers(api_token)
    logger.info(f"Initialized GitHub source for organization: {organization}")

    # Test authentication with a simple API call
    test_url = "https://api.github.com/user"
    test_response = github_request(test_url, headers)
    user_info = test_response.json()
    logger.info(f"GitHub authentication successful. Authenticated as: {user_info.get('login', 'unknown')}")

    # Get all repositories
    repos_url = f"https://api.github.com/orgs/{organization}/repos"
    logger.info(f"Fetching repositories from: {repos_url}")

    repos = get_paginated_data(repos_url, headers)
    logger.info(f"Successfully fetched {len(repos)} repositories from GitHub API")

    if not repos:
        logger.warning(
            f"No repositories found for organization '{organization}'. Check if the organization exists and your token has access."
        )

    return [
        dlt.resource(traffic_stats(organization, headers, repos), name="traffic_stats"),
        dlt.resource(contributor_stats(organization, headers, repos), name="contributor_stats"),
        dlt.resource(issue_stats(organization, headers, repos), name="issue_stats"),
        dlt.resource(org_members(organization, headers), name="org_members"),
        dlt.resource(commit_stats(organization, headers, repos), name="commit_stats"),
        dlt.resource(pipelines(organization, headers, repos), name="nfcore_pipelines"),
        dlt.resource(modules_container_conversion(headers), name="modules_container_conversion"),
    ]


@dlt.resource(write_disposition="merge", primary_key=["pipeline_name", "timestamp"])
def traffic_stats(
    organization: str, headers: dict, repos: list[dict], only_active_repos: bool = False, max_repos: int | None = None
) -> Iterator[dict]:
    """Collect traffic stats for repositories

    Args:
        organization: GitHub organization name
        headers: GitHub API headers
        repos: List of repository data
        only_active_repos: Only collect traffic for recently active repos (default False)
        max_repos: Maximum number of repos to process (default None for all)
    """
    # Filter repositories if requested
    filtered_repos = repos

    if only_active_repos:
        # Only get traffic for repos that have been updated in the last 6 months and are not archived
        six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
        filtered_repos = [
            repo
            for repo in repos
            if datetime.strptime(repo["updated_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) > six_months_ago
            and not repo["archived"]
        ]
        logger.info(f"Filtered to {len(filtered_repos)} active repositories (updated in last 6 months)")
    else:
        # Process all repos, but skip archived ones
        filtered_repos = [repo for repo in repos if not repo["archived"]]
        logger.info(
            f"Processing {len(filtered_repos)} repositories (skipping {len(repos) - len(filtered_repos)} archived)"
        )

    # Sort by stars/activity to prioritize important repos
    filtered_repos = sorted(filtered_repos, key=lambda x: x.get("stargazers_count", 0), reverse=True)

    if max_repos:
        filtered_repos = filtered_repos[:max_repos]
        logger.info(f"Limited to top {max_repos} repositories by stars")

    logger.info(f"Collecting traffic stats for {len(filtered_repos)} repositories")

    successful_repos = 0
    failed_repos = 0

    for repo in filtered_repos:
        name = repo["name"]

        # Get views and clones
        views_url = f"https://api.github.com/repos/{organization}/{name}/traffic/views"
        clones_url = f"https://api.github.com/repos/{organization}/{name}/traffic/clones"

        try:
            views_data = github_request(views_url, headers).json()
            clones_data = github_request(clones_url, headers).json()
            successful_repos += 1
        except RateLimitError:
            raise
        except requests.RequestException as e:
            # Traffic data requires push access - skip if not available
            if "403" in str(e) or "Forbidden" in str(e):
                logger.info(f"Skipping traffic data for {name} (requires push access)")
            elif "404" in str(e):
                logger.info(f"Skipping traffic data for {name} (not found)")
            else:
                logger.warning(f"Failed to get traffic data for {name}: {e}")
            failed_repos += 1
            continue

        # Get views and clones data
        views_list = views_data.get("views", [])
        clones_list = clones_data.get("clones", [])

        if not views_list and not clones_list:
            logger.debug(f"No traffic data available for {name}")
            continue

        # Create a mapping of clone data by timestamp for efficient lookup
        clones_by_timestamp = {c["timestamp"]: c for c in clones_list}

        # Process views data and match with clones
        for view in views_list:
            timestamp = view["timestamp"]
            clone_data = clones_by_timestamp.get(timestamp, {"count": 0, "uniques": 0})

            yield {
                "pipeline_name": name,
                "timestamp": timestamp,
                "views": view["count"],
                "views_uniques": view["uniques"],
                "clones": clone_data["count"],
                "clones_uniques": clone_data["uniques"],
            }

        # Process clone data that doesn't have corresponding view data
        for clone in clones_list:
            timestamp = clone["timestamp"]
            # Only yield if we haven't already processed this timestamp from views
            if not any(view["timestamp"] == timestamp for view in views_list):
                yield {
                    "pipeline_name": name,
                    "timestamp": timestamp,
                    "views": 0,
                    "views_uniques": 0,
                    "clones": clone["count"],
                    "clones_uniques": clone["uniques"],
                }

    logger.info(f"Traffic stats completed: {successful_repos} successful, {failed_repos} failed/skipped")


@dlt.resource(write_disposition="merge", primary_key=["pipeline_name", "author", "week_date"])
def contributor_stats(organization: str, headers: dict, repos: list[dict]) -> Iterator[dict]:
    """Collect contributor stats"""
    logger.info(f"Collecting contributor stats for {len(repos)} repositories")
    for repo in repos:
        name = repo["name"]
        contributor_data = {}

        # Get commit stats
        stats_url = f"https://api.github.com/repos/{organization}/{name}/stats/contributors"
        try:
            stats = get_paginated_data(stats_url, headers)
            if not isinstance(stats, list):
                continue
        except RateLimitError:
            raise
        except requests.RequestException as e:
            logger.warning(f"Failed to get contributor stats for {name}: {e}")
            continue

        # Process commit stats
        for contributor in stats:
            # GitHub returns author: null for contributors whose account was deleted
            if not contributor.get("author"):
                continue

            author = contributor["author"]["login"]
            avatar_url = contributor["author"]["avatar_url"]

            for week in contributor["weeks"]:
                week_date = datetime.fromtimestamp(week["w"], tz=timezone.utc).strftime("%Y-%m-%d")
                key = (author, week_date)

                if key not in contributor_data:
                    contributor_data[key] = {
                        "pipeline_name": name,
                        "author": author,
                        "avatar_url": avatar_url,
                        "week_date": week_date,
                        "week_additions": week["a"],
                        "week_deletions": week["d"],
                        "week_commits": week["c"],
                        "week_approvals": 0,
                    }

        yield from contributor_data.values()


@dlt.resource(write_disposition="merge", primary_key=["pipeline_name", "issue_number"])
def issue_stats(
    organization: str,
    headers: dict,
    repos: list[dict],
    updated_at: dlt.sources.incremental[str] = dlt.sources.incremental(
        "updated_at", initial_value="2010-01-01T00:00:00Z"
    ),
) -> Iterator[dict]:
    """Collect issue and PR stats with incremental comment loading"""
    logger.info(f"Collecting issue and PR stats for {len(repos)} repositories")

    # Get current state to check which issues we've already processed
    state = dlt.current.source_state()
    processed_issues = state.setdefault("processed_issues", {})

    # Check rate limit before expensive comment fetching
    rate_status = check_rate_limit(headers, min_remaining=500)
    fetch_comments = rate_status["remaining"] > 500

    if not fetch_comments:
        logger.warning(
            f"Skipping comment fetching due to low rate limit ({rate_status['remaining']} remaining). "
            "Will fetch comments on next run."
        )

    for repo in repos:
        name = repo["name"]
        issues_url = (
            f"https://api.github.com/repos/{organization}/{name}/issues"
            f"?state=all&per_page=100&since={updated_at.last_value}"
        )

        try:
            issues = get_paginated_data(issues_url, headers)
            if not isinstance(issues, list):
                continue
        except RateLimitError:
            raise
        except requests.RequestException as e:
            logger.warning(f"Failed to get issues for {name}: {e}")
            continue

        repo_processed = processed_issues.setdefault(name, {})

        for issue in issues:
            is_pr = "pull_request" in issue
            created_at = datetime.strptime(issue["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            issue_key = str(issue["number"])  # Calculate close time
            closed_wait = None
            if issue["closed_at"]:
                closed_at = datetime.strptime(issue["closed_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                closed_wait = (closed_at - created_at).total_seconds()

            # Check if we need to fetch comments for this issue
            previous_data = repo_processed.get(issue_key, {})
            previous_comment_count = previous_data.get("num_comments", 0)
            current_comment_count = issue["comments"]

            # Only fetch comments if:
            # 1. We have rate limit headroom
            # 2. Issue has comments
            # 3. Either new issue OR comment count has changed
            should_fetch_comments = (
                fetch_comments
                and current_comment_count > 0
                and (issue_key not in repo_processed or current_comment_count != previous_comment_count)
            )

            first_response_time = previous_data.get("first_response_seconds")
            first_responder = previous_data.get("first_responder")

            if should_fetch_comments:
                comments_url = f"https://api.github.com/repos/{organization}/{name}/issues/{issue['number']}/comments"
                try:
                    comments = get_paginated_data(comments_url, headers)
                    if isinstance(comments, list):
                        for comment in comments:
                            if (
                                comment.get("user", {}).get("login")
                                and comment["user"]["login"] != issue["user"]["login"]
                            ):
                                comment_time = datetime.strptime(comment["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(
                                    tzinfo=timezone.utc
                                )
                                first_response_time = (comment_time - created_at).total_seconds()
                                first_responder = comment["user"]["login"]
                                break
                except RateLimitError:
                    raise
                except requests.RequestException as e:
                    logger.warning(f"Failed to get comments for issue {issue['number']} in {name}: {e}")
                    # Don't fail the whole pipeline, just skip this issue's comments
                    pass

            # Store this issue in our state
            repo_processed[issue_key] = {
                "num_comments": current_comment_count,
                "first_response_seconds": first_response_time,
                "first_responder": first_responder,
            }

            yield {
                "pipeline_name": name,
                "issue_number": issue["number"],
                "issue_type": "pr" if is_pr else "issue",
                "state": issue["state"],
                "created_by": issue["user"]["login"],
                "created_at": issue["created_at"],
                "updated_at": issue["updated_at"],
                "closed_at": issue["closed_at"],
                "closed_wait_seconds": closed_wait,
                "first_response_seconds": first_response_time,
                "first_responder": first_responder,
                "num_comments": issue["comments"],
                "html_url": issue["html_url"],
            }


# nf-core was created on 2018-01-17. Reviews on pull requests updated before this are not collected.
PR_REVIEW_HISTORY_START = date(2018, 1, 1)
# 100 PRs per page. 50 pages is a few busy weeks and stays far under the GraphQL point budget,
# so the daily run can walk backward through history without a burst that trips a secondary limit.
PR_REVIEW_PAGE_BUDGET = 50
_SEARCH_RESULT_CAP = 1000

_PR_SEARCH = """
query($q: String!, $cursor: String) {
  search(query: $q, type: ISSUE, first: 100, after: $cursor) {
    issueCount
    pageInfo { hasNextPage endCursor }
    nodes {
      ... on PullRequest {
        id
        number
        repository { name }
        author { login __typename }
        reviews(first: 100) {
          pageInfo { hasNextPage endCursor }
          nodes { id state submittedAt author { login __typename } }
        }
      }
    }
  }
}
"""

_REVIEW_PAGE = """
query($id: ID!, $cursor: String) {
  node(id: $id) {
    ... on PullRequest {
      reviews(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes { id state submittedAt author { login __typename } }
      }
    }
  }
}
"""


class _PageBudgetExhaustedError(Exception):
    """This run's GraphQL page budget is spent. Older history waits for the next run."""


class _PageBudget:
    def __init__(self, limit: int | None):
        self.limit = limit
        self.used = 0

    def charge(self) -> None:
        if self.limit is not None and self.used >= self.limit:
            raise _PageBudgetExhaustedError
        self.used += 1


def _actor_login(actor: dict | None) -> str | None:
    """GitHub login, with the `[bot]` suffix the REST API uses for GitHub App accounts."""
    if not actor:
        return None
    login = actor.get("login")
    if not login:
        return None
    if actor.get("__typename") == "Bot" and not login.endswith("[bot]"):
        return f"{login}[bot]"
    return login


def _review_rows(pr: dict, reviews: list[dict]) -> Iterator[dict]:
    for review in reviews:
        if not review or review.get("state") == "PENDING" or not review.get("submittedAt") or not review.get("id"):
            continue
        yield {
            "review_id": review["id"],
            "pipeline_name": pr["repository"]["name"],
            "pr_number": pr["number"],
            "pr_author": _actor_login(pr.get("author")),
            "reviewer": _actor_login(review.get("author")),
            "state": review["state"],
            "submitted_at": review["submittedAt"],
        }


def _reviews_updated(organization: str, headers: dict, start: date, end: date, budget: _PageBudget) -> Iterator[dict]:
    """Yield submitted reviews on PRs updated in [start, end], splitting ranges over the search cap."""
    if start > end:
        return

    query = f"org:{organization} is:pr updated:{start.isoformat()}..{end.isoformat()}"
    cursor = None
    saw_count = False
    while True:
        budget.charge()
        search = github_graphql(_PR_SEARCH, {"q": query, "cursor": cursor}, headers)["search"]
        if not saw_count:
            saw_count = True
            count = search["issueCount"]
            if count > _SEARCH_RESULT_CAP and start < end:
                mid = start + (end - start) // 2
                logger.info(f"{count} PRs updated {start}..{end}; splitting the search")
                yield from _reviews_updated(organization, headers, start, mid, budget)
                yield from _reviews_updated(organization, headers, mid + timedelta(days=1), end, budget)
                return
            if count > _SEARCH_RESULT_CAP:
                logger.warning(
                    f"{count} PRs updated on {start}. GitHub search returns {_SEARCH_RESULT_CAP}, so the rest are skipped."
                )
            else:
                logger.info(f"{count} PRs updated {start}..{end}")

        for pr in search["nodes"]:
            if not pr or "repository" not in pr:
                continue
            reviews = pr["reviews"]
            yield from _review_rows(pr, reviews["nodes"])
            page = reviews["pageInfo"]
            while page["hasNextPage"]:
                budget.charge()
                reviews = github_graphql(_REVIEW_PAGE, {"id": pr["id"], "cursor": page["endCursor"]}, headers)["node"][
                    "reviews"
                ]
                yield from _review_rows(pr, reviews["nodes"])
                page = reviews["pageInfo"]

        if not search["pageInfo"]["hasNextPage"]:
            return
        cursor = search["pageInfo"]["endCursor"]


@dlt.resource(write_disposition="merge", primary_key="review_id", name="pr_reviews")
def pr_reviews(
    organization: str,
    headers: dict,
    page_budget: int | None = PR_REVIEW_PAGE_BUDGET,
) -> Iterator[dict]:
    """Collect submitted PR reviews.

    One GraphQL search returns a page of pull requests with their reviews nested, instead of
    one REST call per pull request. Each run re-reads pull requests updated in the last two days,
    then walks older update dates back to `PR_REVIEW_HISTORY_START` within `page_budget` pages.
    The older-date cursor is saved only after a week finishes, so a budget stop retries that week.
    """
    state = dlt.current.resource_state()
    today = datetime.now(timezone.utc).date()
    # The latest two days are always re-read: a new review bumps the pull request's update time.
    yield from _reviews_updated(organization, headers, today - timedelta(days=1), today, _PageBudget(None))

    history_before = date.fromisoformat(
        state.setdefault("history_before", (today - timedelta(days=1)).isoformat())
    )
    budget = _PageBudget(page_budget)
    while history_before > PR_REVIEW_HISTORY_START:
        week_end = history_before - timedelta(days=1)
        week_start = max(PR_REVIEW_HISTORY_START, week_end - timedelta(days=6))
        try:
            yield from _reviews_updated(organization, headers, week_start, week_end, budget)
        except _PageBudgetExhaustedError:
            logger.info(
                f"PR review page budget reached while scanning {week_start}..{week_end}. "
                "Older pull requests resume on the next run."
            )
            return
        history_before = week_start
        state["history_before"] = history_before.isoformat()
        logger.info(f"PR review history scanned back to {week_start.isoformat()}")


@dlt.resource(write_disposition="merge", primary_key=["timestamp"])
def org_members(organization: str, headers: dict) -> Iterator[dict]:
    """Collect organization member count"""
    logger.info(f"Collecting organization member count for {organization}")
    members_url = f"https://api.github.com/orgs/{organization}/members"

    members = get_paginated_data(members_url, headers)
    logger.info(f"Found {len(members)} members in {organization}")
    yield {"timestamp": datetime.now(timezone.utc).timestamp(), "num_members": len(members)}


@dlt.resource(write_disposition="merge", primary_key=["name"], name="nfcore_pipelines")
def pipelines(organization: str, headers: dict, repos: list[dict]) -> Iterator[dict]:
    """Collect pipeline information"""
    logger.info(f"Collecting pipeline information for {len(repos)} repositories")
    # Get pipeline names from nf-core website
    pipeline_names_url = "https://raw.githubusercontent.com/nf-core/website/main/public/pipeline_names.json"
    try:
        pipeline_names = github_request(pipeline_names_url, headers).json()
    except RateLimitError:
        raise
    except requests.RequestException as e:
        logger.warning(f"Failed to get pipeline names from nf-core website: {e}")
        return

    for pipeline_name in pipeline_names.get("pipeline", []):
        pipeline = next((repo for repo in repos if repo["name"] == pipeline_name), None)
        if not pipeline:
            logger.warning(f"{pipeline_name} is not a pipeline")
            continue

        # Get releases (stable only: excludes drafts, prereleases and unpublished)
        release_url = f"https://api.github.com/repos/{organization}/{pipeline_name}/releases?per_page=100"
        try:
            releases = get_paginated_data(release_url, headers)
        except RateLimitError:
            raise
        except requests.RequestException as e:
            # Resource merges on primary_key=["name"], so yielding NULLs here would
            # overwrite good release data. Skip the row instead and retry next run.
            logger.warning(f"Failed to get releases for {pipeline_name}, skipping: {e}")
            continue

        # GitHub sorts /releases by created_at, not published_at, so derive the
        # bounds from the dates themselves rather than the list order.
        release_dates = [
            r["published_at"]
            for r in releases
            if r.get("published_at") and not r.get("draft") and not r.get("prerelease")
        ]
        number_of_releases = len(release_dates)
        first_release_date = min(release_dates) if release_dates else None
        last_release_date = max(release_dates) if release_dates else None

        yield {
            "name": pipeline["name"],
            "description": pipeline["description"] or "",
            "gh_created_at": pipeline["created_at"],
            "gh_updated_at": pipeline["updated_at"],
            "gh_pushed_at": pipeline["pushed_at"],
            "stargazers_count": pipeline["stargazers_count"],
            "watchers_count": pipeline["watchers_count"],
            "forks_count": pipeline["forks_count"],
            "open_issues_count": pipeline["open_issues_count"],
            "topics": pipeline["topics"],
            "default_branch": pipeline["default_branch"],
            "archived": pipeline["archived"],
            "last_release_date": last_release_date,
            "first_release_date": first_release_date,
            "number_of_releases": number_of_releases,
            "category": "pipeline",
        }

    # add all repos that are not pipelines to core_repos
    for repo in repos:
        if repo["name"] not in pipeline_names.get("pipeline", []):
            logger.info(f"Adding {repo['name']} to core_repos")
            yield {
                "name": repo["name"],
                "description": repo["description"] or "",
                "gh_created_at": repo["created_at"],
                "gh_updated_at": repo["updated_at"],
                "gh_pushed_at": repo["pushed_at"],
                "stargazers_count": repo["stargazers_count"],
                "watchers_count": repo["watchers_count"],
                "forks_count": repo["forks_count"],
                "open_issues_count": repo["open_issues_count"],
                "topics": repo["topics"],
                "default_branch": repo["default_branch"],
                "archived": repo["archived"],
                "category": "core",
            }


@dlt.resource(write_disposition="merge", primary_key=["pipeline_name", "timestamp"])
def commit_stats(organization: str, headers: dict, repos: list[dict]) -> Iterator[dict]:
    """Collect commit statistics over time with incremental loading"""
    # Get state for incremental loading
    state = dlt.current.source_state()
    last_commit_check = state.setdefault("last_commit_check", {})

    logger.info(f"Collecting commit statistics for {len(repos)} repositories (incremental mode)")

    for repo in repos:
        name = repo["name"]

        # Check if we have a last check time for this repo
        since_date = last_commit_check.get(name)

        # Build URL - only use 'since' parameter if we have a previous state
        if since_date:
            commits_url = f"https://api.github.com/repos/{organization}/{name}/commits?since={since_date}&per_page=100"
            logger.debug(f"Fetching commits for {name} since {since_date} (incremental)")
        else:
            commits_url = f"https://api.github.com/repos/{organization}/{name}/commits?per_page=100"
            logger.info(f"Fetching all commits for {name} (first run)")

        try:
            commits = get_paginated_data(commits_url, headers)
            if not isinstance(commits, list):
                continue

            # Update last check time for this repo to now
            last_commit_check[name] = datetime.now(timezone.utc).isoformat()

        except RateLimitError:
            raise
        except requests.RequestException as e:
            logger.warning(f"Failed to get commits for {name}: {e}")
            continue

        if not commits:
            logger.debug(f"No new commits for {name}")
            continue

        logger.info(f"Found {len(commits)} commits for {name}")

        # Group commits by week
        commit_counts: dict[int, int] = {}
        for commit in commits:
            commit_date = commit.get("commit", {}).get("author", {}).get("date")
            if not commit_date:
                continue

            commit_time = datetime.strptime(commit_date, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            week_start = commit_time - timedelta(days=commit_time.weekday())
            week_timestamp = int(week_start.timestamp())

            commit_counts[week_timestamp] = commit_counts.get(week_timestamp, 0) + 1

        # Yield all data for this repo
        for timestamp, commit_count in commit_counts.items():
            yield {
                "pipeline_name": name,
                "timestamp": timestamp,
                "number_of_commits": commit_count,
            }


@dlt.resource(write_disposition="append", primary_key=["timestamp"])
def modules_container_conversion(headers: dict) -> Iterator[dict]:
    """Track nf-core/modules containing 'linux/amd64' in meta.yml files, to track new container syntax."""
    logger.info("Scanning nf-core/modules for linux/amd64 usage in meta.yml")

    try:
        archive_url = "https://codeload.github.com/nf-core/modules/zip/refs/heads/master"
        logger.info("Downloading nf-core/modules repository archive")
        response = github_request(archive_url, headers)

        total_modules = 0
        total_with_pattern = 0
        total_with_topics_version = 0
        total_with_wave = 0

        logger.info("Scanning repository archive for meta.yml and main.nf files")
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            for entry in archive.infolist():
                if entry.is_dir():
                    continue
                path = entry.filename
                if "/modules/nf-core/" not in path:
                    continue
                if path.endswith("meta.yml"):
                    total_modules += 1
                    content = archive.read(entry).decode("utf-8", errors="replace")
                    if "linux/amd64" in content:
                        total_with_pattern += 1
                    if "topics:" in content and "versions:" in content:
                        total_with_topics_version += 1
                elif path.endswith("main.nf"):
                    content = archive.read(entry).decode("utf-8", errors="replace")
                    if "community.wave.seqera.io/library/" in content:
                        total_with_wave += 1

        logger.info(f"Found {total_modules} meta.yml files in modules/nf-core/")
        logger.info(f"Total meta.yml files with linux/amd64: {total_with_pattern}/{total_modules}")
        logger.info(f"Total meta.yml files with topics: versions: {total_with_topics_version}/{total_modules}")
        logger.info(f"Total modules in repository: {total_modules}")
        logger.info(f"Total main.nf files with community.wave.seqera.io/library/: {total_with_wave}/{total_modules}")

    except Exception as e:
        logger.error(f"Failed to count modules: {e}")
        raise

    # Calculate stats
    modules_without_pattern = total_modules - total_with_pattern if total_modules else None
    modules_without_topics_version = total_modules - total_with_topics_version if total_modules else None
    modules_without_wave = total_modules - total_with_wave if total_modules else None

    result = {
        "timestamp": datetime.now().isoformat(),
        "total_modules": total_modules,
        "modules_new_container_syntax": total_with_pattern,
        "modules_old_container_syntax": modules_without_pattern,
        "modules_with_topics_version": total_with_topics_version,
        "modules_without_topics_version": modules_without_topics_version,
        "modules_with_wave_containers": total_with_wave,
        "modules_without_wave_containers": modules_without_wave,
    }

    logger.info(
        f"modules container conversion: {total_with_pattern}/{total_modules} modules use linux/amd64. \n modules container conversion: data collected"
    )

    yield result


def main(
    *,
    destination: str = "motherduck",
    resources: list[
        Literal[
            "org_members",
            "nfcore_pipelines",
            "commit_stats",
            "traffic_stats",
            "issue_stats",
            "contributor_stats",
            "modules_container_conversion",
            "pr_reviews",
        ]
    ]
    | None = None,
    traffic_only_active_repos: bool = False,
    traffic_max_repos: int | None = None,
    max_repos: int | None = None,
):
    """
    Run the github data ingestion pipeline

    Args:
        destination: dlt backend. Use 'motherduck' for production. Can use 'duckdb' for local testing
        resources: Resources to run. If None, run all resources.
        traffic_only_active_repos:
            Only collect traffic for repos updated in last 6 months (default False - all repos).
        traffic_max_repos: Limit to top N repos by stars (default None - all repos)
        max_repos:
            Limit to the first N org repos across all resources (default None - all repos).
            CI smoke mode: used on PR runs only, to keep feedback fast. Production
            push/schedule runs leave this unset so the dataset stays complete.
    """
    logger.info("Starting GitHub data pipeline...")
    pipeline = dlt.pipeline(pipeline_name="github", destination=destination, dataset_name="github")

    # Configuration
    organization = "nf-core"

    # Initialize headers and repos once (this will get the token from secrets)
    headers = get_github_headers()

    # Check initial rate limit
    logger.info("Checking initial rate limit status...")
    check_rate_limit(headers)

    repos_url = f"https://api.github.com/orgs/{organization}/repos"
    repos = get_paginated_data(repos_url, headers)
    logger.info(f"Successfully fetched {len(repos)} repositories from GitHub API")

    if max_repos:
        repos = repos[:max_repos]
        logger.info(f"Smoke mode: limited to {len(repos)} repositories")

    # Define resources to run (ordered by API call intensity - least to most)
    # GraphQL reviews sit with the cheap calls. The page budget keeps a backfill from
    # bursting the shared token before the REST resources run. Smoke mode still refreshes
    # the last two days, and caps the history walk at one page.
    review_budget = 1 if max_repos else PR_REVIEW_PAGE_BUDGET
    all_resources = [
        ("org_members", lambda: org_members(organization, headers)),
        ("modules_container_conversion", lambda: modules_container_conversion(headers)),
        ("pr_reviews", lambda: pr_reviews(organization, headers, page_budget=review_budget)),
        ("nfcore_pipelines", lambda: pipelines(organization, headers, repos)),
        ("commit_stats", lambda: commit_stats(organization, headers, repos)),
        (
            "traffic_stats",
            lambda: traffic_stats(
                organization, headers, repos, only_active_repos=traffic_only_active_repos, max_repos=traffic_max_repos
            ),
        ),
        ("issue_stats", lambda: issue_stats(organization, headers, repos)),
        (
            "contributor_stats",
            lambda: contributor_stats(organization, headers, repos),
        ),
    ]
    resources_to_run = all_resources if resources is None else filter(lambda x: x[0] in resources, all_resources)

    total_rows_processed = 0
    failed_resources = []

    for resource_name, resource_func in resources_to_run:
        try:
            logger.info(f"Processing resource: {resource_name}")

            # Run just this resource
            pipeline.run(resource_func())

            # Log results for this resource
            if pipeline.last_trace and pipeline.last_trace.last_normalize_info:
                row_counts = pipeline.last_trace.last_normalize_info.row_counts
                resource_rows = sum(row_counts.values())
                total_rows_processed += resource_rows
                logger.info(f"✅ {resource_name} completed: {resource_rows} rows processed")

                for table_name, count in row_counts.items():
                    logger.info(f"  {table_name}: {count} rows")
            else:
                logger.info(f"✅ {resource_name} completed (no row count info)")

        except Exception as e:
            rate_limit_error = find_rate_limit_error(e)
            if rate_limit_error is not None:
                logger.error(f"❌ Rate limit hit during {resource_name}: {rate_limit_error}. Stopping pipeline.")
                break
            logger.error(f"❌ Failed to process {resource_name}: {e}")
            logger.info("Continuing with next resource...")
            failed_resources.append(resource_name)
            continue

    logger.info("=== PIPELINE COMPLETION SUMMARY ===")
    logger.info(f"Total rows processed across all resources: {total_rows_processed}")

    if failed_resources:
        raise RuntimeError(f"GitHub data pipeline completed with failed resources: {', '.join(failed_resources)}")

    logger.info("GitHub data pipeline completed!")
