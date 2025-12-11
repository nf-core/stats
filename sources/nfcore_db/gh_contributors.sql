USE nf_core_stats_bot;

-- Pipeline contributions: contributors stats for repositories categorized as 'pipeline'
SELECT DISTINCT 
    'pipeline' as contribution_type,
    cs.author, 
    cs.avatar_url, 
    SUM(cs.week_commits) AS total_sum_commits,
    SUM(cs.week_additions) AS total_sum_additions,
    SUM(cs.week_deletions) AS total_sum_deletions,
    MIN(CASE WHEN cs.week_commits > 0 THEN cs.week_date END) AS first_commit_week,
    MAX(CASE WHEN cs.week_commits > 0 THEN cs.week_date END) AS last_commit_week
FROM github.contributor_stats cs
INNER JOIN github.nfcore_pipelines p ON cs.pipeline_name = p.name
WHERE p.category = 'pipeline'
GROUP BY cs.author, cs.avatar_url

UNION ALL

-- Core repository contributions: contributors stats for repositories categorized as 'core'
SELECT DISTINCT 
    'core' as contribution_type,
    cs.author, 
    cs.avatar_url, 
    SUM(cs.week_commits) AS total_sum_commits,
    SUM(cs.week_additions) AS total_sum_additions,
    SUM(cs.week_deletions) AS total_sum_deletions,
    MIN(CASE WHEN cs.week_commits > 0 THEN cs.week_date END) AS first_commit_week,
    MAX(CASE WHEN cs.week_commits > 0 THEN cs.week_date END) AS last_commit_week
FROM github.contributor_stats cs
INNER JOIN github.nfcore_pipelines p ON cs.pipeline_name = p.name
WHERE p.category = 'core'
GROUP BY cs.author, cs.avatar_url
ORDER BY contribution_type, total_sum_commits DESC;







