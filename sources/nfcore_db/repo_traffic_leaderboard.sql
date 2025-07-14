USE nf_core_stats_bot;

SELECT 
    t.pipeline_name as repository,
    'https://github.com/nf-core/' || t.pipeline_name as repository_link,
    SUM(COALESCE(t.views, 0)) as total_views,
    SUM(COALESCE(t.views_uniques, 0)) as total_views_unique,
    SUM(COALESCE(t.clones, 0)) as total_clones,
    SUM(COALESCE(t.clones_uniques, 0)) as total_clones_unique,
    COALESCE(p.stargazers_count, 0) as stargazers_count
FROM github.traffic_stats t
LEFT JOIN github.nfcore_pipelines p ON t.pipeline_name = p.name
GROUP BY t.pipeline_name, p.stargazers_count, p.name
ORDER BY total_views DESC