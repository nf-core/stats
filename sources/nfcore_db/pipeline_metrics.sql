USE nf_core_stats_bot;

SELECT
    timestamp,
    SUM(views) AS sum_total_views,
    SUM(views_uniques) AS sum_total_views_uniques,
    SUM(clones) AS sum_total_clones,
    SUM(clones_uniques) AS sum_total_clones_uniques,
    MIN(timestamp) AS min_timestamp
FROM github.traffic_stats
INNER JOIN
    github.nfcore_pipelines
    ON github.traffic_stats.pipeline_name = github.nfcore_pipelines.name
GROUP BY timestamp
ORDER BY timestamp ASC;
