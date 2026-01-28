SELECT
    month,
    month_commits,
    sum(month_commits) OVER (ORDER BY month) AS num_commits,
    round((month_commits / lag(month_commits, 1, 1) OVER (ORDER BY month) - 1)::numeric, 1) AS growth_rate
FROM (
    SELECT
        date_trunc('month', timestamp::date) AS month,
        sum(week_commits::integer) AS month_commits
    FROM nfcore_db.community_github_contributors
    WHERE week_commits > 0 AND timestamp IS NOT NULL
    GROUP BY ALL
)
ORDER BY month DESC
