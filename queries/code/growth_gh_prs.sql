USE nf_core_stats_bot;
with monthly_counts as (
    select date_trunc('month', generate_series) as month,
        max(closed_merged) as num_prs
    from github.issue_stats
        cross join generate_series(
            date_trunc('month', '2020-01-01'::timestamp),
            date_trunc('month', current_date),
            interval '1 month'
        )
    where date <= generate_series
    group by 1
)
select month,
    num_prs,
    lag(num_prs) over (
        order by month
    ) as prev_month_num_prs,
    round(
        cast(
            (
                num_prs / nullif(
                    lag(num_prs) over (
                        order by month
                    ),
                    0
                ) - 1
            ) * 100 as numeric
        ),
        1
    ) as growth_rate
from monthly_counts
order by month desc