# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the nf-core stats dashboard project. It consists of two main components:

1. **Evidence.dev frontend** - A data visualization dashboard for nf-core statistics
2. **DLT data pipelines** - Python pipelines that collect data from GitHub, Slack, and Twitter APIs

## Build Commands

### Frontend (Evidence.dev)

```bash
npm install          # Install dependencies
npm run sources      # Refresh data sources
npm run dev          # Start development server
npm run build        # Build for production
npm run test         # Run tests (builds the project)
```

### Data Pipelines (Python/DLT)

```bash
cd pipeline
uv run python github_pipeline.py  # Run GitHub stats collection
uv run python slack_pipeline.py   # Run Slack stats collection
```

## Architecture

### Data Flow

1. **Data Collection**: Python DLT pipelines (`pipeline/`) fetch data from external APIs (GitHub, Slack)
2. **Data Storage**: Data is stored in MotherDuck (cloud DuckDB) database `nf_core_stats_bot`
3. **Data Visualization**: Evidence.dev reads from MotherDuck and renders interactive dashboards

### Key Directories

- `pipeline/` - DLT data pipelines for collecting stats
- `pages/` - Evidence.dev markdown pages with SQL queries and visualizations
- `sources/` - Database connection configurations
- `.github/workflows/` - GitHub Actions for daily pipeline runs and Netlify builds

### Database Schema

The MotherDuck database contains tables for:

- `github_traffic_stats` - Repository views and clones
- `github_contributor_stats` - Contributor activity by week
- `github_issue_stats` - Issues and pull requests
- `slack_messages` - Slack channel message counts
- `slack_members` - Slack member statistics

### Environment Variables

Required secrets for pipelines (set in GitHub Actions or local `.env`):

- `SOURCES__GITHUB_PIPELINE__GITHUB__API_TOKEN` - GitHub personal access token
- `SOURCES__SLACK_PIPELINE__SLACK__API_TOKEN` - Slack user token
- `DESTINATION__MOTHERDUCK__CREDENTIALS__DATABASE` - MotherDuck database name
- `DESTINATION__MOTHERDUCK__CREDENTIALS__PASSWORD` - MotherDuck token

## Development Notes

- Evidence pages use SQL queries embedded in markdown to fetch data
- The GitHub pipeline uses incremental loading with merge strategy to update existing records
- Pipelines run daily via GitHub Actions and are monitored with runitor
- The frontend is deployed to Netlify and rebuilt daily after pipeline runs
