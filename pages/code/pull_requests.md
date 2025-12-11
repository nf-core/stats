---
title: Pull Requests
sidebar_position: 2
---

When people contribute code to a nf-core repository, we conduct a "Pull request" - other members of the nf-core community review the proposed code and make suggestions, before merging into the main repository.

## Pull Requests Over Time

```sql pull_requests_over_time
select timestamp, -closed_merged as "Closed / Merged", open as "Open"
from nfcore_db.issues_and_prs_over_time
where type = 'pr'
```

<LineChart
  data={pull_requests_over_time}
  x=timestamp
  y={["Closed / Merged", "Open"]}
  title="GitHub Pull Requests over time"
  yAxisTitle="Number of Pull Requests"
/>

## Pull Request Response Times

Pull-requests are reviewed by the nf-core community - they can contain discussion on the code and can be merged and closed. We aim to be prompt with reviews and merging. Note that some PRs can be a simple type and so very fast to merge, others can be major pipeline updates.

The histogram below shows the distribution of response times split between pipeline repositories and core infrastructure repositories. Pipeline repos are those listed in the nf-core pipelines registry, while core repos include tools, website, and other infrastructure. This comparison helps identify if there are different response patterns between the scientific pipelines and the supporting infrastructure.

```sql pr_response_times
select *
from nfcore_db.response_times
where type = 'pr'
```

<BarChart
data={pr_response_times}
x=label
y={["pipeline_time_to_close", "core_time_to_close"]}
sort=false
type=grouped
title="GitHub Pull Request Response Time by Repository Type"
subtitle="Distribution of close times for pipeline repos vs core infrastructure repos"
yAxisTitle="Percentage of PRs"
yFmt=pct
xType="category"
xGridLines=true
xLabelWrap=true
legendPosition="bottom"
/>

<LastRefreshed prefix="Data last updated"/>