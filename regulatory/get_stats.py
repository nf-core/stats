import json
import os
from pathlib import Path

import duckdb


def get_pipeline_stats(conn: duckdb.DuckDBPyConnection) -> dict:
    """Get stats from the nfcore_pipelines table"""
    # Execute query
    query = """
    SELECT
        "name",
        description,
        stargazers_count,
        watchers_count,
        forks_count,
        open_issues_count,
        archived,
        last_release_date,
        category
    FROM nf_core_stats_bot.github.nfcore_pipelines
    WHERE category == 'pipeline'
    """

    result = conn.execute(query).fetchall()
    columns = [desc[0] for desc in conn.description]
    # convert to list of dicts
    data = [dict(zip(columns, row)) for row in result]

    # organize by pipeline
    return {x["name"]: x for x in data}


def get_issue_stats(conn: duckdb.DuckDBPyConnection) -> dict:
    """Get stats related to issues/prs"""
    query = """
    SELECT
        COALESCE(i.pipeline_name, c.pipeline_name, p.pipeline_name, pc.pipeline_name) AS pipeline_name,
        i.issue_count,
        c.closed_issue_count,
        c.median_seconds_to_issue_closed,
        p.pr_count,
        pc.closed_pr_count,
        pc.median_seconds_to_pr_closed
    FROM (
        SELECT
            pipeline_name,
            COUNT(issue_number) AS issue_count
        FROM nf_core_stats_bot.github.issue_stats
        WHERE issue_type = 'issue'
        GROUP BY pipeline_name
    ) AS i
    FULL JOIN (
        SELECT
            pipeline_name,
            COUNT(issue_number) AS closed_issue_count,
            MEDIAN(closed_wait_seconds) as median_seconds_to_issue_closed
        FROM nf_core_stats_bot.github.issue_stats
        WHERE issue_type = 'issue' AND state = 'closed'
        GROUP BY pipeline_name
    ) AS c ON i.pipeline_name = c.pipeline_name
    FULL JOIN (
        SELECT
            pipeline_name,
            COUNT(issue_number) AS pr_count
        FROM nf_core_stats_bot.github.issue_stats
        WHERE issue_type = 'pr'
        GROUP BY pipeline_name
    ) AS p ON COALESCE(i.pipeline_name, c.pipeline_name) = p.pipeline_name
    FULL JOIN (
        SELECT
            pipeline_name,
            COUNT(issue_number) AS closed_pr_count,
            MEDIAN(closed_wait_seconds) as median_seconds_to_pr_closed
        FROM nf_core_stats_bot.github.issue_stats
        WHERE issue_type = 'pr' AND state = 'closed'
        GROUP BY pipeline_name
    ) AS pc ON COALESCE(i.pipeline_name, c.pipeline_name, p.pipeline_name) = pc.pipeline_name
    ORDER BY pipeline_name
    """

    result = conn.execute(query).fetchall()
    columns = [desc[0] for desc in conn.description]
    # convert to list of dicts
    data = [dict(zip(columns, row)) for row in result]

    # organize by pipeline
    return {x["pipeline_name"]: x for x in data}


def get_contributor_stats(conn: duckdb.DuckDBPyConnection) -> dict:
    """Get contributor statistics per pipeline"""
    query = """
    SELECT
        pipeline_name,
        COUNT(DISTINCT author) AS number_of_contributors
    FROM nf_core_stats_bot.github.contributor_stats
    GROUP BY pipeline_name
    """

    result = conn.execute(query).fetchall()
    columns = [desc[0] for desc in conn.description]
    # convert to list of dicts
    data = [dict(zip(columns, row)) for row in result]

    # organize by pipeline
    return {x["pipeline_name"]: x for x in data}


def main():
    """
    Load pipeline statistics from MotherDuck and save to JSON file.

    Outputs are organized as a dictionary by pipeline:

    ```
    {
        "rnaseq": {
            "pipeline_metrics": { ... },
            "issue_metrics": { ... },
            ...
        },
        "sarek": { ... }
    }
    """
    # Get MotherDuck token from environment
    token = os.getenv("MOTHERDUCK_TOKEN")
    if not token:
        raise ValueError("MOTHERDUCK_TOKEN environment variable not set")

    # Connect to MotherDuck
    with duckdb.connect(f"md:?motherduck_token={token}") as conn:
        pipeline_stats = get_pipeline_stats(conn)
        issue_stats = get_issue_stats(conn)
        contributor_stats = get_contributor_stats(conn)

    pipelines = pipeline_stats.keys()

    data_obj = {
        # it can happen that no metrics exist, e.g. if no issues are reported in new repos -> None/null in that case
        pipeline: {
            "pipeline_stats": pipeline_stats[pipeline],
            "issue_stats": issue_stats.get(pipeline, None),
            "contributor_stats": contributor_stats.get(pipeline, None),
        }
        for pipeline in pipelines
    }

    # Ensure data directory exists
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)

    # Write to JSON file
    output_file = data_dir / "stats.json"
    with open(output_file, "w") as f:
        json.dump(data_obj, f, indent=2, default=str)


if __name__ == "__main__":
    main()
