---
title: Pipeline numbers
sidebar_position: 5
---

All nf-core pipelines are only considered stable when they have at least one release. Until then, they are classed as "in development".

```sql pipeline_numbers
select 
  date::date as date,
  'Released' as status,
  released as count
from stats_static.pipeline_numbers
union all
select
  date::date as date,
  'In development' as status,
  in_development as count
from stats_static.pipeline_numbers
order by date asc, status asc
```

<AreaChart
  data={pipeline_numbers}
  x=date
  y=count
  series=status
  seriesOrder={['Released', 'In development']}
  title="nf-core pipeline numbers over time"
  yAxisTitle="Number of pipelines"
  colorPalette={['#4DB6AC', '#EF5350']}
/>

## Pipeline Status

As of <Value data={pipeline_numbers} column=date row=last/>, there are:
- <Value data={pipeline_numbers} column=count filter="status = 'In development'" /> pipelines in development
- <Value data={pipeline_numbers} column=count filter="status = 'Released'" /> released pipelines

<!-- TODO Table with Name 	Age 	Releases 	Committers 	Commits 	Stargazers 	Watchers 	Network Forks 	Clones 	Unique cloners 	Repo views 	Unique repo visitors -->

## Pipelines

<!-- TODO Table with Name 	Age 	Releases 	Committers 	Commits 	Stargazers 	Watchers 	Network Forks 	Clones 	Unique cloners 	Repo views 	Unique repo visitors -->
