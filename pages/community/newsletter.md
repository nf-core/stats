---
title: Newsletter
sidebar_position: 3
---

The nf-core monthly newsletter rounds up community news, new pipeline releases, events and more. Sign up (double opt-in, one-click unsubscribe) at [nf-co.re/newsletter](https://nf-co.re/newsletter). Subscriptions are managed with Amazon SES.

```sql view_days
select
    timestamp
from newsletter_subscribers
group by 1 order by 1 desc
```

<DateRange
    name=range_filtering_a_query
    data={view_days}
    dates=timestamp
    defaultValue="All Time"
    for
/>

```subscribers_filtered
select distinct * from newsletter_subscribers
where timestamp between '${inputs.range_filtering_a_query.start}' and ('${inputs.range_filtering_a_query.end}'::date + interval '1 day')
order by 1 desc
```

<AreaChart
data={subscribers_filtered}
x=timestamp
y=value
series=category
seriesOrder={['subscribed', 'pending', 'inactive']}
title="nf-core newsletter subscribers over time"
subtitle="Per day from {inputs.range_filtering_a_query.start} to {inputs.range_filtering_a_query.end}"
echartsOptions={{legend: {selected: {inactive: false}}}}
/>

ℹ️ **Subscribed** contacts have confirmed their email address (completed double opt-in) and receive the newsletter. **Pending** contacts have signed up in the last 7 days but not yet confirmed. **Inactive** contacts never confirmed and are now more than 7 days old — hidden by default, click the legend to show them.
