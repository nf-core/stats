SELECT
    month,
    type,
    total_count AS num_total,
    open_count AS num_open,
    lag(total_count) OVER (PARTITION BY type ORDER BY month) AS prev_month_total,
    lag(open_count) OVER (PARTITION BY type ORDER BY month) AS prev_month_open,
    round((total_count / lag(total_count, 1, 1) OVER (PARTITION BY type ORDER BY month) - 1)::numeric, 1) AS growth_rate,
    round((open_count / lag(open_count, 1, 1) OVER (PARTITION BY type ORDER BY month) - 1)::numeric * 100, 1) AS open_growth_rate
FROM (
    SELECT
        date_trunc('month', generate_series) AS month,
        type,
        max(closed_merged + open) AS total_count,
        max(open) AS open_count
    FROM nfcore_db.issues_and_prs_over_time
    CROSS JOIN generate_series(
        date_trunc('month', '2020-01-01'::timestamp),
        date_trunc('month', current_date),
        INTERVAL '1 month'
    )
    WHERE timestamp <= generate_series
        AND type IN ('issue', 'pr')
    GROUP BY ALL
)
ORDER BY type, month DESC
