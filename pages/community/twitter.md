---
title: Twitter
sidebar_position: 2
---

Up until 2025-01-20, we used our [@nf_core](https://twitter.com/nf_core) twitter account to send automated tweets about new pipeline releases and other updates relevant to the community. 

Follower counts give some indication to the historical level of interest in the nf-core project.

```sql view_days
select
    to_timestamp(timestamp) as date
from twitter
group by 1
```

<DateRange
    name=range_filtering_a_query
    data={view_days}
    dates=date
    defaultValue="All Time"
/>

```twitter_followers
select 
    to_timestamp(timestamp) as date,
    followers_count
from twitter
where date between '${inputs.range_filtering_a_query.start}' and '${inputs.range_filtering_a_query.end}'
```

<AreaChart
    data={twitter_followers}
    x=date
    y=followers_count
    title="nf-core Twitter followers over time"
    subtitle="Per day from {inputs.range_filtering_a_query.start} to {inputs.range_filtering_a_query.end}"
/>


⚠️ Data from before 2019-06-26 fudged by reverse-engineering a tiny sparkline plot on the twitter analytics website.

