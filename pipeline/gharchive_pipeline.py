import dlt
from dlt.sources.sql_database import sql_table
import pendulum
from typing import Iterator, Dict, List
from collections import defaultdict
import os


def process_events_for_stats(events: List[Dict]) -> Dict:
    """Process a batch of events to calculate statistics."""
    stats = {
        "repo_metrics": defaultdict(
            lambda: {
                "stars": 0,
                "forks": 0,
                "watchers": 0,
            }
        ),
        "traffic": defaultdict(
            lambda: {
                "views": defaultdict(int),
                "clones": defaultdict(int),
                "unique_views": defaultdict(int),
                "unique_clones": defaultdict(int),
            }
        ),
        "contributors": defaultdict(
            lambda: {
                "commits": 0,
                "additions": 0,
                "deletions": 0,
                "first_contribution": None,
            }
        ),
        "issues": {
            "total": 0,
            "open": 0,
            "closed": 0,
            "response_times": [],
            "close_times": [],
            "daily_opened": defaultdict(int),
            "daily_closed": defaultdict(int),
        },
        "pull_requests": {
            "total": 0,
            "open": 0,
            "closed": 0,
            "response_times": [],
            "close_times": [],
            "daily_opened": defaultdict(int),
            "daily_closed": defaultdict(int),
        },
    }

    for event in events:
        repo_name = event.get("repo", {}).get("name", "").split("/")[-1]
        event_type = event.get("type")

        # Process different event types
        if event_type == "WatchEvent":
            stats["repo_metrics"][repo_name]["stars"] += 1
        elif event_type == "ForkEvent":
            stats["repo_metrics"][repo_name]["forks"] += 1
        elif event_type == "PushEvent":
            author = event.get("actor", {}).get("login")
            if author:
                stats["contributors"][author]["commits"] += len(
                    event.get("payload", {}).get("commits", [])
                )
                for commit in event.get("payload", {}).get("commits", []):
                    stats["contributors"][author]["additions"] += commit.get(
                        "stats", {}
                    ).get("additions", 0)
                    stats["contributors"][author]["deletions"] += commit.get(
                        "stats", {}
                    ).get("deletions", 0)
        elif event_type == "IssuesEvent":
            action = event.get("payload", {}).get("action")
            issue = event.get("payload", {}).get("issue", {})
            is_pr = "pull_request" in issue

            stats_key = "pull_requests" if is_pr else "issues"
            stats[stats_key]["total"] += 1

            if action == "opened":
                stats[stats_key]["open"] += 1
                created_date = pendulum.parse(issue.get("created_at")).format(
                    "YYYY-MM-DD"
                )
                stats[stats_key]["daily_opened"][created_date] += 1
            elif action == "closed":
                stats[stats_key]["closed"] += 1
                closed_date = pendulum.parse(event.get("created_at")).format(
                    "YYYY-MM-DD"
                )
                stats[stats_key]["daily_closed"][closed_date] += 1

                # Calculate close time
                if issue.get("created_at"):
                    created_time = pendulum.parse(issue["created_at"])
                    closed_time = pendulum.parse(event.get("created_at"))
                    close_time = (closed_time - created_time).total_seconds()
                    stats[stats_key]["close_times"].append(close_time)

        elif event_type == "IssueCommentEvent":
            issue = event.get("payload", {}).get("issue", {})
            is_pr = "pull_request" in issue
            stats_key = "pull_requests" if is_pr else "issues"

            # Calculate response time for first comment
            if issue.get("created_at") and event.get("created_at"):
                created_time = pendulum.parse(issue["created_at"])
                comment_time = pendulum.parse(event.get("created_at"))
                response_time = (comment_time - created_time).total_seconds()
                stats[stats_key]["response_times"].append(response_time)

    return stats


@dlt.source
def gharchive_source(start_date: str = "2024-01-01", end_date: str = None):
    """
    Load GitHub events for nf-core organization from GH Archive BigQuery dataset.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (defaults to current date)
    """
    if end_date is None:
        end_date = pendulum.now().format("YYYY-MM-DD")

    # Get BigQuery credentials path from environment
    # credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    # if not credentials_path:
    #     raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable must be set")

    # Construct BigQuery connection string for ConnectorX
    conn = f"bigquery://{credentials_path}"

    @dlt.resource(write_disposition="append", name="raw_events")
    def events(
        start_date: str = start_date, end_date: str = end_date
    ) -> Iterator[Dict]:
        """Query GitHub events from BigQuery."""
        query = f"""
        SELECT *
        FROM `githubarchive.day.*`
        WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', DATE('{start_date}'))
                          AND FORMAT_DATE('%Y%m%d', DATE('{end_date}'))
        AND JSON_EXTRACT_SCALAR(payload, '$.organization.login') = 'nf-core'
        """

        # Create sql_table with ConnectorX backend
        table = sql_table(
            conn,  # BigQuery connection string
            query=query,
            chunk_size=100000,  # Process in chunks for better memory usage
            backend="connectorx",  # Use ConnectorX backend for better performance
            reflection_level="full_with_precision",  # Get exact data types
            backend_kwargs={"return_type": "arrow"},  # Use Arrow for better performance
        )
        yield from table

    @dlt.resource(write_disposition="merge", primary_key="date", name="daily_stats")
    def daily_statistics(
        start_date: str = start_date, end_date: str = end_date
    ) -> Iterator[Dict]:
        """Calculate daily statistics from BigQuery events."""
        start = pendulum.parse(start_date)
        end = pendulum.parse(end_date)
        current = start

        while current <= end:
            query = f"""
            SELECT *
            FROM `githubarchive.day.{current.format("YYYYMMDD")}`
            WHERE JSON_EXTRACT_SCALAR(payload, '$.organization.login') = 'nf-core'
            """

            # Create sql_table with ConnectorX backend
            table = sql_table(
                conn,
                query=query,
                chunk_size=100000,
                backend="connectorx",
                reflection_level="full_with_precision",
                backend_kwargs={"return_type": "arrow"},
            )
            daily_events = list(table)

            if daily_events:
                stats = process_events_for_stats(daily_events)
                yield {"date": current.format("YYYY-MM-DD"), "stats": stats}

            current = current.add(days=1)

    return events, daily_statistics


if __name__ == "__main__":
    # Initialize the pipeline
    pipeline = dlt.pipeline(
        pipeline_name="gharchive",
        destination="duckdb",
        dataset_name="github_events",
        progress="log",  # Add progress logging
        dev_mode=True,  # Enable dev mode for better debugging
    )

    # Run the pipeline for 2024 data
    load_info = pipeline.run(
        gharchive_source(
            start_date="2024-01-01", end_date=pendulum.now().format("YYYY-MM-DD")
        ),
        loader_file_format="parquet",  # Use parquet for better performance
    )

    print(load_info)
