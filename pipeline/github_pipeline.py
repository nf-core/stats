import os
import time
from collections.abc import Iterator
from datetime import datetime, timedelta
import logging

import dlt
import requests
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def get_github_headers(api_token: str = dlt.secrets["sources.github_pipeline.github.api_token"]):
    """Get GitHub API headers with authentication"""
    if not api_token:
        raise ValueError(
            "GitHub API token is not configured. Please set SOURCES__GITHUB_PIPELINE__GITHUB__API_TOKEN in your secrets."
        )
    return {"Authorization": f"token {api_token}", "Accept": "application/vnd.github.v3+json"}


def github_request(url: str, headers: dict) -> requests.Response:
    """Make GitHub API request with rate limit handling"""
    response = requests.get(url, headers=headers, timeout=30)

    # Handle rate limiting
    if response.status_code == 403 and "rate limit" in response.text.lower():
        reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
        wait_time = max(reset_time - int(time.time()), 60)
        logger.info(f"Rate limited. Waiting {wait_time} seconds...")
        time.sleep(wait_time)
        response = requests.get(url, headers=headers, timeout=30)

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
        dlt.resource(
            traffic_stats(organization, headers, repos, only_active_repos=True, max_repos=30), name="traffic_stats"
        ),
        dlt.resource(contributor_stats(organization, headers, repos), name="contributor_stats"),
        dlt.resource(issue_stats(organization, headers, repos), name="issue_stats"),
        dlt.resource(org_members(organization, headers), name="org_members"),
        dlt.resource(commit_stats(organization, headers, repos), name="commit_stats"),
        dlt.resource(pipelines(organization, headers, repos), name="nfcore_pipelines"),
    ]


