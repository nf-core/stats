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


def get_github_headers(api_token: str = dlt.secrets.value):
    """Get GitHub API headers with authentication"""
    if not api_token:
        raise ValueError("GitHub API token is not configured. Please set SOURCES__GITHUB__API_TOKEN in your secrets.")
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
        dlt.resource(traffic_stats(organization, headers, repos), name="traffic_stats"),
        dlt.resource(contributor_stats(organization, headers, repos), name="contributor_stats"),
        dlt.resource(issue_stats(organization, headers, repos), name="issue_stats"),
        dlt.resource(org_members(organization, headers), name="org_members"),
        dlt.resource(commit_stats(organization, headers, repos), name="commit_stats"),
        dlt.resource(pipelines(organization, headers, repos), name="nfcore_pipelines"),
    ]


@dlt.resource(write_disposition="merge", primary_key=["pipeline_name", "timestamp"])
def traffic_stats(organization: str, headers: dict, repos: list[dict]) -> Iterator[dict]:
    """Collect traffic stats for repositories"""
    logger.info(f"Collecting traffic stats for {len(repos)} repositories")
    for repo in repos:
        name = repo["name"]

        # Get views and clones
        views_url = f"https://api.github.com/repos/{organization}/{name}/traffic/views"
        clones_url = f"https://api.github.com/repos/{organization}/{name}/traffic/clones"

        try:
            views_data = github_request(views_url, headers).json()
            clones_data = github_request(clones_url, headers).json()
        except requests.RequestException as e:
            # Traffic data requires push access - skip if not available
            if "403" in str(e) or "Forbidden" in str(e):
                logger.info(f"Skipping traffic data for {name} (requires push access)")
            else:
                logger.warning(f"Failed to get traffic data for {name}: {e}")
            continue

        # Combine data by timestamp
        for view in views_data.get("views", []):
            timestamp = view["timestamp"]
            clone_data = next(
                (c for c in clones_data.get("clones", []) if c["timestamp"] == timestamp), {"count": 0, "uniques": 0}
            )

            yield {
                "pipeline_name": name,
                "timestamp": timestamp,
                "views": view["count"],
                "views_uniques": view["uniques"],
                "clones": clone_data["count"],
                "clones_uniques": clone_data["uniques"],
            }


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
                        "week_reviews": 0,
                        "week_approvals": 0,
                    }

        # Get PR review stats
        prs_url = f"https://api.github.com/repos/{organization}/{name}/pulls?state=all"
        try:
            prs = get_paginated_data(prs_url, headers)
            if not isinstance(prs, list):
                continue
        except requests.RequestException as e:
            logger.warning(f"Failed to get PR data for {name}: {e}")
            continue

        for pr in prs:
            reviews_url = f"https://api.github.com/repos/{organization}/{name}/pulls/{pr['number']}/reviews"
            try:
                reviews = get_paginated_data(reviews_url, headers)
                if not isinstance(reviews, list):
                    continue
            except requests.RequestException as e:
                logger.warning(f"Failed to get review data for PR {pr['number']} in {name}: {e}")
                continue

            for review in reviews:
                if not (review.get("submitted_at") and review.get("user", {}).get("login")):
                    continue

                reviewer = review["user"]["login"]
                review_date = datetime.strptime(review["submitted_at"], "%Y-%m-%dT%H:%M:%SZ")
                week_start = review_date - timedelta(days=review_date.weekday())
                week_date = week_start.strftime("%Y-%m-%d")
                key = (reviewer, week_date)

                if key not in contributor_data:
                    contributor_data[key] = {
                        "pipeline_name": name,
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
                if review.get("state") == "APPROVED":
                    contributor_data[key]["week_approvals"] += 1

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
    load_info = pipeline.run(github_source())

    # Log final summary using DLT's built-in statistics
    logger.info("=== PIPELINE COMPLETION SUMMARY ===")

    # Get row counts from the normalize info
    if pipeline.last_trace and pipeline.last_trace.last_normalize_info:
        row_counts = pipeline.last_trace.last_normalize_info.row_counts
        total_rows = sum(row_counts.values())
        logger.info(f"Total rows processed: {total_rows}")

        for table_name, count in row_counts.items():
            logger.info(f"  {table_name}: {count} rows")
    else:
        logger.info("No row count information available")

    # Log package information from load_info
    if load_info.load_packages:
        for package in load_info.load_packages:
            logger.info(f"Load package {package.load_id}: {package.state}")
            for job_type, jobs in package.jobs.items():
                if jobs:
                    logger.info(f"  {job_type}: {len(jobs)} jobs")

    logger.info("=== DLT LOAD INFO ===")
    print(load_info)

    logger.info("GitHub data pipeline completed successfully!")
