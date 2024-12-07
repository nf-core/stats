---
title: Issues
sidebar_position: 3
---

# GitHub Issues

GitHub issues can be created to log feature requests, bug reports or questions.

<!-- TODO: Live data https://github.com/nf-core/stats/issues/4 -->
<!-- FIXME Need to split the data again values aren't right-->

```sql issues_over_time
select
  date,
  'Closed' as status,
  closed as count
from stats_static.github_issues
union all
select
  date,
  'Open' as status,
  open as count
from stats_static.github_issues
order by date asc, status asc
```

<AreaChart
  data={issues_over_time}
  x=date
  y=count
  series=status
  seriesOrder={['Closed', 'Open']}
  title="GitHub Issues over time"
  yAxisTitle="Number of Issues"
  colorPalette={['#ff7675', '#85ea7d']}
/>

## Issue response times

A sign of an active community is a quick response time to issues. Here we see a frequency histogram of how long it takes to respond to and close issues.

<!-- TODO: Live data https://github.com/nf-core/stats/issues/5 -->

```sql issues_response_time
select
  label,
  time_to_close as value,
  'Time to close' as category
from stats_static.github_issue_response_time

union all

select
  label,
  time_to_first_response as value,
  'Time to First Response' as category
from stats_static.github_issue_response_time
```

<BarChart
  data={issues_response_time}
  x=label
  y=value
  swapXY=true
  series=category
  sort=false
  type=grouped
  title="GitHub Issues Response Time"
  subtitle="First response is when a comment is made by a GitHub user other than the original issue author"
  yAxisTitle="Percentage of issues"
  colorPalette={[
    '#ff7675', /* Red for Time to Close */
    '#85ea7d', /* Green for Time to First Response */
  ]}
  yFmt=pct
  xType="category"
  xGridLines=true
  xLabelRotation={45}
  legendPosition="bottom"
/>
