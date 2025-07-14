USE nf_core_stats_bot;

SELECT 
    t.pipeline_name as repository,
    'https://github.com/nf-core/' || t.pipeline_name as repository_link,
    SUM(t.views) as total_views,
    SUM(t.views_uniques) as total_views_unique,
    SUM(t.clones) as total_clones,
    SUM(t.clones_uniques) as total_clones_unique,
    p.stargazers_count
FROM github.traffic_stats t
LEFT JOIN github.nfcore_pipelines p ON t.pipeline_name = p.name
GROUP BY t.pipeline_name, p.stargazers_count, p.name
ORDER BY total_views DESC 