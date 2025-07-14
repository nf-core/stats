-- This query depends on the traffic_stats_raw source
-- It aggregates traffic data by timestamp for time series visualization

SELECT
    timestamp,
    SUM(views) AS sum_total_views,
    SUM(views_uniques) AS sum_total_views_unique,
    SUM(clones) AS sum_total_clones,
    SUM(clones_uniques) AS sum_total_clones_unique
FROM nfcore_db.traffic_stats_raw
GROUP BY timestamp

-- Add explicit 0 records at the boundary dates [24-01-24 until 25-06-10] for proper chart visualization
UNION ALL
SELECT '2024-01-25'::timestamp as timestamp, 0 as sum_total_views, 0 as sum_total_views_unique, 0 as sum_total_clones, 0 as sum_total_clones_unique
UNION ALL
SELECT '2025-06-09'::timestamp as timestamp, 0 as sum_total_views, 0 as sum_total_views_unique, 0 as sum_total_clones, 0 as sum_total_clones_unique

ORDER BY timestamp ASC 