@dlt.resource(write_disposition="merge", primary_key=["pipeline_name", "timestamp"])
def traffic_stats(
    organization: str, headers: dict, repos: list[dict], only_active_repos: bool = True, max_repos: int | None = 30
) -> Iterator[dict]:
    """Collect traffic stats for repositories with optimizations to reduce API burden

    Args:
        organization: GitHub organization name
        headers: GitHub API headers
        repos: List of repository data
        only_active_repos: Only collect traffic for recently active repos (default True)
        max_repos: Maximum number of repos to process (default 30, None for all)
    """
    # Filter repositories to reduce API calls
    filtered_repos = repos

    if only_active_repos:
        # Only get traffic for repos that have been updated in the last 6 months and are not archived
        six_months_ago = datetime.now() - timedelta(days=180)
        filtered_repos = [
            repo
            for repo in repos
            if datetime.strptime(repo["updated_at"], "%Y-%m-%dT%H:%M:%SZ") > six_months_ago and not repo["archived"]
        ]
        logger.info(f"Filtered to {len(filtered_repos)} active repositories (updated in last 6 months)")

    # Sort by stars/activity to prioritize important repos
    filtered_repos = sorted(filtered_repos, key=lambda x: x.get("stargazers_count", 0), reverse=True)

    if max_repos:
        filtered_repos = filtered_repos[:max_repos]
        logger.info(f"Limited to top {max_repos} repositories by stars")

    logger.info(f"Collecting traffic stats for {len(filtered_repos)} repositories (reduced from {len(repos)})")

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
        except requests.RequestException as e:
            logger.warning(f"Failed to get contributor stats for {name}: {e}")
            continue

        # Process commit stats
        for contributor in stats:
            author = contributor["author"]["login"]
            avatar_url = contributor["author"]["avatar_url"]

            for week in contributor["weeks"]:
                week_date = datetime.fromtimestamp(week["w"]).strftime("%Y-%m-%d")
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
def issue_stats(organization: str, headers: dict, repos: list[dict]) -> Iterator[dict]:
    """Collect issue and PR stats"""
    logger.info(f"Collecting issue and PR stats for {len(repos)} repositories")
    for repo in repos:
        name = repo["name"]
        issues_url = f"https://api.github.com/repos/{organization}/{name}/issues?state=all"

        try:
            issues = get_paginated_data(issues_url, headers)
            if not isinstance(issues, list):
                continue
        except requests.RequestException as e:
            logger.warning(f"Failed to get issues for {name}: {e}")
            continue

        for issue in issues:
            is_pr = "pull_request" in issue
            created_at = datetime.strptime(issue["created_at"], "%Y-%m-%dT%H:%M:%SZ")

            # Calculate close time
            closed_wait = None
            if issue["closed_at"]:
                closed_at = datetime.strptime(issue["closed_at"], "%Y-%m-%dT%H:%M:%SZ")
                closed_wait = (closed_at - created_at).total_seconds()

            # Calculate first response time
            first_response_time = None
            first_responder = None

            if issue["comments"] > 0:
                comments_url = f"https://api.github.com/repos/{organization}/{name}/issues/{issue['number']}/comments"
                try:
                    comments = get_paginated_data(comments_url, headers)
                    if isinstance(comments, list):
                        for comment in comments:
                            if (
                                comment.get("user", {}).get("login")
                                and comment["user"]["login"] != issue["user"]["login"]
                            ):
                                comment_time = datetime.strptime(comment["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                                first_response_time = (comment_time - created_at).total_seconds()
                                first_responder = comment["user"]["login"]
                                break
                except requests.RequestException as e:
                    logger.warning(f"Failed to get comments for issue {issue['number']} in {name}: {e}")
                    pass

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


@dlt.resource(write_disposition="merge", primary_key=["timestamp"])
def org_members(organization: str, headers: dict) -> Iterator[dict]:
    """Collect organization member count"""
    logger.info(f"Collecting organization member count for {organization}")
    members_url = f"https://api.github.com/orgs/{organization}/members"

    members = get_paginated_data(members_url, headers)
    logger.info(f"Found {len(members)} members in {organization}")
    yield {"timestamp": datetime.now().timestamp(), "num_members": len(members)}


@dlt.resource(write_disposition="merge", primary_key=["name"])
def pipelines(organization: str, headers: dict, repos: list[dict]) -> Iterator[dict]:
    """Collect pipeline information"""
    logger.info(f"Collecting pipeline information for {len(repos)} repositories")
    # Get pipeline names from nf-core website
    pipeline_names_url = "https://raw.githubusercontent.com/nf-core/website/main/public/pipeline_names.json"
    try:
        pipeline_names = github_request(pipeline_names_url, headers).json()
    except requests.RequestException as e:
        logger.warning(f"Failed to get pipeline names from nf-core website: {e}")
        return

    for pipeline_name in pipeline_names.get("pipeline", []):
        pipeline = next((repo for repo in repos if repo["name"] == pipeline_name), None)
        if not pipeline:
            logger.warning(f"{pipeline_name} is not a pipeline")
            continue

        # Get latest release
        release_url = f"https://api.github.com/repos/{organization}/{pipeline_name}/releases/latest"
        try:
            release = github_request(release_url, headers).json()
            last_release_date = release.get("published_at")
        except requests.RequestException as e:
            if "404" in str(e) or "Not Found" in str(e):
                logger.info(f"No releases found for {pipeline_name} (this is expected for new repositories)")
            else:
                logger.warning(f"Failed to get latest release for {pipeline_name}: {e}")
            last_release_date = None

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
    """Collect commit statistics over time"""
    logger.info(f"Collecting commit statistics for {len(repos)} repositories")
    for repo in repos:
        name = repo["name"]
        commits_url = f"https://api.github.com/repos/{organization}/{name}/commits"

        try:
            commits = get_paginated_data(commits_url, headers)
            if not isinstance(commits, list):
                continue
        except requests.RequestException as e:
            logger.warning(f"Failed to get commits for {name}: {e}")
            continue

        # Group commits by week
        commit_counts: dict[int, int] = {}
        for commit in commits:
            commit_date = commit.get("commit", {}).get("author", {}).get("date")
            if not commit_date:
                continue

            commit_time = datetime.strptime(commit_date, "%Y-%m-%dT%H:%M:%SZ")
            week_start = commit_time - timedelta(days=commit_time.weekday())
            week_timestamp = int(week_start.timestamp())

            commit_counts[week_timestamp] = commit_counts.get(week_timestamp, 0) + 1

        for timestamp, commit_count in commit_counts.items():
            yield {
                "pipeline_name": name,
                "timestamp": timestamp,
                "number_of_commits": commit_count,
            }


if __name__ == "__main__":
    logger.info("Starting GitHub data pipeline...")
    pipeline = dlt.pipeline(pipeline_name="github", destination="motherduck", dataset_name="github")

    # Configuration
    organization = "nf-core"

    # Traffic stats optimization settings to reduce API burden
    # This reduces API calls from ~100+ repos to ~30 most important active repos
    TRAFFIC_ONLY_ACTIVE_REPOS = True  # Only collect traffic for repos updated in last 6 months
    TRAFFIC_MAX_REPOS = 50  # Limit to top N repos by stars (None for all)

    # Initialize headers and repos once (this will get the token from secrets)
    headers = get_github_headers()
    repos_url = f"https://api.github.com/orgs/{organization}/repos"
    repos = get_paginated_data(repos_url, headers)
    logger.info(f"Successfully fetched {len(repos)} repositories from GitHub API")

    # Define resources to run (ordered by API call intensity - least to most)
    resources_to_run = [
        ("org_members", lambda: org_members(organization, headers)),
        ("nfcore_pipelines", lambda: pipelines(organization, headers, repos)),
        ("commit_stats", lambda: commit_stats(organization, headers, repos)),
        (
            "traffic_stats",
            lambda: traffic_stats(
                organization, headers, repos, only_active_repos=TRAFFIC_ONLY_ACTIVE_REPOS, max_repos=TRAFFIC_MAX_REPOS
            ),
        ),
        ("issue_stats", lambda: issue_stats(organization, headers, repos)),
        (
            "contributor_stats",
            lambda: contributor_stats(organization, headers, repos),
        ),
    ]

    total_rows_processed = 0

    for resource_name, resource_func in resources_to_run:
        try:
            logger.info(f"Processing resource: {resource_name}")

            # Run just this resource
            load_info = pipeline.run(resource_func())

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
            logger.error(f"❌ Failed to process {resource_name}: {e}")
            logger.info(f"Continuing with next resource...")
            continue

    logger.info("=== PIPELINE COMPLETION SUMMARY ===")
    logger.info(f"Total rows processed across all resources: {total_rows_processed}")
    logger.info("GitHub data pipeline completed!")
