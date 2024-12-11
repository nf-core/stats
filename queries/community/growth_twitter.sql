select date_trunc('month', to_timestamp(timestamp)::timestamp) as month,
    followers,
    lag(followers) over (
        order by date_trunc('month', to_timestamp(timestamp)::timestamp)
    ) as prev_month_followers,
    round(
        cast(
            (
                followers / nullif(
                    lag(followers) over (
                        order by date_trunc('month', to_timestamp(timestamp)::timestamp)
                    ),
                    0
                ) - 1
            ) * 100 as numeric
        ),
        1
    ) as growth_rate
from nfcore_db.twitter
where to_timestamp(timestamp)::timestamp >= '2020-01-01'
group by 1,
    2,
    date_trunc('month', to_timestamp(timestamp)::timestamp),
    followers
order by date_trunc('month', to_timestamp(timestamp)::timestamp) desc