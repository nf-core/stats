USE nf_core_stats_bot;

SELECT
    name,
    description,
    stargazers_count,
    watchers_count,
    forks_count,
    open_issues_count,
    archived,
    last_release_date,
    category
FROM github.nfcore_pipelines
WHERE category = 'pipeline'
ORDER BY name;
