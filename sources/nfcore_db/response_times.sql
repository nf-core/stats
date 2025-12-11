USE nf_core_stats_bot;

-- Combined PR and Issue response times histogram data split by repo type
WITH time_bins AS (
  SELECT * FROM VALUES
    ('1 hour', 0, 3600),
    ('2 hours', 3600, 7200),
    ('3 hours', 7200, 10800),
    ('4 hours', 10800, 14400),
    ('5 hours', 14400, 18000),
    ('6 hours', 18000, 21600),
    ('12 hours', 21600, 43200),
    ('1 day', 43200, 86400),
    ('2 days', 86400, 172800),
    ('3 days', 172800, 259200),
    ('4 days', 259200, 345600),
    ('5 days', 345600, 432000),
    ('6 days', 432000, 518400),
    ('7 days', 518400, 604800),
    ('14 days', 604800, 1209600),
    ('1 month', 1209600, 2678400),
    ('6 months', 2678400, 15811200),
    ('1 year', 15811200, 31536000),
    ('Over 1 year', 31536000, 999999999999)
  AS t(label, min_seconds, max_seconds)
),

pr_pipeline_totals AS (
  SELECT COUNT(*) as total
  FROM github.issue_stats i
  JOIN github.nfcore_pipelines p ON i.pipeline_name = p.name
  WHERE i.issue_type = 'pr' AND i.closed_wait_seconds IS NOT NULL
),

pr_core_totals AS (
  SELECT COUNT(*) as total
  FROM github.issue_stats i
  LEFT JOIN github.nfcore_pipelines p ON i.pipeline_name = p.name
  WHERE i.issue_type = 'pr' AND i.closed_wait_seconds IS NOT NULL AND p.name IS NULL
),

issue_pipeline_totals AS (
  SELECT COUNT(*) as total
  FROM github.issue_stats i
  JOIN github.nfcore_pipelines p ON i.pipeline_name = p.name
  WHERE i.issue_type = 'issue' AND i.closed_wait_seconds IS NOT NULL
),

issue_core_totals AS (
  SELECT COUNT(*) as total
  FROM github.issue_stats i
  LEFT JOIN github.nfcore_pipelines p ON i.pipeline_name = p.name
  WHERE i.issue_type = 'issue' AND i.closed_wait_seconds IS NOT NULL AND p.name IS NULL
)

SELECT
  b.label,
  'pr' as type,
  b.min_seconds,
  -- PR Pipeline repos
  ROUND(
    CAST(COUNT(CASE WHEN p.name IS NOT NULL AND i1.issue_type = 'pr' AND i1.closed_wait_seconds IS NOT NULL THEN 1 END) AS FLOAT) /
    (SELECT total FROM pr_pipeline_totals),
    6
  ) as pipeline_time_to_close,
  -- PR Core repos
  ROUND(
    CAST(COUNT(CASE WHEN p.name IS NULL AND i1.issue_type = 'pr' AND i1.closed_wait_seconds IS NOT NULL THEN 1 END) AS FLOAT) /
    (SELECT total FROM pr_core_totals),
    6
  ) as core_time_to_close
FROM time_bins b
LEFT JOIN github.issue_stats i1 ON (
  i1.issue_type = 'pr'
  AND i1.closed_wait_seconds > b.min_seconds
  AND i1.closed_wait_seconds <= b.max_seconds
)
LEFT JOIN github.nfcore_pipelines p ON i1.pipeline_name = p.name
GROUP BY b.label, b.min_seconds

UNION ALL

SELECT
  b.label,
  'issue' as type,
  b.min_seconds,
  -- Issue Pipeline repos
  ROUND(
    CAST(COUNT(CASE WHEN p.name IS NOT NULL AND i1.issue_type = 'issue' AND i1.closed_wait_seconds IS NOT NULL THEN 1 END) AS FLOAT) /
    (SELECT total FROM issue_pipeline_totals),
    6
  ) as pipeline_time_to_close,
  -- Issue Core repos
  ROUND(
    CAST(COUNT(CASE WHEN p.name IS NULL AND i1.issue_type = 'issue' AND i1.closed_wait_seconds IS NOT NULL THEN 1 END) AS FLOAT) /
    (SELECT total FROM issue_core_totals),
    6
  ) as core_time_to_close
FROM time_bins b
LEFT JOIN github.issue_stats i1 ON (
  i1.issue_type = 'issue'
  AND i1.closed_wait_seconds > b.min_seconds
  AND i1.closed_wait_seconds <= b.max_seconds
)
LEFT JOIN github.nfcore_pipelines p ON i1.pipeline_name = p.name
GROUP BY b.label, b.min_seconds

ORDER BY type, min_seconds
