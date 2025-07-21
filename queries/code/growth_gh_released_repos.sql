SELECT 
    month,
    sum(new_repos) OVER (ORDER BY month) AS num_repos,
    new_repos,
    lag(new_repos) OVER (ORDER BY month) AS prev_month_new_repos,
    round((new_repos / lag(new_repos, 1, 1) OVER (ORDER BY month) - 1)::numeric, 1) AS growth_rate
FROM (
    SELECT 
        date_trunc('month', 
            CASE 
                WHEN last_release_date = 'Not released' THEN NULL
                ELSE last_release_date::date
            END
        ) AS month,
        count(*) AS new_repos
    FROM nfcore_db.all_repos
    WHERE last_release_date != 'Not released' AND last_release_date IS NOT NULL
    GROUP BY ALL
)
ORDER BY month DESC