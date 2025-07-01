USE nf_core_stats_bot;

-- get the first commit date for each contributor, meaning the first week that is not 0 commits and add it to the gh_contributors table

SELECT DISTINCT 
    author, 
    avatar_url, 
    SUM(week_commits) AS total_sum_commits,
    SUM(week_additions) AS total_sum_additions,
    SUM(week_deletions) AS total_sum_deletions,
    MIN(CASE WHEN week_commits > 0 THEN week_date END) AS first_commit_week,
    MAX(CASE WHEN week_commits > 0 THEN week_date END) AS last_commit_week
FROM github.contributor_stats
GROUP BY author, avatar_url
ORDER BY total_sum_commits DESC







