with first_contributions as (
    select 
        username,
        date_trunc('month', min(timestamp)) as first_contribution_month
    from community_github_contributors 
    where week_commits > 0  -- only count actual contributors
    group by username
),
monthly_new_contributors as (
    select 
        first_contribution_month as month,
        count(*) as new_contributors
    from first_contributions
    group by first_contribution_month
),
cumulative_data as (
    select
        month,
        sum(new_contributors) over (order by month rows unbounded preceding) as cumulative_contributors,
        new_contributors
    from monthly_new_contributors
)
select
    month,
    cumulative_contributors,
    new_contributors,
    lag(cumulative_contributors) over (order by month) as prev_month_cumulative,
    round(cast((cumulative_contributors / nullif(lag(cumulative_contributors) over (order by month), 0) - 1) as numeric), 3) as growth_rate
from cumulative_data
order by month desc