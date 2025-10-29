import json
import os
from pathlib import Path

import duckdb


def main():
    """Load pipeline statistics from MotherDuck and save to JSON file."""
    # Get MotherDuck token from environment
    token = os.getenv("MOTHERDUCK_TOKEN")
    if not token:
        raise ValueError("MOTHERDUCK_TOKEN environment variable not set")

    # Connect to MotherDuck
    conn = duckdb.connect(f"md:?motherduck_token={token}")

    # Execute query
    query = """
    SELECT
        "name",
        description,
        gh_created_at,
        gh_updated_at,
        gh_pushed_at,
        stargazers_count,
        watchers_count,
        forks_count,
        open_issues_count,
        default_branch,
        archived,
        _dlt_load_id,
        _dlt_id,
        last_release_date,
        category
    FROM nf_core_stats_bot.github.nfcore_pipelines
    """

    result = conn.execute(query).fetchall()
    columns = [desc[0] for desc in conn.description]

    # Convert to list of dictionaries
    data = [dict(zip(columns, row)) for row in result]

    # Ensure data directory exists
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)

    # Write to JSON file
    output_file = data_dir / "stats.json"
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2, default=str)

    print(f"Successfully wrote {len(data)} records to {output_file}")

    conn.close()


if __name__ == "__main__":
    main()
