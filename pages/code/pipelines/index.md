---
title: Pipeline numbers
sidebar_position: 1
---

All nf-core pipelines are only considered stable when they have at least one release. Until then, they are classed as "in development".


```sql pipeline_chart_data
-- Transform the data for the area chart
SELECT 
  date,
  in_development as count,
  'in development' as status
FROM nfcore_db.pipeline_numbers
UNION ALL
SELECT 
  date,
  released as count,
  'released' as status
FROM nfcore_db.pipeline_numbers
ORDER BY date, status, count
```

<AreaChart
data={pipeline_chart_data}
x=date
y=count
series=status
seriesOrder={['released','in development']} 
title="nf-core pipeline numbers over time"
yAxisTitle="Number of pipelines"
/>

## Pipeline Status

```sql latest_numbers
-- Get the most recent counts for both statuses
WITH latest_data AS (
  SELECT 
    in_development,
    released
  FROM nfcore_db.pipeline_numbers
  ORDER BY date DESC
  LIMIT 1
)
SELECT 
  'In development' as status,
  in_development as count
FROM latest_data

UNION ALL

SELECT 
  'Released' as status,
  released as count
FROM latest_data
```

- <Value data={latest_numbers.where(`status = 'In development'`)} column=count/> pipelines in development
- <Value data={latest_numbers.where(`status = 'Released'`)} column=count/> released pipelines

## Pipelines

```sql pipeline_table
select
      'https://nf-co.re/' || name as repository_link,
      *
from nfcore_db.all_repos
order by stargazers_count desc
```

<DataTable
data={pipeline_table}
defaultSort={[{ id: 'Stargazers', desc: true }]}
search=true
wrapTitles=true
totalRow=true
link=repository_link
/>

---

## Related

For a detailed timeline view of individual pipeline development cycles, see the [Pipeline Development Timeline](timeline) page. This shows when each pipeline was in development and helps answer whether old pipelines are finally being released or if there are quick-fire pipeline releases.
