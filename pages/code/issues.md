---
title: Issues
sidebar_position: 3
---

# GitHub Issues

GitHub issues can be created to log feature requests, bug reports or questions.

```sql issues_over_time
select timestamp, -closed_merged as "Closed", open as "Open"
from nfcore_db.issues_and_prs_over_time
where type = 'issue'
```

<LineChart
  data={issues_over_time}
  x=timestamp
  y={["Closed", "Open"]}
  title="GitHub Issues over time"
  yAxisTitle="Number of Issues"
/>

## Issue Response Times

A sign of an active community is a quick response time to issues. Here we see a frequency histogram of how long it takes to respond to and close issues.

The histogram below shows the distribution of response times split between pipeline repositories and core infrastructure repositories. Pipeline repos are those listed in the nf-core pipelines registry, while core repos include tools, website, and other infrastructure. This comparison helps identify if there are different response patterns between the scientific pipelines and the supporting infrastructure.

```sql issues_response_time
select *
from nfcore_db.response_times
where type = 'issue'
```

<BarChart
data={issues_response_time}
x=label
y={["pipeline_time_to_close", "core_time_to_close"]}
sort=false
type=grouped
title="GitHub Issue Response Time by Repository Type"
subtitle="Distribution of close times for pipeline repos vs core infrastructure repos"
yAxisTitle="Percentage of Issues"
yFmt=pct
xType="category"
xGridLines=true
xLabelWrap=true
legendPosition="bottom"
/>
