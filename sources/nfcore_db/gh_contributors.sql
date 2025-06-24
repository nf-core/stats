USE nf_core_stats_bot;

SELECT DISTINCT author, avatar_url, SUM(week_commits) AS total_sum_commits
FROM github.contributor_stats
GROUP BY author, avatar_url
ORDER BY total_sum_commits DESC
