import logging
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from typing import Literal

import dlt
import requests

from ._github import check_rate_limit, get_github_headers, get_paginated_data, github_request

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
        # dlt.resource(
        #     traffic_stats(organization, headers, repos, only_active_repos=True, max_repos=30), name="traffic_stats"
        # ),
        # dlt.resource(contributor_stats(organization, headers, repos), name="contributor_stats"),
        # dlt.resource(issue_stats(organization, headers, repos), name="issue_stats"),
        # dlt.resource(org_members(organization, headers), name="org_members"),
        # dlt.resource(commit_stats(organization, headers, repos), name="commit_stats"),
        # dlt.resource(pipelines(organization, headers, repos), name="nfcore_pipelines"),
        dlt.resource(modules_container_conversion(headers), name="modules_container_conversion"),
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
        six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
        filtered_repos = [
            repo
            for repo in repos
            if datetime.strptime(repo["updated_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) > six_months_ago
            and not repo["archived"]
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
def issue_stats(organization: str, headers: dict, repos: list[dict]) -> Iterator[dict]:
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
        issues_url = f"https://api.github.com/repos/{organization}/{name}/issues?state=all"

        try:
            issues = get_paginated_data(issues_url, headers)
            if not isinstance(issues, list):
                continue
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


@dlt.resource(write_disposition="merge", primary_key=["timestamp"])
def org_members(organization: str, headers: dict) -> Iterator[dict]:
    """Collect organization member count"""
    logger.info(f"Collecting organization member count for {organization}")
    members_url = f"https://api.github.com/orgs/{organization}/members"

    members = get_paginated_data(members_url, headers)
    logger.info(f"Found {len(members)} members in {organization}")
    yield {"timestamp": datetime.now(timezone.utc).timestamp(), "num_members": len(members)}


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
        release_url = f"https://api.github.com/repos/{organization}/{pipeline_name}/releases"
        try:
            releases = get_paginated_data(release_url, headers)
            number_of_releases = len(releases)
            if number_of_releases:
                # releases are sorted by date, starting with the most recent one
                last_release_date = releases[0].get("published_at")
            else:
                logger.info(f"No releases found for {pipeline_name} (this is expected for new repositories)")
                last_release_date = None
        except requests.RequestException as e:
            logger.warning(f"Failed to get latest release for {pipeline_name}: {e}")
            last_release_date = None
            number_of_releases = None

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

            commit_time = datetime.strptime(commit_date, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            week_start = commit_time - timedelta(days=commit_time.weekday())
            week_timestamp = int(week_start.timestamp())

            commit_counts[week_timestamp] = commit_counts.get(week_timestamp, 0) + 1

        for timestamp, commit_count in commit_counts.items():
            yield {
                "pipeline_name": name,
                "timestamp": timestamp,
                "number_of_commits": commit_count,
            }


@dlt.resource(write_disposition="append", primary_key=["timestamp"])
def modules_container_conversion(headers: dict) -> Iterator[dict]:
    """Track nf-core/modules containing 'linux_amd64' in meta.yml files, to track new container syntax.    """
    logger.info("Scanning nf-core/modules for linux_amd64 usage in meta.yml")

    try:
        # Use GitHub Tree API to get all files (only 1 API call)
        tree_url = "https://api.github.com/repos/nf-core/modules/git/trees/master?recursive=1"
        logger.info("Fetching repository tree from GitHub API")
        response = github_request(tree_url, headers)
        tree_data = response.json()

        # Filter to only meta.yml files in modules/nf-core/ directory
        meta_yml_files = [
            item for item in tree_data.get("tree", [])
            if item.get("path", "").startswith("modules/nf-core/")
            and item.get("path", "").endswith("meta.yml")
            and item.get("type") == "blob"
        ]

        total_modules = len(meta_yml_files)
        logger.info(f"Found {total_modules} meta.yml files in modules/nf-core/")

        # Now search for "linux_amd64" pattern in these specific files using Code Search
        # This is much more efficient than searching all yml files
        logger.info("Searching for linux_amd64 pattern in meta.yml files")
        container_query = 'repo:nf-core/modules "linux_amd64" extension:yml path:modules/nf-core'
        search_url = f"https://api.github.com/search/code?q={requests.utils.quote(container_query)}&per_page=100"

        container_results = []
        url = search_url
        while url:
            response = github_request(url, headers)
            data = response.json()
            items = data.get("items", [])
            container_results.extend(items)

            if "next" in response.links:
                url = response.links["next"]["url"]
            else:
                url = None

        # Filter to only meta.yml files
        filtered_container = [
            r for r in container_results
            if r.get("path", "").endswith("meta.yml")
        ]
        total_with_pattern = len(filtered_container)

        logger.info(f"Total meta.yml files with linux_amd64: {total_with_pattern}/{total_modules}")

        # Search for "topics:" with "versions:" pattern in meta.yml files
        logger.info("Searching for topics: versions: pattern in meta.yml files")
        topics_query = 'repo:nf-core/modules "topics:" "versions:" extension:yml path:modules/nf-core'
        topics_search_url = f"https://api.github.com/search/code?q={requests.utils.quote(topics_query)}&per_page=100"

        topics_results = []
        url = topics_search_url
        while url:
            response = github_request(url, headers)
            data = response.json()
            items = data.get("items", [])
            topics_results.extend(items)

            if "next" in response.links:
                url = response.links["next"]["url"]
            else:
                url = None

        # Filter to only meta.yml files
        filtered_topics = [
            r for r in topics_results
            if r.get("path", "").endswith("meta.yml")
        ]
        total_with_topics_version = len(filtered_topics)

        logger.info(f"Total meta.yml files with topics: versions: {total_with_topics_version}/{total_modules}")

        # Search for "community.wave.seqera.io/library/" pattern in main.nf files
        logger.info("Searching for community.wave.seqera.io/library/ pattern in main.nf files")
        wave_query = 'repo:nf-core/modules "community.wave.seqera.io/library/" path:modules/nf-core'
        wave_search_url = f"https://api.github.com/search/code?q={requests.utils.quote(wave_query)}&per_page=100"

        wave_results = []
        url = wave_search_url
        while url:
            response = github_request(url, headers)
            data = response.json()
            items = data.get("items", [])
            wave_results.extend(items)

            if "next" in response.links:
                url = response.links["next"]["url"]
            else:
                url = None

        # Filter to only main.nf files
        filtered_wave = [
            r for r in wave_results
            if r.get("path", "").endswith("main.nf")
        ]
        total_with_wave = len(filtered_wave)

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
        f"modules container conversion: {total_with_pattern}/{total_modules} modules use linux_amd64. \n modules container conversion: data collected"
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
        ]
    ]
    | None = None,
    traffic_only_active_repos: bool = True,
    traffic_max_repos: int | None = 50,
):
    """
    Run the github data ingestion pipeline

    Args:
        destination: dlt backend. Use 'motherduck' for production. Can use 'duckdb' for local testing
        resources: Resources to run. If None, run all resources.
        traffic_only_active_repos:
            Only collect traffic for repos updated in last 6 months.
            Traffic stats optimization settings to reduce API burden.
            This reduces API calls from ~100+ repos to ~30 most important active repos.
        traffic_max_repos: Limit to top N repos by stars (None for all)
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

    # Define resources to run (ordered by API call intensity - least to most)
    all_resources = [
        ("org_members", lambda: org_members(organization, headers)),
        ("modules_container_conversion", lambda: modules_container_conversion(headers)),
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

    for resource_name, resource_func in resources_to_run:
        try:
            logger.info(f"Processing resource: {resource_name}")

            # Check rate limit before processing resource
            rate_status = check_rate_limit(headers, min_remaining=100)
            if rate_status["remaining"] < 100:
                logger.warning(f"Low rate limit before {resource_name}. Stopping pipeline to resume on next run.")
                break

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

        except requests.HTTPError as e:
            if "rate limit" in str(e).lower():
                logger.error(f"❌ Rate limit hit during {resource_name}. Stopping pipeline.")
                break
            logger.error(f"❌ Failed to process {resource_name}: {e}")
            logger.info("Continuing with next resource...")
            continue
        except Exception as e:
            logger.error(f"❌ Failed to process {resource_name}: {e}")
            logger.info("Continuing with next resource...")
            continue

    logger.info("=== PIPELINE COMPLETION SUMMARY ===")
    logger.info(f"Total rows processed across all resources: {total_rows_processed}")
    logger.info("GitHub data pipeline completed!")
