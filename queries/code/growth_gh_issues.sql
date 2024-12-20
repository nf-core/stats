with monthly_latest as (
    select distinct on (date_trunc('month', date))
        date_trunc('month', date) as month,
        closed + open as num_issues
    from stats_static.github_issues
    where date >= '2020-01-01'
    order by date_trunc('month', date), date desc
)
select 
    month,
    num_issues,
    lag(num_issues) over (order by month) as prev_month_num_issues,
    round(
        cast(
            (
                num_issues / nullif(lag(num_issues) over (order by month), 0) - 1
            ) * 100 as numeric
        ),
        1
    ) as growth_rate
from monthly_latest
order by month desc 