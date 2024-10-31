---
title: Slack
sidebar_position: 1
---

Slack is a real-time messaging tool, with discussion split into channels and groups. We use it to provide help to people running nf-core pipelines, as well as discussing development ideas. You can join the nf-core slack by getting an invite [here](https://nf-co.re/join/slack).

```sql view_days
select
    to_timestamp(timestamp) as timestamp
from slack
group by 1
```

<DateRange
    name=range_filtering_a_query
    data={view_days}
    dates=timestamp
    defaultValue="All Time"
/>

<!-- https://github.com/nf-core/website/blob/33acd6a2fab2bf9251e14212ce731ef3232b5969/public_html/stats.php#L714 -->


```users_long_filtered
select * from nfcore_db.slack_users
where timestamp between '${inputs.range_filtering_a_query.start}' and '${inputs.range_filtering_a_query.end}'
order by 3 asc
```

<AreaChart
    data={users_long_filtered}
    x=timestamp
    y=value
    series=category
    title="nf-core Slack users over time"
    subtitle="Per day from {inputs.range_filtering_a_query.start} to {inputs.range_filtering_a_query.end}"
/>

ℹ️Slack considers users to be inactive when they haven't used slack for the previous 14 days.

⚠️Data from before 2019-07-24 fudged by reverse-engineering billing details on the slack admin pages.
