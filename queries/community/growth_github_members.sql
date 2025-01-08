select
    date_trunc('month', timestamp) as month,
    total_github_members as members,
    lag(total_github_members) over (order by date_trunc('month', timestamp)) as prev_month_members,
    round(cast((total_github_members / nullif(lag(total_github_members) over (order by date_trunc('month', timestamp)), 0) - 1) * 100 as numeric), 1) as growth_rate
from nfcore_db.community_github_members
where timestamp >= '2020-01-01'
group by 1, 2, date_trunc('month', timestamp), total_github_members
order by date_trunc('month', timestamp) desc