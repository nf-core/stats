with monthly as (
    select
        date_trunc('month', timestamp) as month,
        max(value) as subscribers
    from newsletter_subscribers
    where category = 'subscribed'
    group by 1
),
with_lag as (
    select
        month,
        subscribers,
        lag(subscribers) over (order by month) as prev_month_subscribers
    from monthly
)
select
    month,
    subscribers,
    prev_month_subscribers,
    round(cast(subscribers::float / nullif(prev_month_subscribers, 0) - 1 as numeric), 3) as growth_rate
from with_lag
order by month desc
