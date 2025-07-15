import logging
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from typing import Any

import dlt
from dlt.sources import incremental
from dlt.sources.helpers import requests
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class GitHubGraphQLSource:
    """DLT-optimized GitHub GraphQL source with built-in pagination and error handling"""

    def __init__(self, token: str):
        self.token = token
        self.endpoint = "https://api.github.com/graphql"
        self.headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def graphql_request(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make GraphQL request using DLT's requests helper with built-in retry logic"""
        payload = {"query": query, "variables": variables or {}}

        # Use DLT's requests helper which includes retry logic and better error handling
        response = requests.post(self.endpoint, json=payload, headers=self.headers, timeout=30)

        result = response.json()

        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")

        return result["data"]


@dlt.source(name="github_graphql", max_table_nesting=2)
def github_graphql_source(
    organization: str = "nf-core",
    api_token: str = dlt.secrets["sources.github_pipeline.github.api_token"],
    max_repos_traffic: int = 200,
    only_active_repos: bool = False,
):
    """
    DLT-optimized GitHub data source using GraphQL with incremental loading

    Args:
        organization: GitHub organization name
        api_token: GitHub API token
        max_repos_traffic: Maximum number of repositories to collect traffic for
        only_active_repos: Only collect traffic for recently updated repositories
    """

    graphql_client = GitHubGraphQLSource(api_token)

    # Create REST headers for endpoints not available in GraphQL
    rest_headers = {"Authorization": f"token {api_token}", "Accept": "application/vnd.github.v3+json"}

    @dlt.resource(
        name="repositories",
        write_disposition="merge",
        primary_key="name",
        columns={"topics": {"data_type": "json"}, "repositoryTopics": {"data_type": "json"}},
    )
    def repositories(
        updated_at: incremental[datetime] = dlt.sources.incremental(
            "updated_at",
            initial_value=datetime(2018, 1, 1, tzinfo=timezone.utc),  # Start from 2018
            allow_external_schedulers=True,
        ),
    ) -> Iterator[dict[str, Any]]:
        """Get all organization repositories with releases using GraphQL pagination and incremental loading"""
        query = """
        query($org: String!, $cursor: String) {
          organization(login: $org) {
            repositories(first: 100, after: $cursor, orderBy: {field: UPDATED_AT, direction: DESC}) {
              pageInfo {
                hasNextPage
                endCursor
              }
              nodes {
                name
                description
                createdAt
                updatedAt
                pushedAt
                stargazerCount
                watchers {
                  totalCount
                }
                forkCount
                issues(states: OPEN) {
                  totalCount
                }
                repositoryTopics(first: 10) {
                  nodes {
                    topic {
                      name
                    }
                  }
                }
                defaultBranchRef {
                  name
                }
                isArchived
                releases(first: 1, orderBy: {field: CREATED_AT, direction: DESC}) {
                  nodes {
                    publishedAt
                    tagName
                  }
                }
              }
            }
          }
        }
        """

        cursor = None
        last_value = updated_at.last_value or datetime(2018, 1, 1, tzinfo=timezone.utc)
        logger.info(f"Last value: {last_value}")

        while True:
            variables = {"org": organization, "cursor": cursor}
            data = graphql_client.graphql_request(query, variables)

            repos = data["organization"]["repositories"]["nodes"]

            # Filter repos updated since last run for incremental loading
            filtered_repos = []
            for repo in repos:
                repo_updated = datetime.fromisoformat(repo["updatedAt"].replace("Z", "+00:00"))
                if repo_updated >= last_value:
                    filtered_repos.append(repo)
                    logger.info(f"Yielding repo: {repo['name']}")
                else:
                    # Since results are ordered by updated_at DESC, we can break early
                    break

            # Process and yield repositories
            for repo in filtered_repos:
                # Extract topics for easier querying
                topics = [topic["topic"]["name"] for topic in repo["repositoryTopics"]["nodes"]]

                # Get latest release
                latest_release = None
                if repo["releases"]["nodes"]:
                    latest_release = _safe_datetime_convert(repo["releases"]["nodes"][0]["publishedAt"])

                yield {
                    "name": repo["name"],
                    "description": repo["description"],
                    "created_at": _safe_datetime_convert(repo["createdAt"]),
                    "updated_at": _safe_datetime_convert(repo["updatedAt"]),
                    "pushed_at": _safe_datetime_convert(repo["pushedAt"]),
                    "stargazers_count": repo["stargazerCount"],
                    "watchers_count": repo["watchers"]["totalCount"],
                    "forks_count": repo["forkCount"],
                    "open_issues_count": repo["issues"]["totalCount"],
                    "topics": topics,
                    "repositoryTopics": repo["repositoryTopics"]["nodes"],  # Keep original for compatibility
                    "default_branch": repo["defaultBranchRef"]["name"] if repo["defaultBranchRef"] else "main",
                    "archived": repo["isArchived"],
                    "latest_release": latest_release,
                }

            # Check for next page
            page_info = data["organization"]["repositories"]["pageInfo"]
            if not page_info["hasNextPage"] or not filtered_repos:
                break
            cursor = page_info["endCursor"]

            logger.info(f"Fetched {len(filtered_repos)} updated repositories via GraphQL (page {cursor or 'first'})")

    # Materialize the list of updated repositories once to ensure all downstream
    # resources use the same data for the entire pipeline run. This prevents
    # the incremental state from being updated mid-run, which would cause
    # subsequent resources to receive a prematurely filtered list.
    updated_repositories_list = list(repositories())
    logger.info(f"Materialized {len(updated_repositories_list)} updated repositories for this run.")

    @dlt.resource(
        name="issue_stats",
        write_disposition="merge",
        primary_key=["pipeline_name", "issue_number"],
        columns={"labels": {"data_type": "json"}, "assignees": {"data_type": "json"}},
    )
    def issue_stats(
        updated_at: incremental[datetime] = dlt.sources.incremental(
            "updated_at", initial_value=datetime(2018, 1, 1, tzinfo=timezone.utc), allow_external_schedulers=True
        ),
    ) -> Iterator[dict[str, Any]]:
        """Get all issues and PRs using GraphQL with efficient pagination and incremental loading"""

        # Use the materialized list of updated repositories
        repo_names = [repo["name"] for repo in updated_repositories_list]

        if not repo_names:
            logger.info("No updated repositories found, skipping issue_stats collection")
            return

        # Query for issues (which includes PRs) with date filtering
        issues_query = """
        query($org: String!, $repo: String!, $cursor: String, $since: DateTime!) {
          repository(owner: $org, name: $repo) {
            issues(first: 100, after: $cursor, orderBy: {field: UPDATED_AT, direction: DESC}, filterBy: {since: $since}) {
              pageInfo { hasNextPage, endCursor }
              nodes {
                number
                title
                state
                createdAt
                updatedAt
                closedAt
                author { login }
                comments(first: 1) {
                  totalCount
                  nodes {
                    createdAt
                    author { login }
                  }
                }
                labels(first: 10) {
                  nodes { name }
                }
                assignees(first: 10) {
                  nodes { login }
                }
                url
              }
            }
          }
        }
        """

        last_value = updated_at.last_value or datetime(2018, 1, 1, tzinfo=timezone.utc)
        since_date = last_value.isoformat()

        for repo_name in repo_names:
            logger.info(f"Fetching updated issues and PRs for {repo_name}")

            # Get issues and PRs together
            cursor = None
            while True:
                variables = {"org": organization, "repo": repo_name, "cursor": cursor, "since": since_date}
                data = graphql_client.graphql_request(issues_query, variables)

                repo_data = data["repository"]

                # Process issues (which includes PRs) with incremental filtering
                for issue in repo_data["issues"]["nodes"]:
                    issue_updated = datetime.fromisoformat(issue["updatedAt"].replace("Z", "+00:00"))
                    if issue_updated > last_value:
                        item_type = "pr" if "/pull/" in issue["url"] else "issue"
                        yield _format_issue_data(issue, repo_name, item_type)

                # Check pagination
                page_info = repo_data["issues"]["pageInfo"]
                if not page_info["hasNextPage"]:
                    break

                cursor = page_info["endCursor"]

    @dlt.resource(
        name="org_members",
        write_disposition="merge",
        primary_key=["timestamp"],
    )
    def org_members() -> Iterator[dict[str, Any]]:
        """Get organization member count using GraphQL (always runs to track changes)"""
        query = """
        query($org: String!) {
          organization(login: $org) {
            membersWithRole {
              totalCount
            }
          }
        }
        """

        data = graphql_client.graphql_request(query, {"org": organization})
        member_count = data["organization"]["membersWithRole"]["totalCount"]

        yield {
            "timestamp": datetime.now(timezone.utc).timestamp(),
            "num_members": member_count,
        }

    @dlt.resource(name="traffic_stats", write_disposition="merge", primary_key=["pipeline_name", "timestamp"])
    def traffic_stats(
        timestamp: incremental[datetime] = dlt.sources.incremental(
            "timestamp",
            initial_value=datetime.now(timezone.utc) - timedelta(days=14),  # GitHub only keeps 14 days of traffic data
            allow_external_schedulers=True,
        ),
    ) -> Iterator[dict[str, Any]]:
        """Get traffic stats using REST API with incremental loading (only new data)"""

        # Use the materialized list of updated repositories
        repos_data = updated_repositories_list

        # Filter repositories if needed
        filtered_repos = repos_data

        if only_active_repos:
            six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
            filtered_repos = [
                repo for repo in repos_data if repo["updated_at"] > six_months_ago and not repo["archived"]
            ]
            logger.info(f"Filtered to {len(filtered_repos)} active repositories")

        # Sort by stars and limit
        filtered_repos = sorted(filtered_repos, key=lambda x: x["stargazers_count"], reverse=True)
        if max_repos_traffic:
            filtered_repos = filtered_repos[:max_repos_traffic]
            logger.info(f"Limited to top {max_repos_traffic} repositories")

        for repo in filtered_repos:
            repo_name = repo["name"]

            # Get traffic data using DLT's requests helper
            views_url = f"https://api.github.com/repos/{organization}/{repo_name}/traffic/views"
            clones_url = f"https://api.github.com/repos/{organization}/{repo_name}/traffic/clones"

            try:
                views_response = requests.get(views_url, headers=rest_headers)
                clones_response = requests.get(clones_url, headers=rest_headers)

                views_data = views_response.json()
                clones_data = clones_response.json()

                # Process traffic data
                views_list = views_data.get("views", [])
                clones_list = clones_data.get("clones", [])

                # Create lookup for clones
                clones_by_timestamp = {c["timestamp"]: c for c in clones_list}

                # Yield combined data
                for view in views_list:
                    view_timestamp_str = view["timestamp"]
                    clone_data = clones_by_timestamp.get(view_timestamp_str, {"count": 0, "uniques": 0})

                    yield {
                        "pipeline_name": repo_name,
                        "timestamp": _safe_datetime_convert(view_timestamp_str),
                        "views": view["count"],
                        "views_uniques": view["uniques"],
                        "clones": clone_data["count"],
                        "clones_uniques": clone_data["uniques"],
                    }

                # Handle clones without corresponding views
                for clone in clones_list:
                    clone_timestamp_str = clone["timestamp"]
                    if not any(view["timestamp"] == clone_timestamp_str for view in views_list):
                        yield {
                            "pipeline_name": repo_name,
                            "timestamp": _safe_datetime_convert(clone_timestamp_str),
                            "views": 0,
                            "views_uniques": 0,
                            "clones": clone["count"],
                            "clones_uniques": clone["uniques"],
                        }

            except Exception as e:
                logger.warning(f"Failed to get traffic data for {repo_name}: {e}")
                continue

    @dlt.resource(
        name="contributor_stats", write_disposition="merge", primary_key=["pipeline_name", "author", "week_date"]
    )
    def contributor_stats() -> Iterator[dict[str, Any]]:
        """Get contributor stats using REST API (only for updated repos to reduce API calls)"""

        # Use the materialized list of updated repositories
        repos_data = updated_repositories_list

        for repo in repos_data:
            repo_name = repo["name"]

            # Get contributor stats
            stats_url = f"https://api.github.com/repos/{organization}/{repo_name}/stats/contributors"

            try:
                response = requests.get(stats_url, headers=rest_headers)
                stats = response.json()

                if not isinstance(stats, list):
                    continue

                # Process contributor data
                for contributor in stats:
                    author = contributor["author"]["login"]
                    avatar_url = contributor["author"]["avatar_url"]

                    for week in contributor["weeks"]:
                        week_date = datetime.fromtimestamp(week["w"]).strftime("%Y-%m-%d")

                        # Only yield if there's actual activity (optimization)
                        if week["a"] > 0 or week["d"] > 0 or week["c"] > 0:
                            yield {
                                "pipeline_name": repo_name,
                                "author": author,
                                "avatar_url": avatar_url,
                                "week_date": week_date,
                                "week_additions": week["a"],
                                "week_deletions": week["d"],
                                "week_commits": week["c"],
                                "week_approvals": 0,
                            }

            except Exception as e:
                logger.warning(f"Failed to get contributor stats for {repo_name}: {e}")
                continue

    @dlt.resource(
        name="all_repositories",
        write_disposition="merge",
        primary_key="name",
        columns={"topics": {"data_type": "json"}, "repositoryTopics": {"data_type": "json"}},
    )
    def all_repositories() -> Iterator[dict[str, Any]]:
        """Get all organization repositories using GraphQL pagination (non-incremental)."""
        query = """
        query($org: String!, $cursor: String) {
          organization(login: $org) {
            repositories(first: 100, after: $cursor, orderBy: {field: UPDATED_AT, direction: DESC}) {
              pageInfo {
                hasNextPage
                endCursor
              }
              nodes {
                name
                description
                createdAt
                updatedAt
                pushedAt
                stargazerCount
                watchers {
                  totalCount
                }
                forkCount
                issues(states: OPEN) {
                  totalCount
                }
                repositoryTopics(first: 10) {
                  nodes {
                    topic {
                      name
                    }
                  }
                }
                defaultBranchRef {
                  name
                }
                isArchived
                releases(first: 1, orderBy: {field: CREATED_AT, direction: DESC}) {
                  nodes {
                    publishedAt
                    tagName
                  }
                }
              }
            }
          }
        }
        """

        cursor = None
        while True:
            variables = {"org": organization, "cursor": cursor}
            data = graphql_client.graphql_request(query, variables)
            repos = data["organization"]["repositories"]["nodes"]

            for repo in repos:
                topics = [topic["topic"]["name"] for topic in repo["repositoryTopics"]["nodes"]]
                latest_release = None
                if repo["releases"]["nodes"]:
                    latest_release = _safe_datetime_convert(repo["releases"]["nodes"][0]["publishedAt"])

                yield {
                    "name": repo["name"],
                    "description": repo["description"],
                    "created_at": _safe_datetime_convert(repo["createdAt"]),
                    "updated_at": _safe_datetime_convert(repo["updatedAt"]),
                    "pushed_at": _safe_datetime_convert(repo["pushedAt"]),
                    "stargazers_count": repo["stargazerCount"],
                    "watchers_count": repo["watchers"]["totalCount"],
                    "forks_count": repo["forkCount"],
                    "open_issues_count": repo["issues"]["totalCount"],
                    "topics": topics,
                    "repositoryTopics": repo["repositoryTopics"]["nodes"],
                    "default_branch": repo["defaultBranchRef"]["name"] if repo["defaultBranchRef"] else "main",
                    "archived": repo["isArchived"],
                    "latest_release": latest_release,
                }

            page_info = data["organization"]["repositories"]["pageInfo"]
            if not page_info["hasNextPage"]:
                break
            cursor = page_info["endCursor"]
            logger.info(f"Fetched a page of repositories via GraphQL (page {cursor or 'first'})")

    @dlt.resource(name="commit_stats", write_disposition="merge", primary_key=["pipeline_name", "timestamp"])
    def commit_stats() -> Iterator[dict[str, Any]]:
        """Get commit statistics over time using REST API (only for updated repos to reduce API calls)"""

        # Use the materialized list of updated repositories
        repos_data = updated_repositories_list

        for repo in repos_data:
            repo_name = repo["name"]

            # Get commit stats
            page_url = f"https://api.github.com/repos/{organization}/{repo_name}/commits"

            try:
                all_commits = []
                while page_url:
                    response = requests.get(page_url, headers=rest_headers)
                    commits = response.json()

                    if not isinstance(commits, list):
                        logger.warning(f"Unexpected response format when fetching commits for {repo_name}: {commits}")
                        break

                    all_commits.extend(commits)
                    page_url = response.links.get("next", {}).get("url")

                # Group commits by week
                commit_counts: dict[int, int] = {}
                for commit in all_commits:
                    commit_date = commit.get("commit", {}).get("author", {}).get("date")
                    if not commit_date:
                        continue

                    commit_time = _safe_datetime_convert(commit_date)
                    if not commit_time:
                        continue

                    week_start = commit_time - timedelta(days=commit_time.weekday())
                    week_timestamp = int(week_start.timestamp())

                    commit_counts[week_timestamp] = commit_counts.get(week_timestamp, 0) + 1

                for timestamp, commit_count in commit_counts.items():
                    yield {
                        "pipeline_name": repo_name,
                        "timestamp": timestamp,
                        "number_of_commits": commit_count,
                    }

            except Exception as e:
                logger.warning(f"Failed to get commit stats for {repo_name}: {e}")
                continue

    @dlt.resource(name="nfcore_pipelines", write_disposition="merge", primary_key=["name"])
    def nfcore_pipelines() -> Iterator[dict[str, Any]]:
        """Get pipeline information matching original structure"""

        # Get repository data
        repos_data = list(all_repositories())

        # Get pipeline names from nf-core website
        pipeline_names_url = "https://raw.githubusercontent.com/nf-core/website/main/public/pipeline_names.json"
        try:
            response = requests.get(pipeline_names_url, headers=rest_headers)
            pipeline_names = response.json()
        except Exception as e:
            logger.warning(f"Failed to get pipeline names from nf-core website: {e}")
            return

        for pipeline_name in pipeline_names.get("pipeline", []):
            pipeline = next((repo for repo in repos_data if repo["name"] == pipeline_name), None)
            if not pipeline:
                logger.warning(f"{pipeline_name} is not a pipeline")
                continue

            # Get latest release
            release_url = f"https://api.github.com/repos/{organization}/{pipeline_name}/releases/latest"
            try:
                release_response = requests.get(release_url, headers=rest_headers)
                release = release_response.json()
                last_release_date = release.get("published_at")
            except Exception as e:
                if "404" in str(e) or "Not Found" in str(e):
                    logger.info(f"No releases found for {pipeline_name}`")
                else:
                    logger.warning(f"Failed to get latest release for {pipeline_name}: {e}")
                last_release_date = None

            yield {
                "name": pipeline["name"],
                "description": pipeline["description"],
                "gh_created_at": pipeline["created_at"].isoformat() if pipeline["created_at"] else None,
                "gh_updated_at": pipeline["updated_at"].isoformat() if pipeline["updated_at"] else None,
                "gh_pushed_at": pipeline["pushed_at"].isoformat() if pipeline["pushed_at"] else None,
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
        for repo in repos_data:
            if repo["name"] not in pipeline_names.get("pipeline", []):
                yield {
                    "name": repo["name"],
                    "description": repo["description"],
                    "gh_created_at": repo["created_at"].isoformat() if repo["created_at"] else None,
                    "gh_updated_at": repo["updated_at"].isoformat() if repo["updated_at"] else None,
                    "gh_pushed_at": repo["pushed_at"].isoformat() if repo["pushed_at"] else None,
                    "stargazers_count": repo["stargazers_count"],
                    "watchers_count": repo["watchers_count"],
                    "forks_count": repo["forks_count"],
                    "open_issues_count": repo["open_issues_count"],
                    "topics": repo["topics"],
                    "default_branch": repo["default_branch"],
                    "archived": repo["archived"],
                    "category": "core",
                }

    return [repositories, issue_stats, org_members, traffic_stats, contributor_stats, commit_stats, nfcore_pipelines]


def _safe_datetime_convert(datetime_str: str | None) -> datetime | None:
    """Safely convert GitHub datetime string to datetime object"""
    if datetime_str is None:
        return None
    return datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))


