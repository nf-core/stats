select
    date_trunc('month', timestamp::timestamp) as month,
    active_users as members,
    lag(active_users) over (order by date_trunc('month', timestamp::timestamp)) as prev_month_members,
    round(cast((active_users / nullif(lag(active_users) over (order by date_trunc('month', timestamp::timestamp)), 0) - 1) as numeric), 1) as growth_rate
from slack
where timestamp::timestamp >= '2020-01-01'
group by 1, 2, date_trunc('month', timestamp::timestamp), active_users
order by date_trunc('month', timestamp::timestamp) desc