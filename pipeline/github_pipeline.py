import dlt
from typing import Dict, Iterator, List
import os
from datetime import datetime
import requests
from dotenv import load_dotenv

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


@dlt.source(name="github")
def github_source(organization: str = "nf-core"):
    """DLT source for GitHub statistics"""
    return [
        dlt.resource(traffic_stats_resource(organization), name="traffic_stats"),
        dlt.resource(
            contributor_stats_resource(organization), name="contributor_stats"
        ),
        dlt.resource(issue_stats_resource(organization), name="issue_stats"),
    ]


@dlt.resource(
    name="traffic_stats",
    write_disposition="merge",
    primary_key=["pipeline_name", "timestamp"],
)
def traffic_stats_resource(organization: str) -> Iterator[Dict]:
    """Collect traffic stats for each repository"""
    headers = get_github_headers()

    # Get all repositories
    repos_url = f"https://api.github.com/orgs/{organization}/repos"
    response = requests.get(repos_url, headers=headers)
    repos = response.json()

    for repo in repos:
        pipeline_name = repo["name"]

        # Get views
        views_url = (
            f"https://api.github.com/repos/{organization}/{pipeline_name}/traffic/views"
        )
        views_response = requests.get(views_url, headers=headers)
        views_data = views_response.json()

        # Get clones
        clones_url = f"https://api.github.com/repos/{organization}/{pipeline_name}/traffic/clones"
        clones_response = requests.get(clones_url, headers=headers)
        clones_data = clones_response.json()

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

            yield {
                "pipeline_name": pipeline_name,
                "timestamp": timestamp,
                "views": view["count"],
                "views_uniques": view["uniques"],
                "clones": clone_data["count"],
                "clones_uniques": clone_data["uniques"],
                "source": "github_api",
            }


@dlt.resource(
    name="contributor_stats",
    write_disposition="merge",
    primary_key=["pipeline_name", "author", "week_date"],
)
def contributor_stats_resource(organization: str) -> Iterator[Dict]:
    """Collect contributor stats for each repository"""
    headers = get_github_headers()

    # Get all repositories
    repos_url = f"https://api.github.com/orgs/{organization}/repos"
    response = requests.get(repos_url, headers=headers)
    repos = response.json()

    for repo in repos:
        pipeline_name = repo["name"]

        # Get contributor stats
        stats_url = f"https://api.github.com/repos/{organization}/{pipeline_name}/stats/contributors"
        response = requests.get(stats_url, headers=headers)

        # Handle 202 response (GitHub is computing stats)
        if response.status_code == 202:
            # In production, you might want to implement retry logic here
            continue

        stats = response.json()

        for contributor in stats:
            author = contributor["author"]["login"]
            avatar_url = contributor["author"]["avatar_url"]

            for week in contributor["weeks"]:
                yield {
                    "pipeline_name": pipeline_name,
                    "author": author,
                    "avatar_url": avatar_url,
                    "week_date": datetime.fromtimestamp(week["w"]).strftime("%Y-%m-%d"),
                    "week_additions": week["a"],
                    "week_deletions": week["d"],
                    "week_commits": week["c"],
                }


@dlt.resource(
    name="issue_stats",
    write_disposition="merge",
    primary_key=["pipeline_name", "issue_number"],
)
def issue_stats_resource(organization: str) -> Iterator[Dict]:
    """Collect issue stats for each repository"""
    headers = get_github_headers()

    # Get all repositories
    repos_url = f"https://api.github.com/orgs/{organization}/repos"
    response = requests.get(repos_url, headers=headers)
    repos = response.json()

    for repo in repos:
        pipeline_name = repo["name"]

        # Get all issues (including PRs)
        issues_url = f"https://api.github.com/repos/{organization}/{pipeline_name}/issues?state=all"
        response = requests.get(issues_url, headers=headers)
        issues = response.json()

        for issue in issues:
            is_pr = "pull_request" in issue

            created_at = issue["created_at"]
            closed_at = issue["closed_at"]
            closed_wait = None

            if closed_at:
                created_timestamp = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                closed_timestamp = datetime.strptime(closed_at, "%Y-%m-%dT%H:%M:%SZ")
                closed_wait = (closed_timestamp - created_timestamp).total_seconds()

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


if __name__ == "__main__":
    # Initialize the pipeline with DuckDB destination
    pipeline = dlt.pipeline(
        pipeline_name="github",
        destination="motherduck",
        dataset_name="github",
        # Add schema evolution settings to handle existing tables
        destination_options={
            "schema_evolution": {
                "add_missing_columns": True,
                "drop_extra_columns": False,
            }
        },
    )

    # Run the pipeline
    load_info = pipeline.run(github_source())

    print(load_info)
