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


def main():
    """Load pipeline statistics from MotherDuck and save to JSON file."""
    # Get MotherDuck token from environment
    token = os.getenv("MOTHERDUCK_TOKEN")
    if not token:
        raise ValueError("MOTHERDUCK_TOKEN environment variable not set")

    # Connect to MotherDuck
    with duckdb.connect(f"md:?motherduck_token={token}") as conn:
        pipeline_stats = get_pipeline_stats(conn)

    pipelines = pipeline_stats.keys()

    data_obj = {
        pipeline: {"pipeline_stats": pipeline_stats[pipeline]} for pipeline in pipelines
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
