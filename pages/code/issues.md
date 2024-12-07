---
title: Issues
sidebar_position: 3
---

# GitHub Issues

GitHub issues can be created to log feature requests, bug reports or questions.

<!-- TODO: Live data https://github.com/nf-core/stats/issues/4 -->

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

<!-- TODO GitHub Issues Response Time -->
*We're working on a dashboard to show the response times of issues. See [this issue](https://github.com/nf-core/stats/issues/5) for more details.*
