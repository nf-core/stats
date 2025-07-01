## Database Hierarchy

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
└── Schema: slack
│   └── Table: workspace_stats
│       └── (user counts, activity metrics)
```


### Why this structure?

1. **Single Database**: Yes, keep everything in one database (`nf_core_stats`) as it's all related to nf-core statistics.

2. **Separate Schemas**: Using different schemas for each data source (GitHub, Slack, etc.) is good practice because:

- Provides logical separation of concerns
- Makes permissions management easier
- Helps avoid naming conflicts
- Makes it clear where data comes from

3. **Clear Table Names**: Each table has a specific purpose and the hierarchy makes it obvious where to find data.