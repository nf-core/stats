---
title: Pipeline numbers
sidebar_position: 5
---

All nf-core pipelines are only considered stable when they have at least one release. Until then, they are classed as "in development".

```sql pipeline_numbers
select
  date::date as date,
  'In development' as status,
  in_development as count
from stats_static.pipeline_numbers
union all
select
  date::date as date,
  'Released' as status,
  released as count
from stats_static.pipeline_numbers
order by date asc, status desc
```

<AreaChart
data={pipeline_numbers}
x=date
y=count
series=status
seriesOrder={['In development', 'Released']}
title="nf-core pipeline numbers over time"
yAxisTitle="Number of pipelines"
/>

## Pipeline Status

```sql latest_numbers
-- Get the most recent counts for both statuses
with latest_date as (
  select max(date::date) as max_date
  from stats_static.pipeline_numbers
)
select
  'In development' as status,
  in_development as count
from stats_static.pipeline_numbers
where date::date = (select max_date from latest_date)
union all
select
  'Released' as status,
  released as count
from stats_static.pipeline_numbers
where date::date = (select max_date from latest_date)
```

- <Value data={latest_numbers.where(`status = 'In development'`)} column=count/> pipelines in development
- <Value data={latest_numbers.where(`status = 'Released'`)} column=count/> released pipelines

<!-- TODO Use pull in live data <LastRefreshed prefix="As of"/> -->

## Pipelines

```sql pipeline_table
select
  *
from stats_static.pipelines
order by Stargazers desc
```

<!-- TODO Add links -->

We're working on using live data for this table, but it's not quite ready yet. Check [this issue](https://github.com/nf-core/stats/issues/9) for updates.

<DataTable
data={pipeline_table}
defaultSort={[{ id: 'Stargazers', desc: true }]}
search=true
wrapTitles=true
totalRow=true
/>
