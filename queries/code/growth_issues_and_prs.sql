with monthly_counts as (
    select 
        date_trunc('month', generate_series) as month,
        type,
        max(closed_merged + open) as total_count,
        max(open) as open_count
    from nfcore_db.issues_and_prs_over_time
        cross join generate_series(
            date_trunc('month', '2020-01-01'::timestamp),
            date_trunc('month', current_date),
            interval '1 month'
        )
    where timestamp <= generate_series
    and type in ('issue', 'pr')
    group by 1, 2
),
with_lag as (
    select 
        month,
        type,
        total_count,
        open_count,
        lag(total_count) over (partition by type order by month) as prev_month_total,
        lag(open_count) over (partition by type order by month) as prev_month_open
    from monthly_counts
)
select 
    month,
    type,
    total_count as num_total,
    open_count as num_open,
    prev_month_total,
    prev_month_open,
    round(
        cast(
            (total_count / nullif(prev_month_total, 0) - 1) as numeric
        ),
        1
    ) as growth_rate,
    round(
        cast(
            (open_count / nullif(prev_month_open, 0) - 1) * 100 as numeric
        ),
        1
    ) as open_growth_rate
from with_lag
order by type, month desc