# nf-core Stats DLT Pipeline

This directory contains a DLT (Data Load Tool) pipeline that replaces the old PHP scripts for collecting GitHub statistics for nf-core repositories.

## Features

- Collects repository traffic statistics (views and clones)
- Gathers contributor statistics (commits, additions, deletions)
- Tracks issue and pull request metrics
- Uses DuckDB as the destination database
- Implements incremental loading with merge strategy

## Setup

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Unix/macOS
   # or
   .venv\Scripts\activate  # On Windows
   ```

2. Install dependencies using uv:

   ```bash
   uv pip install .
   ```

3. Set up your environment variables by creating a `.env` file:

```toml
[sources.github]
api_token = "<your_github_personal_access_token>"

[sources.slack_pipeline]
access_token = "<your_slack_token>"

[destination.motherduck.credentials]
database = "<your_motherduck_database_name>"
password = "<your_motherduck_password>"
```

Make sure your GitHub token has the following permissions:

- `repo` access for private repositories
- `public_repo` for public repositories
- `read:org` for organization access

## Usage

Run the pipeline:

```bash
python github_stats.py
```

The pipeline will:

1. Collect all statistics from the nf-core organization
2. Store the data in a DuckDB database
3. Use merge strategy to handle incremental updates

## Data Schema

### Traffic Stats

- `pipeline_name`: Repository name
- `timestamp`: Time of the stat collection
- `views`: Number of views
- `views_uniques`: Number of unique viewers
- `clones`: Number of clones
- `clones_uniques`: Number of unique cloners

### Contributor Stats

- `pipeline_name`: Repository name
- `author`: GitHub username of contributor
- `avatar_url`: URL to contributor's avatar
- `week_date`: Week of contribution
- `week_additions`: Lines added
- `week_deletions`: Lines deleted
- `week_commits`: Number of commits

### Issue Stats

- `pipeline_name`: Repository name
- `issue_number`: Issue or PR number
- `issue_type`: Either "issue" or "pr"
- `state`: Issue state (open/closed)
- `created_by`: Username of creator
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp
- `closed_at`: Closing timestamp
- `closed_wait_seconds`: Time to close
- `num_comments`: Number of comments
- `html_url`: Link to issue/PR
