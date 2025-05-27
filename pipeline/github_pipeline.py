import logging
import os
from collections.abc import Iterator
from datetime import datetime

import dlt
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("github_pipeline")

# Load environment variables
load_dotenv()


def get_github_headers():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable is not set")
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }


def get_paginated_results(url: str, headers: dict) -> tuple[list[dict], list[str]]:
    """Get all paginated results from a GitHub API endpoint"""
    all_results = []
    skipped_urls = []

    while True:
        response = requests.get(url, headers=headers)
        if response.status_code == 202:
            # GitHub is computing the data
            logger.warning(f"GitHub is computing data for {url}, skipping...")
            skipped_urls.append(url)

        results = response.json()
        # Handle both list and dict responses
        if isinstance(results, dict) and "items" in results:
            all_results.extend(results["items"])
        elif isinstance(results, list):
            all_results.extend(results)
        else:
            # For non-paginated responses (like traffic data)
            return results

        if "next" not in response.links:
            break
        url = response.links["next"]["url"]

    return all_results, skipped_urls


def get_all_repos(organization: str, headers: dict) -> list[dict]:
    """Get all repositories for an organization"""
    repos_url = f"https://api.github.com/orgs/{organization}/repos"
    results = get_paginated_results(repos_url, headers)
    all_repos = results if isinstance(results, list) else []
    logger.info(f"Found {len(all_repos)} repositories in {organization}")
    return all_repos


@dlt.source(name="github")
def github_source(organization: str = "nf-core"):
    """DLT source for GitHub statistics"""
    headers = get_github_headers()
    all_repos = get_all_repos(organization, headers)

    return [
        dlt.resource(
            traffic_stats_resource(organization, headers, all_repos),
            name="traffic_stats",
        ),
        dlt.resource(
            contributor_stats_resource(organization, headers, all_repos),
            name="contributor_stats",
        ),
        dlt.resource(
            issue_stats_resource(organization, headers, all_repos), name="issue_stats"
        ),
        dlt.resource(org_members_resource(organization), name="org_members"),
    ]


@dlt.resource(
    name="traffic_stats",
    write_disposition="merge",
    primary_key=["pipeline_name", "timestamp"],
)
def traffic_stats_resource(
    organization: str, headers: dict, repos: list[dict]
) -> Iterator[dict]:
    """Collect traffic stats for each repository"""
    entry_count = 0

    for repo in repos:
        pipeline_name = repo["name"]

        # Get views - traffic endpoints don't support pagination
        views_url = (
            f"https://api.github.com/repos/{organization}/{pipeline_name}/traffic/views"
        )
        views_result = get_paginated_results(views_url, headers)
        views_data = views_result if isinstance(views_result, dict) else {"views": []}

        # Get clones - traffic endpoints don't support pagination
        clones_url = f"https://api.github.com/repos/{organization}/{pipeline_name}/traffic/clones"
        clones_result = get_paginated_results(clones_url, headers)
        clones_data = (
            clones_result if isinstance(clones_result, dict) else {"clones": []}
        )

        # Combine and yield data
        for view in views_data.get("views", []):
            timestamp = view["timestamp"]

            # Find matching clone data
            clone_data = next(
                (
                    c
                    for c in clones_data.get("clones", [])
                    if c["timestamp"] == timestamp
                ),
                {"count": 0, "uniques": 0},
            )

            entry_count += 1
            yield {
                "pipeline_name": pipeline_name,
                "timestamp": timestamp,
                "views": view["count"],
                "views_uniques": view["uniques"],
                "clones": clone_data["count"],
                "clones_uniques": clone_data["uniques"],
            }

    logger.info(f"Collected {entry_count} traffic stat entries")


@dlt.resource(
    name="contributor_stats",
    write_disposition="merge",
    primary_key=["pipeline_name", "author", "week_date"],
)
def contributor_stats_resource(
    organization: str, headers: dict, repos: List[dict]
) -> Iterator[dict]:
    """Collect contributor stats for each repository"""
    entry_count = 0

    for repo in repos:
        pipeline_name = repo["name"]

        # Get contributor stats
        stats_url = f"https://api.github.com/repos/{organization}/{pipeline_name}/stats/contributors"
        stats = get_paginated_results(stats_url, headers)

        if not stats:  # Skip if GitHub is still computing stats
            continue

        logger.debug(f"Found {len(stats)} contributors for {pipeline_name}")

        for contributor in stats:
            author = contributor["author"]["login"]
            avatar_url = contributor["author"]["avatar_url"]

            for week in contributor["weeks"]:
                entry_count += 1
                yield {
                    "pipeline_name": pipeline_name,
                    "author": author,
                    "avatar_url": avatar_url,
                    "week_date": datetime.fromtimestamp(week["w"]).strftime("%Y-%m-%d"),
                    "week_additions": week["a"],
                    "week_deletions": week["d"],
                    "week_commits": week["c"],
                }

    logger.info(f"Collected {entry_count} contributor stat entries")


@dlt.resource(
    name="issue_stats",
    write_disposition="merge",
    primary_key=["pipeline_name", "issue_number"],
)
def issue_stats_resource(
    organization: str, headers: dict, repos: List[dict]
) -> Iterator[dict]:
    """Collect issue stats for each repository"""
    entry_count = 0

    for repo in repos:
        pipeline_name = repo["name"]

        # Get all issues (including PRs) with pagination
        issues_url = f"https://api.github.com/repos/{organization}/{pipeline_name}/issues?state=all"
        issues = get_paginated_results(issues_url, headers)

        logger.debug(f"Found {len(issues)} issues for {pipeline_name}")

        for issue in issues:
            is_pr = "pull_request" in issue

            created_at = issue["created_at"]
            closed_at = issue["closed_at"]
            closed_wait = None

            if closed_at:
                created_timestamp = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                closed_timestamp = datetime.strptime(closed_at, "%Y-%m-%dT%H:%M:%SZ")
                closed_wait = (closed_timestamp - created_timestamp).total_seconds()

            entry_count += 1
            yield {
                "pipeline_name": pipeline_name,
                "issue_number": issue["number"],
                "issue_type": "pr" if is_pr else "issue",
                "state": issue["state"],
                "created_by": issue["user"]["login"],
                "created_at": created_at,
                "updated_at": issue["updated_at"],
                "closed_at": closed_at,
                "closed_wait_seconds": closed_wait,
                "num_comments": issue["comments"],
                "html_url": issue["html_url"],
            }

    logger.info(f"Collected {entry_count} issue stat entries")


@dlt.resource(
    name="org_members",
    write_disposition="merge",
    primary_key=["timestamp"],
)
def org_members_resource(organization: str) -> Iterator[dict]:
    """Collect member stats for the whole organization"""
    headers = get_github_headers()

    # Get all members in the organization with pagination
    members_url = f"https://api.github.com/orgs/{organization}/members"
    members = get_paginated_results(members_url, headers)

    logger.info(f"Found {len(members)} members in {organization}")

    yield {
        "timestamp": datetime.now().timestamp(),
        "num_members": len(members),
    }


if __name__ == "__main__":
    # Initialize the pipeline with DuckDB destination
    pipeline = dlt.pipeline(
        pipeline_name="github", destination="motherduck", dataset_name="github"
    )

    # Run the pipeline
    logger.info("Starting GitHub data pipeline run")
    load_info = pipeline.run(github_source())

    # Log detailed information about what was loaded
    logger.info("=== Pipeline Run Summary ===")

    for load_package in load_info.load_packages:
        logger.info(load_package)
