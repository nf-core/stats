with monthly_commits as (
    select 
        date_trunc('month', CAST(timestamp as date)) as month,
        sum(cast(week_commits as integer)) as month_commits
    from nfcore_db.community_github_contributors
    where week_commits > 0 and timestamp is not null
    group by 1
),
cumulative_commits as (
    select 
        month,
        month_commits,
        sum(month_commits) over (order by month) as num_commits
    from monthly_commits
)
select 
    month,
    num_commits,
    month_commits,
    lag(month_commits) over (order by month) as prev_month_commits,
    round(
        cast(
            (
                month_commits / nullif(
                    lag(month_commits) over (order by month), 
                    0
                ) - 1
            ) as numeric
        ), 
        1
    ) as growth_rate
from cumulative_commits
order by month desc