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

<LineChart
data={subscribers_filtered}
x=timestamp
y=value
series=category
title="nf-core newsletter subscribers over time"
subtitle="Per day from {inputs.range_filtering_a_query.start} to {inputs.range_filtering_a_query.end}"
/>

ℹ️ **Subscribed** contacts have confirmed their email address (completed double opt-in) and receive the newsletter. **Pending** contacts have signed up but not yet confirmed.
