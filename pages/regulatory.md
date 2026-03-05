---
title: Regulatory Stats
sidebar_position: 10
---

Pipeline statistics for regulatory and compliance reporting. This data is generated at build time from the nf-core statistics database and can be downloaded as a JSON export.

## Download

Download a JSON export of all pipeline statistics, including issue metrics and contributor data, for use in regulatory reports.

```sql pipeline_stats
SELECT * FROM nfcore_db.regulatory_pipeline_stats
```

```sql issue_stats
SELECT * FROM nfcore_db.regulatory_issue_stats
```

```sql contributor_stats
SELECT * FROM nfcore_db.regulatory_contributor_stats
```

<DownloadStatsJson
  pipelineStats={pipeline_stats}
  issueStats={issue_stats}
  contributorStats={contributor_stats}
/>

The exported JSON contains the following data per pipeline:

- **Pipeline stats** — name, description, stars, forks, open issues, archive status, last release date
- **Issue stats** — total/closed issue and PR counts, median time to close
- **Contributor stats** — number of unique contributors
