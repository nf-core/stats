USE nf_core_stats_bot;

-- Pipeline numbers over time - using existing github.nfcore_pipelines table
WITH date_series AS (
  -- Generate monthly series from first pipeline to today
  SELECT UNNEST(generate_series(
    date_trunc('week', (SELECT MIN(gh_created_at) FROM github.nfcore_pipelines WHERE NOT archived)),
    date_trunc('week', CURRENT_DATE),
    INTERVAL '1 week'
  )) AS date
),

pipeline_stats AS (
  SELECT
    date,
    -- Count pipelines created by this date
    (SELECT COUNT(*) FROM github.nfcore_pipelines
     WHERE date_trunc('week', gh_created_at) <= date AND NOT archived AND category = 'pipeline') AS total_created,
    -- Count pipelines released by this date
    (SELECT COUNT(*) FROM github.nfcore_pipelines
     WHERE date_trunc('week', last_release_date) <= date AND NOT archived AND last_release_date IS NOT NULL AND category = 'pipeline') AS total_released
  FROM date_series
)

SELECT
  date,
  total_created - total_released AS in_development,
  total_released AS released,
FROM pipeline_stats
ORDER BY date;
