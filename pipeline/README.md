# nf-core Stats DLT Pipeline

This directory contains a DLT (Data Load Tool) pipeline that replaces the old PHP scripts for collecting GitHub statistics for nf-core repositories.

## Features

- Collects repository traffic statistics (views and clones)
- Gathers contributor statistics (commits, additions, deletions)
- Tracks issue and pull request metrics
- Uses DuckDB as the destination database
- Implements incremental loading with merge strategy

## Setup

All dependencies are declared in `pyproject.toml` and `uv.lock`. 
To setup the virtual environment, execute

```bash
uv sync
```

in the `pipeline` directory.

## Configuration

The pipeline relies on the following environment variables for retrieving secrets and
configuration: 

```bash
# github token
# requires `repo`, `public_repo`, and `read:org` permissions
SOURCES__GITHUB_PIPELINE__GITHUB__API_TOKEN                           
SOURCES__SLACK_PIPELINE__SLACK__API_TOKEN                             # slack token
DESTINATION__MOTHERDUCK__CREDENTIALS__DATABASE="nf_core_stats_bot"    # motherduck database name
DESTINATION__MOTHERDUCK__CREDENTIALS__PASSWORD                        # motherduck token
```

`dotenv` can retrieve them from 1password automatically, see `.envrc` for more details. If you 
are not using `dotenv`, you need to set these env vars manually.

## Usage

The data loading pipeline is executed on github actions, triggered by a nightly cronjob. 
See `.github/workflows/run_pipelines.yml` for more details. 

To manually run the pipeline in development mode, run the pipelines with `uv`

```bash
uv run github_stats.py
uv run slack_stats.py
```

The pipeline will:

1. Collect all statistics from the nf-core organization
2. Store the data in a DuckDB database
3. Use merge strategy to handle incremental updates
4. Automatically handle rate limiting with retries and fail-fast when exhausted
5. Process resources in order from least to most API-intensive

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
