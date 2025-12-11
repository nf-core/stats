## Architecture Overview

The nf-core stats page follows a multi-stage data pipeline architecture:

### 1. **Data Collection Layer (DLT)**

- Uses DLT (Data Load Tool) to perform ETL operations
- Collects data from multiple sources:
  - **GitHub**: Repository traffic stats, contributor statistics, issues/PRs, organization members
  - **Slack**: Workspace statistics (total/active/inactive users)
- Implements incremental loading with merge strategies for efficient updates

### 2. **Storage Layer (MotherDuck)**

- All collected data is stored in MotherDuck (a cloud-native DuckDB service)
- Database structure:
  - `github` schema: traffic_stats, contributor_stats, issue_stats, org_members
  - `slack` schema: workspace_stats
  - `twitter` schema: account_stats
- Could alternatively use local DuckDB or even CSV files

### 3. **Analytics Layer (Evidence)**

- Evidence framework queries MotherDuck at build time
- SQL queries aggregate and transform the data for visualization
- Examples include:
  - Pipeline metrics (views, clones over time)
  - Community statistics (contributors, members, followers)
  - Code overview metrics

### 4. **Static Site Generation**

- Evidence builds a static website from the query results
- The generated site runs entirely in-memory in the browser
- **No runtime connection to MotherDuck** - all data is embedded at build time
- Provides interactive visualizations without backend dependencies

This architecture enables a scalable, cost-effective solution that updates periodically via scheduled DLT runs while serving a fast, static frontend to users.
