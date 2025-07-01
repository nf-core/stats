import logging
import os
import time
from collections.abc import Iterator
from datetime import datetime, timedelta
from typing import Union

import dlt
import requests
from dotenv import load_dotenv
from requests.exceptions import ConnectionError, RequestException, Timeout
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
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


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=60),
    retry=retry_if_exception_type((ConnectionError, Timeout, RequestException)),
    reraise=True,
)
def make_github_request(url: str, headers: dict) -> requests.Response:
    """Make a single request to GitHub API with retry logic"""
    logger.debug(f"Making request to: {url}")
    response = requests.get(url, headers=headers, timeout=30)

    # Check for rate limiting
    if response.status_code == 403 and "rate limit" in response.text.lower():
        reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
        current_time = int(time.time())
        wait_time = max(reset_time - current_time, 60)  # Wait at least 1 minute
        logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds...")
        time.sleep(wait_time)
        # Retry the request after waiting
        response = requests.get(url, headers=headers, timeout=30)

    response.raise_for_status()
    return response


def get_paginated_results(url: str, headers: dict) -> tuple[Union[list[dict], dict], list[str]]:
    """Get all paginated results from a GitHub API endpoint"""
    all_results = []
    skipped_urls = []

    while True:
        try:
            response = make_github_request(url, headers)

            if response.status_code == 202:
                # GitHub is computing the data
                logger.warning(f"GitHub is computing data for {url}, skipping...")
                skipped_urls.append(url)
                break

            results = response.json()

            # Handle both list and dict responses
            if isinstance(results, dict) and "items" in results:
                all_results.extend(results["items"])
            elif isinstance(results, list):
                all_results.extend(results)
            else:
                # For non-paginated responses (like traffic data)
                return results, skipped_urls

            if "next" not in response.links:
                break
            url = response.links["next"]["url"]

        except Exception as e:
            logger.error(f"Failed to get data from {url} after retries: {e}")
            skipped_urls.append(url)
            break

    # Ensure we always return a list for paginated results
    if not isinstance(all_results, list):
        logger.warning(f"Expected list but got {type(all_results)} for {url}")
        return [], skipped_urls

    return all_results, skipped_urls


def get_all_repos(organization: str, headers: dict) -> list[dict]:
    """Get all repositories for an organization"""
    repos_url = f"https://api.github.com/orgs/{organization}/repos"
    results, _ = get_paginated_results(repos_url, headers)
    all_repos = results if isinstance(results, list) else []
    logger.info(f"Found {len(all_repos)} repositories in {organization}")
    return all_repos


@dlt.source(name="github")
def github_source(organization: str = "nf-core"):
    """DLT source for GitHub statistics"""
    headers = get_github_headers()
    all_repos = get_all_repos(organization, headers)

    return [
        dlt.resource(pipelines_resource(organization, headers, all_repos), name="nfcore_pipelines"),
        dlt.resource(
            traffic_stats_resource(organization, headers, all_repos),
            name="traffic_stats",
        ),
        dlt.resource(
            contributor_stats_resource(organization, headers, all_repos),
            name="contributor_stats",
        ),
        dlt.resource(issue_stats_resource(organization, headers, all_repos), name="issue_stats"),
        dlt.resource(org_members_resource(organization), name="org_members"),
        dlt.resource(commit_stats_resource(organization, headers, all_repos), name="commit_stats"),
    ]


