select
    date_trunc('month', timestamp) as month,
    count(*) as members,
    lag(count(*)) over (order by date_trunc('month', timestamp)) as prev_month_members,
    count(*) / nullif(lag(count(*)) over (order by date_trunc('month', timestamp)), 0) - 1 as growth_rate
from nfcore_db.community_github_members
where timestamp >= date_trunc('month', current_date - interval '12 months')
group by 1
order by 1 desc