---
title: Pipeline numbers
sidebar_position: 5
---

All nf-core pipelines are only considered stable when they have at least one release. Until then, they are classed as "in development".

<!-- TODO Live data https://github.com/nf-core/stats/issues/9 -->

```sql pipeline_numbers
select
  date::date as date,
  in_development,
  released
from stats_static.pipeline_numbers
order by date asc
```

<LineChart
  data={pipeline_numbers}
  x=date
  y={["released", "in_development"]}
  title="nf-core pipeline numbers over time"
  yAxisTitle="Number of pipelines"
  colorPalette={["#4DB6AC", "#EF5350"]} 
/>

## Pipeline Status

As of <Value data={pipeline_numbers} column=date row=last/>, there are:
- <Value data={pipeline_numbers} column=in_development row=last/> pipelines in development
- <Value data={pipeline_numbers} column=released row=last/> released pipelines

<!-- TODO Table with Name 	Age 	Releases 	Committers 	Commits 	Stargazers 	Watchers 	Network Forks 	Clones 	Unique cloners 	Repo views 	Unique repo visitors -->


## Pipelines

<!-- TODO Table with Name 	Age 	Releases 	Committers 	Commits 	Stargazers 	Watchers 	Network Forks 	Clones 	Unique cloners 	Repo views 	Unique repo visitors -->