@dlt.resource(
    name="traffic_stats",
    write_disposition="merge",
    primary_key=["pipeline_name", "timestamp"],
)
def traffic_stats_resource(organization: str, headers: dict, repos: list[dict]) -> Iterator[dict]:
    """Collect traffic stats for each repository"""
    entry_count = 0

    for repo in repos:
        pipeline_name = repo["name"]
        logger.info(f"Collecting traffic stats for {pipeline_name}")

        # Get views - traffic endpoints don't support pagination
        views_url = f"https://api.github.com/repos/{organization}/{pipeline_name}/traffic/views"
        views_result, skipped_urls = get_paginated_results(views_url, headers)
        if skipped_urls:
            logger.info(f"Skipped {len(skipped_urls)} views for {pipeline_name}. Rerunning...")
            for url in skipped_urls:
                views_result, _ = get_paginated_results(url, headers)
                # Traffic endpoints return single dict, no need to extend
        logger.info(f"Views result: {views_result}")
        views_data = views_result if isinstance(views_result, dict) else {"views": []}
        logger.info(f"Views data: {views_data}")

        # Get clones - traffic endpoints don't support pagination
        clones_url = f"https://api.github.com/repos/{organization}/{pipeline_name}/traffic/clones"
        clones_result, skipped_urls = get_paginated_results(clones_url, headers)
        if skipped_urls:
            logger.info(f"Skipped {len(skipped_urls)} clones for {pipeline_name}. Rerunning...")
            for url in skipped_urls:
                clones_result, _ = get_paginated_results(url, headers)
                # Traffic endpoints return single dict, no need to extend

        clones_data = clones_result if isinstance(clones_result, dict) else {"clones": []}

        # Combine and yield data
        for view in views_data.get("views", []):
            timestamp = view["timestamp"]

            # Find matching clone data
            clone_data = next(
                (c for c in clones_data.get("clones", []) if c["timestamp"] == timestamp),
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
def contributor_stats_resource(organization: str, headers: dict, repos: list[dict]) -> Iterator[dict]:
    """Collect contributor stats including commits and PR reviews for each repository"""
    entry_count = 0

    for repo in repos:
        pipeline_name = repo["name"]
        logger.info(f"Collecting contributor stats for {pipeline_name}")

        # Dictionary to store all contributor data by week
        contributor_data = {}

        # Get commit contributor stats
        stats_url = f"https://api.github.com/repos/{organization}/{pipeline_name}/stats/contributors"
        stats, skipped_urls = get_paginated_results(stats_url, headers)
        if skipped_urls:
            logger.info(f"Skipped {len(skipped_urls)} contributors for {pipeline_name}. Rerunning...")
            for url in skipped_urls:
                retry_stats, _ = get_paginated_results(url, headers)
                if isinstance(stats, list) and isinstance(retry_stats, list):
                    stats.extend(retry_stats)

        # Process commit stats
        if stats:
            logger.debug(f"Found {len(stats)} commit contributors for {pipeline_name}")
            for contributor in stats:
                author = contributor["author"]["login"]
                avatar_url = contributor["author"]["avatar_url"]

                for week in contributor["weeks"]:
                    week_date = datetime.fromtimestamp(week["w"]).strftime("%Y-%m-%d")
                    key = (author, week_date)

                    if key not in contributor_data:
                        contributor_data[key] = {
                            "pipeline_name": pipeline_name,
                            "author": author,
                            "avatar_url": avatar_url,
                            "week_date": week_date,
                            "week_additions": 0,
                            "week_deletions": 0,
                            "week_commits": 0,
                            "week_reviews": 0,
                            "week_approvals": 0,
                        }

                    contributor_data[key]["week_additions"] = week["a"]
                    contributor_data[key]["week_deletions"] = week["d"]
                    contributor_data[key]["week_commits"] = week["c"]

        # Get PR review stats
        logger.info(f"Collecting PR review stats for {pipeline_name}")
        prs_url = f"https://api.github.com/repos/{organization}/{pipeline_name}/pulls?state=all"
        prs, _ = get_paginated_results(prs_url, headers)

        logger.debug(f"Found {len(prs)} PRs for {pipeline_name}")

        for pr in prs:
            pr_number = pr["number"]

            # Get reviews for this PR
            reviews_url = f"https://api.github.com/repos/{organization}/{pipeline_name}/pulls/{pr_number}/reviews"
            reviews, _ = get_paginated_results(reviews_url, headers)

            # Process reviews
            for review in reviews:
                if review.get("submitted_at") and review.get("user") and review["user"].get("login"):
                    reviewer = review["user"]["login"]
                    review_date = review["submitted_at"]
                    review_timestamp = datetime.strptime(review_date, "%Y-%m-%dT%H:%M:%SZ")

                    # Round down to start of week (Monday)
                    week_start = review_timestamp - timedelta(days=review_timestamp.weekday())
                    week_date = week_start.strftime("%Y-%m-%d")

                    key = (reviewer, week_date)

                    if key not in contributor_data:
                        contributor_data[key] = {
                            "pipeline_name": pipeline_name,
                            "author": reviewer,
                            "avatar_url": review["user"].get("avatar_url", ""),
                            "week_date": week_date,
                            "week_additions": 0,
                            "week_deletions": 0,
                            "week_commits": 0,
                            "week_reviews": 0,
                            "week_approvals": 0,
                        }

                    contributor_data[key]["week_reviews"] += 1

                    # Count approvals (APPROVED state)
                    if review.get("state") == "APPROVED":
                        contributor_data[key]["week_approvals"] += 1

        # Yield all contributor data
        for data in contributor_data.values():
            entry_count += 1
            yield data

    logger.info(f"Collected {entry_count} contributor stat entries")


@dlt.resource(
    name="issue_stats",
    write_disposition="merge",
    primary_key=["pipeline_name", "issue_number"],
)
def issue_stats_resource(organization: str, headers: dict, repos: list[dict]) -> Iterator[dict]:
    """Collect issue stats and first response times for each repository"""
    entry_count = 0

    for repo in repos:
        pipeline_name = repo["name"]

        # Get all issues (including PRs) with pagination
        issues_url = f"https://api.github.com/repos/{organization}/{pipeline_name}/issues?state=all"
        issues, _ = get_paginated_results(issues_url, headers)

        logger.debug(f"Found {len(issues)} issues for {pipeline_name}")

        for issue in issues:
            is_pr = "pull_request" in issue
            issue_number = issue["number"]
            created_by = issue["user"]["login"]
            created_at = issue["created_at"]
            closed_at = issue["closed_at"]

            # Calculate close time
            closed_wait = None
            if closed_at:
                created_timestamp = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                closed_timestamp = datetime.strptime(closed_at, "%Y-%m-%dT%H:%M:%SZ")
                closed_wait = (closed_timestamp - created_timestamp).total_seconds()

            # Calculate first response time if there are comments
            first_response_time = None
            first_responder = None

            if issue["comments"] > 0:
                # Get comments for this issue
                comments_url = (
                    f"https://api.github.com/repos/{organization}/{pipeline_name}/issues/{issue_number}/comments"
                )
                comments, _ = get_paginated_results(comments_url, headers)

                # Debug logging to understand what we're getting
                logger.debug(f"Comments type: {type(comments)}, Comments value: {comments}")

                # Ensure comments is a list and not empty
                if comments and isinstance(comments, list):
                    created_timestamp = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")

                    # Find first comment not by the issue author
                    for comment in comments:
                        # Ensure comment is a dict and has the expected structure
                        if (
                            isinstance(comment, dict)
                            and "user" in comment
                            and comment["user"]
                            and "login" in comment["user"]
                        ):
                            comment_author = comment["user"]["login"]
                            if comment_author != created_by:  # First comment not by issue author
                                comment_timestamp = datetime.strptime(comment["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                                first_response_time = (comment_timestamp - created_timestamp).total_seconds()
                                first_responder = comment_author
                                break

            entry_count += 1
            yield {
                "pipeline_name": pipeline_name,
                "issue_number": issue_number,
                "issue_type": "pr" if is_pr else "issue",
                "state": issue["state"],
                "created_by": created_by,
                "created_at": created_at,
                "updated_at": issue["updated_at"],
                "closed_at": closed_at,
                "closed_wait_seconds": closed_wait,
                "first_response_seconds": first_response_time,
                "first_responder": first_responder,
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
    members, _ = get_paginated_results(members_url, headers)

    logger.info(f"Found {len(members)} members in {organization}")

    yield {
        "timestamp": datetime.now().timestamp(),
        "num_members": len(members),
    }


# generate a pipelines table
@dlt.resource(
    name="nfcore_pipelines",
    write_disposition="merge",
    primary_key=["name"],
)
def pipelines_resource(organization: str, headers: dict, repos: list[dict]) -> Iterator[dict]:
    """Collect pipeline stats for each repository"""
    headers = get_github_headers()

    # use https://github.com/nf-core/website/blob/main/public/pipeline_names.json as the source of pipeline names
    pipeline_names_url = "https://raw.githubusercontent.com/nf-core/website/main/public/pipeline_names.json"
    pipeline_names_response, _ = get_paginated_results(pipeline_names_url, headers)
    pipeline_names = pipeline_names_response if isinstance(pipeline_names_response, dict) else {}
    for pipeline_name in pipeline_names.get("pipeline", []):
        pipeline = next((repo for repo in repos if repo["name"] == pipeline_name), None)
        if pipeline:
            # get release date from github api
            release_url = f"https://api.github.com/repos/{organization}/{pipeline_name}/releases/latest"
            release, _ = get_paginated_results(release_url, headers)
            last_release_date = release.get("published_at") if isinstance(release, dict) else None
            yield {
                "name": pipeline["name"],
                "description": pipeline["description"],
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
            }


@dlt.resource(
    name="commit_stats",
    write_disposition="merge",
    primary_key=["pipeline_name", "timestamp"],
)
def commit_stats_resource(organization: str, headers: dict, repos: list[dict]) -> Iterator[dict]:
    """Collect commit stats for each repository over time"""
    entry_count = 0

    for repo in repos:
        pipeline_name = repo["name"]
        logger.info(f"Collecting commit stats for {pipeline_name}")

        # Get all commits with pagination
        commits_url = f"https://api.github.com/repos/{organization}/{pipeline_name}/commits"
        commits, _ = get_paginated_results(commits_url, headers)

        logger.debug(f"Found {len(commits)} commits for {pipeline_name}")

        # Group commits by week (similar to gh_commits.csv format)
        commit_counts = {}

        for commit in commits:
            if commit.get("commit", {}).get("author", {}).get("date"):
                commit_date = commit["commit"]["author"]["date"]
                commit_timestamp = datetime.strptime(commit_date, "%Y-%m-%dT%H:%M:%SZ")

                # Round down to start of week (Monday)
                week_start = commit_timestamp - timedelta(days=commit_timestamp.weekday())
                week_timestamp = int(week_start.timestamp())

                if week_timestamp not in commit_counts:
                    commit_counts[week_timestamp] = 0
                commit_counts[week_timestamp] += 1

        # Yield the aggregated data
        for timestamp, count in commit_counts.items():
            entry_count += 1
            yield {
                "pipeline_name": pipeline_name,
                "timestamp": timestamp,
                "number_of_commits": count,
            }

    logger.info(f"Collected {entry_count} commit stat entries")


if __name__ == "__main__":
    # Initialize the pipeline with DuckDB destination
    pipeline = dlt.pipeline(pipeline_name="github", destination="motherduck", dataset_name="github")

    # Run the pipeline
    logger.info("Starting GitHub data pipeline run")
    load_info = pipeline.run(github_source())

    # Log detailed information about what was loaded
    logger.info("=== Pipeline Run Summary ===")

    for load_package in load_info.load_packages:
        logger.info(load_package)
