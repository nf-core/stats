# nf-core Stats DLT Pipeline

This directory contains a DLT (Data Load Tool) pipeline that replaces the old PHP scripts for collecting GitHub statistics for nf-core repositories.

## Features

The pipeline will:

1. Collect all statistics from the nf-core organization
2. Store the data in a DuckDB database
3. Use merge strategy to handle incremental updates
4. Automatically handle rate limiting with retries and fail-fast when exhausted
5. Process resources in order from least to most API-intensive

## Setup

All dependencies are declared in `pyproject.toml` and `uv.lock`.
To setup the virtual environment, execute

```bash
uv sync
```

in the `pipeline` directory.

## Configuration

The pipeline relies on the following environment variables for retrieving secrets and
configuration. These are "magic" environment variables that are interpreted by `dlt` to
set its configuration. You could also use a `secrets.toml` file instead. For more details,
refor to the [credentials](https://dlthub.com/docs/general-usage/credentials/setup) page.

```bash
# github token
# requires `repo`, `public_repo`, and `read:org` permissions
SOURCES__GITHUB_PIPELINE__GITHUB__API_TOKEN
SOURCES__SLACK_PIPELINE__SLACK__API_TOKEN                             # slack token

# For motherduck destination
DESTINATION__MOTHERDUCK__CREDENTIALS__DATABASE="nf_core_stats_bot"    # motherduck database name
DESTINATION__MOTHERDUCK__CREDENTIALS__PASSWORD                        # motherduck token

# Alternatively, use a local duckdb database for development
DESTINATION__DUCKDB__CREDENTIALS="./nf_core_stats.duckdb"
```

`dotenv` can retrieve them from 1password automatically, see `.envrc` for more details. If you
are not using `dotenv`, you need to set these env vars manually.

## Usage

The data loading pipeline is executed on github actions, triggered by a nightly cronjob.
See `.github/workflows/run_pipelines.yml` for more details.

To manually run the pipeline in development mode, run the pipelines with `uv`. The pipelines
are organized as subcommands of the `nf_core_stats` binary:

```bash
uv run nf_core_stats --help
```

For example, you can run

```bash
uv run nf_core_stats github --destination duckdb
```

For the `github` pipeline, it is possible to only fetch selected resources for testing purposes via the `--resources`
flag. For the full command line interface, run

```bash
uv run nf_core_stats github --help
```

## Database Structure

### Database Hierarchy

1. **Database**: The highest level container that holds all your data. Think of it as a complete application's worth of data.

2. **Schema**: A logical grouping of tables within a database. Like folders to organize your tables.

3. **Table**: The actual structure that holds your data in rows and columns.

### Recommended Structure

```console
Database: nf_core_stats
│
├── Schema: github
│   ├── Table: traffic_stats
│   │   └── (views, clones, timestamps per pipeline)
│   ├── Table: contributor_stats
│   │   └── (commits, additions, deletions per author/week)
│   └── Table: issue_stats
│       └── (issues and PRs details)
│
├── Schema: slack
│   └── Table: workspace_stats
│       └── (user counts, activity metrics)
│
└── Schema: twitter
    └── Table: account_stats
        └── (historical account metrics)
```

### Why this structure?

1. **Single Database**: Yes, keep everything in one database (`nf_core_stats_bot`) as it's all related to nf-core statistics.

2. **Separate Schemas**: Using different schemas for each data source (GitHub, Slack, etc.) is good practice because:
   - Provides logical separation of concerns
   - Makes permissions management easier
   - Helps avoid naming conflicts
   - Makes it clear where data comes from

3. **Clear Table Names**: Each table has a specific purpose and the hierarchy makes it obvious where to find data.

## Data Schema

### Traffic Stats

- `pipeline_name`: Repository name
- `timestamp`: Time of the stat collection
- `views`: Number of views
- `views_uniques`: Number of unique viewers
- `clones`: Number of clones
- `clones_uniques`: Number of unique cloners

**Note**: Traffic stats are optimized to reduce API burden by only collecting data for:

- Repositories updated in the last 6 months (non-archived)
- Top repositories by star count (configurable limit, default 50)

### Contributor Stats

- `pipeline_name`: Repository name
- `author`: GitHub username of contributor
- `avatar_url`: URL to contributor's avatar
- `week_date`: Week of contribution (YYYY-MM-DD format)
- `week_additions`: Lines added that week
- `week_deletions`: Lines deleted that week
- `week_commits`: Number of commits that week
- `week_approvals`: Number of approvals that week (currently 0)

### Issue Stats

- `pipeline_name`: Repository name
- `issue_number`: Issue or PR number
- `issue_type`: Either "issue" or "pr"
- `state`: Issue state (open/closed)
- `created_by`: Username of creator
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp
- `closed_at`: Closing timestamp (null if still open)
- `closed_wait_seconds`: Time to close in seconds (null if still open)
- `first_response_seconds`: Time to first response from someone other than creator
- `first_responder`: Username of first responder
- `num_comments`: Number of comments
- `html_url`: Link to issue/PR

**Note**: Comment fetching is incremental and only occurs when:

- Rate limit allows (>500 requests remaining)
- Issue has new or changed comments since last run

### Organization Members

- `timestamp`: Time of collection
- `num_members`: Number of organization members

### Commit Stats

- `pipeline_name`: Repository name
- `timestamp`: Week start timestamp
- `number_of_commits`: Number of commits in that week

### Pipeline Information (nfcore_pipelines)

- `name`: Repository name
- `description`: Repository description
- `gh_created_at`: GitHub creation timestamp
- `gh_updated_at`: GitHub last update timestamp
- `gh_pushed_at`: GitHub last push timestamp
- `stargazers_count`: Number of stars
- `watchers_count`: Number of watchers
- `forks_count`: Number of forks
- `open_issues_count`: Number of open issues
- `topics`: List of repository topics
- `default_branch`: Default branch name
- `archived`: Whether repository is archived
- `last_release_date`: Date of latest release (null if no releases)
- `category`: "pipeline" for nf-core pipelines, "core" for other repositories
