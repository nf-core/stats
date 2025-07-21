select
    date_trunc('month', timestamp) as month,
    value as members,
    lag(value) over (order by date_trunc('month', timestamp)) as prev_month_members,
    round(cast((value / nullif(lag(value) over (order by date_trunc('month', timestamp)), 0) - 1) as numeric), 1) as growth_rate
from slack_users
where timestamp >= '2020-01-01'
  and category = 'active_users'
group by 1, 2, date_trunc('month', timestamp), value
order by date_trunc('month', timestamp) desc