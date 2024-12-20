with monthly_counts as (
    select 
        date_trunc('month', to_timestamp(timestamp)::timestamp) as month,
        sum(number_of_commits) as num_commits
    from nfcore_issues_stats.gh_commits
    where to_timestamp(timestamp)::timestamp >= '2020-01-01'
    group by 1
    order by month
)
select 
    month,
    num_commits,
    lag(num_commits) over (order by month) as prev_month_num_commits,
    round(
        cast(
            (
                num_commits / nullif(lag(num_commits) over (order by month), 0) - 1
            ) * 100 as numeric
        ),
        1
    ) as growth_rate
from monthly_counts