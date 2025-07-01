with monthly_counts as (
    select date_trunc('month', generate_series) as month,
        max(closed_merged + open) as num_prs,
        max(open) as num_open_prs
    from nfcore_db.issues_and_prs_over_time
        cross join generate_series(
            date_trunc('month', '2020-01-01'::timestamp),
            date_trunc('month', current_date),
            interval '1 month'
        )
    where timestamp <= generate_series
    and type = 'pr'
    group by 1
)
select month,
    num_prs,
    num_open_prs,
    lag(num_prs) over (
        order by month
    ) as prev_month_num_prs,
    lag(num_open_prs) over (
        order by month
    ) as prev_month_num_open_prs,
    round(
        cast(
            (
                num_prs / nullif(
                    lag(num_prs) over (
                        order by month
                    ),
                    0
                ) - 1
            ) as numeric
        ),
        1
    ) as growth_rate,
    round(
        cast(
            (
                num_open_prs / nullif(
                    lag(num_open_prs) over (
                        order by month
                    ),
                    0
                ) - 1
            ) * 100 as numeric
        ),
        1
    ) as open_growth_rate

from monthly_counts
order by month desc