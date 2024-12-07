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
colorPalette={[
'#85ea7d',
'#ff7675',
]}
/>

## Pipeline Status

As of <Value data={pipeline_numbers} column=date row=last/>, there are:

- <Value data={pipeline_numbers} column=count filter="status = 'In development'" /> pipelines in development
- <Value data={pipeline_numbers} column=count filter="status = 'Released'" /> released pipelines

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
/>

## Core repos

```sql core_repos_table
select
  *
from stats_static.core_repos
```

We're working on using live data for this table, but it's not quite ready yet. Check [this issue](https://github.com/nf-core/stats/issues/8) for updates.

<DataTable
data={core_repos_table}
defaultSort={[{ id: 'Stargazers', desc: true }]}
search=true
wrapTitles=true
/>
