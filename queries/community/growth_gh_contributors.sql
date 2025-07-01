select
    date_trunc('month', timestamp) as month,
    count(distinct username) as contributors,
    lag(count(distinct username)) over (order by date_trunc('month', timestamp)) as prev_month_contributors,
    round(cast((count(distinct username) / nullif(lag(count(distinct username)) over (order by date_trunc('month', timestamp)), 0) - 1) as numeric), 1) as growth_rate
from community_github_contributors
group by date_trunc('month', timestamp)
order by date_trunc('month', timestamp) desc