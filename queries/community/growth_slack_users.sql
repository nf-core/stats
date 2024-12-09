select
    date_trunc('month', to_timestamp(timestamp)::timestamp) as month,
    total_users as members,
    lag(total_users) over (order by date_trunc('month', to_timestamp(timestamp)::timestamp)) as prev_month_members,
    round(cast((total_users / nullif(lag(total_users) over (order by date_trunc('month', to_timestamp(timestamp)::timestamp)), 0) - 1) * 100 as numeric), 1) as growth_rate
from nfcore_db.slack
where to_timestamp(timestamp)::timestamp >= '2020-01-01'
group by 1, 2, date_trunc('month', to_timestamp(timestamp)::timestamp), total_users
order by date_trunc('month', to_timestamp(timestamp)::timestamp) desc