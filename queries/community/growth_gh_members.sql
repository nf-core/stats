select
    date_trunc('month', timestamp) as month,
    max(total_github_members) as members,
    lag(max(total_github_members)) over (order by date_trunc('month', timestamp)) as prev_month_members,
    round(cast((max(total_github_members) / nullif(lag(max(total_github_members)) over (order by date_trunc('month', timestamp)), 0) - 1) as numeric), 1) as growth_rate
from nfcore_db.community_github_members
group by date_trunc('month', timestamp)
order by date_trunc('month', timestamp) desc
