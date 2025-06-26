USE nf_core_stats_bot;

SELECT
    timestamp,
    SUM(views) AS sum_total_views,
    SUM(views_uniques) AS sum_total_views_unique

FROM github.traffic_stats
INNER JOIN
    github.nfcore_pipelines
    ON github.traffic_stats.pipeline_name = github.nfcore_pipelines.name
GROUP BY timestamp
ORDER BY timestamp ASC
