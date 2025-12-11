USE nf_core_stats_bot;

SELECT
    timestamp,
    views,
    views_uniques,
    clones,
    clones_uniques
FROM github.traffic_stats
INNER JOIN github.nfcore_pipelines
ON github.traffic_stats.pipeline_name = github.nfcore_pipelines.name
