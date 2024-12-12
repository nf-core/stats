---
title: Pull Requests
sidebar_position: 2
---

When people contribute code to a nf-core repository, we conduct a "Pull request" - other members of the nf-core community review the proposed code and make suggestions, before merging into the main repository.

## Pull Requests Over Time

<!-- TODO: Live data https://github.com/nf-core/stats/issues/7 -->

```sql pull_requests_over_time
select
  date as timestamp,
  closed_merged as "Closed / Merged",
  open
from stats_static.github_prs
```

<AreaChart
  data={pull_requests_over_time}
  x=timestamp
  y={["Closed / Merged", "open"]}
  title="GitHub Pull Requests over time"
  yAxisTitle="Number of Pull Requests"
/>

## Pull Request Response Times

Pull-requests are reviewed by the nf-core community - they can contain discussion on the code and can be merged and closed. We aim to be prompt with reviews and merging. Note that some PRs can be a simple type and so very fast to merge, others can be major pipeline updates.

<!-- TODO: Live data https://github.com/nf-core/stats/issues/7 -->

```sql pr_response_times
select
  label,
  time_to_close as value,
  'Time to merge/close' as category
from stats_static.github_pr_response_time

union all

select
  label,
  time_to_first_response as value,
  'Time to First Response' as category
from stats_static.github_pr_response_time
```

<BarChart
data={pr_response_times}
x=label
y=value
swapXY=true
series=category
sort=false
type=grouped
title="GitHub Pull Request Response Time"
subtitle="First response is when a comment is made by a GitHub user other than the original PR author"
yAxisTitle="Percentage of PRs"
yFmt=pct
xType="category"
xGridLines=true
xLabelRotation={45}
legendPosition="bottom"
/>

<LastRefreshed prefix="Data last updated"/>