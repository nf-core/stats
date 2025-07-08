---
title: Slack
sidebar_position: 1
---

Slack is a real-time messaging tool, with discussion split into channels and groups. We use it to provide help to people running nf-core pipelines, as well as discussing development ideas. You can join the nf-core slack by getting an invite [here](https://nf-co.re/join/slack).

```sql view_days
select
    timestamp
from slack_users
group by 1 order by 1 desc
```

<DateRange
    name=range_filtering_a_query
    data={view_days}
    dates=timestamp
    defaultValue="All Time"
    for
/>

```users_long_filtered
select * from slack_users
where timestamp between '${inputs.range_filtering_a_query.start}' and ('${inputs.range_filtering_a_query.end}'::date + interval '1 day')
order by 1 desc
```

<AreaChart
    data={users_long_filtered}
    x=timestamp
    y=value
    series=category
    title="nf-core Slack users over time"
    subtitle="Per day from {inputs.range_filtering_a_query.start} to {inputs.range_filtering_a_query.end}"
>
    <ReferenceArea xMin='2024-01-25' xMax='2025-07-07' label="Data outage" color="gray"/>
</AreaChart>

ℹ️ Slack considers users to be inactive when they haven't used slack for the previous 14 days.

⚠️ Data from before 2019-07-24 fudged by reverse-engineering billing details on the slack admin pages.
