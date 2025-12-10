---
title: Repository Traffic
sidebar_position: 10
queries:
  - code/clone_view_counts.sql
---

Every time a nextflow user pulls an nf-core pipeline, the repository is cloned. Here we can track how much that happens across all nf-core repositories. Please note that these numbers come with some caveats (GitHub traffic data has a 14-day retention period and may not capture all traffic).

Additionally, GitHub tracks how many times people view repository web pages on github.com.

## Repository Traffic Leaderboard

Here are the nf-core repositories with the highest traffic numbers. This includes both pipeline repositories and core repositories (such as the code for this website).

```sql repo_traffic_leaderboard
select * from nfcore_db.repo_traffic_leaderboard
```

<DataTable 
    data={repo_traffic_leaderboard}
    search=true
    wrapTitles=true
    totalRow=true
    defaultSort={[{ id: 'total_views', desc: true }]}>

    <Column id="repository_link" title="Repository" align="left" contentType=link linkLabel=repository />
    <Column id="total_views" title="Total Views" align="right"/>
    <Column id="total_views_unique" title="Unique Views" align="right"/>
    <Column id="total_clones" title="Total Clones" align="right"/>
    <Column id="total_clones_unique" title="Unique Clones" align="right"/>
    <Column id="stargazers_count" title="Stars" align="right"/>

</DataTable>

## Repository Traffic: All nf-core repositories

<DateRange
    name=range_filtering_a_query
    data={code_clone_view_counts}
    dates=timestamp
    defaultValue="All Time"
/>

```views_filtered
SELECT
    DATE_TRUNC('week', timestamp) as timestamp,
    SUM(sum_total_views) AS value,
    'total_views' AS category
from ${code_clone_view_counts}
where timestamp between '${inputs.range_filtering_a_query.start}' and '${inputs.range_filtering_a_query.end}'
GROUP BY DATE_TRUNC('week', timestamp)

UNION ALL

SELECT
    DATE_TRUNC('week', timestamp) as timestamp,
    SUM(sum_total_views_unique) AS value,
    'total_views_unique' AS category
from ${code_clone_view_counts}
where timestamp between '${inputs.range_filtering_a_query.start}' and '${inputs.range_filtering_a_query.end}'
GROUP BY DATE_TRUNC('week', timestamp)
```

```clones_filtered
SELECT
    DATE_TRUNC('week', timestamp) as timestamp,
    SUM(sum_total_clones) AS value,
    'total_clones' AS category
from ${code_clone_view_counts}
where timestamp between '${inputs.range_filtering_a_query.start}' and '${inputs.range_filtering_a_query.end}'
GROUP BY DATE_TRUNC('week', timestamp)

UNION ALL

SELECT
    DATE_TRUNC('week', timestamp) as timestamp,
    SUM(sum_total_clones_unique) AS value,
    'total_clones_unique' AS category
from ${code_clone_view_counts}
where timestamp between '${inputs.range_filtering_a_query.start}' and '${inputs.range_filtering_a_query.end}'
GROUP BY DATE_TRUNC('week', timestamp)
```

```traffic_by_day_filtered
select * from ${code_clone_view_counts}
where timestamp between '${inputs.range_filtering_a_query.start}' and '${inputs.range_filtering_a_query.end}'
```

<Tabs>
    <Tab label="Views">

<LineChart
data={views_filtered}
x=timestamp
y=value
series=category
title="Views: All nf-core repositories"
subtitle="nf-core repository web views per week from {inputs.range_filtering_a_query.start} to {inputs.range_filtering_a_query.end}"> 
<ReferenceArea xMin='2024-01-24' xMax='2025-06-09' label="Data outage" color="gray"/>
</LineChart>

<CalendarHeatmap
    data={traffic_by_day_filtered}
    date=timestamp
    value=sum_total_views_unique
    title="Views per day"
    subtitle="Unique views per day from {inputs.range_filtering_a_query.start} to {inputs.range_filtering_a_query.end}"
    legend=true
/>

    </Tab>
    <Tab label="Clones">

<AreaChart
data={clones_filtered}
x=timestamp
y=value
series=category
title="Clones: All nf-core repositories"
subtitle="nf-core repository clones per week from {inputs.range_filtering_a_query.start} to {inputs.range_filtering_a_query.end}"> 
<ReferenceArea xMin='2024-01-24' xMax='2025-06-09' label="Data outage" color="gray"/>
</AreaChart>

<CalendarHeatmap
    data={traffic_by_day_filtered}
    date=timestamp
    value=sum_total_clones_unique
    title="Clones per day"
    subtitle="Unique clones per day from {inputs.range_filtering_a_query.start} to {inputs.range_filtering_a_query.end}"
    legend=true
/>

    </Tab>

</Tabs>

```view_counts_summary
select * from ${code_clone_view_counts}
```

```view_counts_summary_top100
select
*
from ${code_clone_view_counts}
order by sum_total_views desc
limit 100
```