def _format_issue_data(item: dict[str, Any], repo_name: str, item_type: str) -> dict[str, Any]:
    """Format issue/PR data with proper datetime handling"""
    created_at = _safe_datetime_convert(item["createdAt"])

    # Calculate close time
    closed_wait_seconds = None
    closed_at = _safe_datetime_convert(item["closedAt"])
    if closed_at and created_at:
        closed_wait_seconds = (closed_at - created_at).total_seconds()

    # Calculate first response time
    first_response_seconds = None
    first_responder = None

    if item["comments"]["nodes"]:
        first_comment = item["comments"]["nodes"][0]
        if first_comment["author"] and first_comment["author"]["login"] != (
            item["author"]["login"] if item["author"] else None
        ):
            comment_time = _safe_datetime_convert(first_comment["createdAt"])
            if comment_time and created_at:
                first_response_seconds = (comment_time - created_at).total_seconds()
                first_responder = first_comment["author"]["login"]

    # Extract labels and assignees
    labels = [label["name"] for label in item["labels"]["nodes"]]
    assignees = [assignee["login"] for assignee in item["assignees"]["nodes"]]

    return {
        "pipeline_name": repo_name,
        "issue_number": item["number"],
        "title": item["title"],
        "issue_type": item_type,
        "state": item["state"].lower(),
        "created_by": item["author"]["login"] if item["author"] else None,
        "created_at": created_at,
        "updated_at": _safe_datetime_convert(item["updatedAt"]),
        "closed_at": closed_at,
        "closed_wait_seconds": closed_wait_seconds,
        "first_response_seconds": first_response_seconds,
        "first_responder": first_responder,
        "num_comments": item["comments"]["totalCount"],
        "labels": labels,
        "assignees": assignees,
        "html_url": item["url"],
    }


if __name__ == "__main__":
    logger.info("Starting DLT-optimized GitHub GraphQL pipeline with incremental loading...")

    # Create pipeline
    pipeline = dlt.pipeline(pipeline_name="github_graphql_optimized", destination="motherduck", dataset_name="github")

    # Configuration
    organization = "nf-core"

    # Run pipeline with same resource selection as original
    source = github_graphql_source(organization=organization, max_repos_traffic=500, only_active_repos=False)

    # Select the same resources as the original pipeline (excluding repositories which is internal)
    load_info = pipeline.run(
        [
            source.traffic_stats,
            source.contributor_stats,
            source.issue_stats,
            source.org_members,
            source.commit_stats,
            source.nfcore_pipelines,
        ]
    )

    # Log results
    logger.info("=== PIPELINE COMPLETION SUMMARY ===")
    if pipeline.last_trace and pipeline.last_trace.last_normalize_info:
        row_counts = pipeline.last_trace.last_normalize_info.row_counts
        total_rows = sum(row_counts.values())
        logger.info(f"Total rows processed: {total_rows}")

        for table_name, count in row_counts.items():
            logger.info(f"  {table_name}: {count} rows")

    logger.info("DLT-optimized GitHub GraphQL pipeline with incremental loading completed!")
