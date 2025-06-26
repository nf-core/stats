USE nf_core_stats_bot;

-- Combined Issues and PRs over time
SELECT
  DATE_TRUNC('week', created_at) as timestamp,
  'issue' as type,
  AVG(COUNT(CASE WHEN closed_at IS NOT NULL THEN 1 END)) OVER (ORDER BY DATE_TRUNC('week', created_at) ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as closed_merged,
  AVG(COUNT(CASE WHEN closed_at IS NULL THEN 1 END)) OVER (ORDER BY DATE_TRUNC('week', created_at) ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as open
FROM github.issue_stats
WHERE issue_type = 'issue'
GROUP BY DATE_TRUNC('week', created_at)

UNION ALL

SELECT
  DATE_TRUNC('week', created_at) as timestamp,
  'pr' as type,
  AVG(COUNT(CASE WHEN closed_at IS NOT NULL THEN 1 END)) OVER (ORDER BY DATE_TRUNC('week', created_at) ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as closed_merged,
  AVG(COUNT(CASE WHEN closed_at IS NULL THEN 1 END)) OVER (ORDER BY DATE_TRUNC('week', created_at) ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as open
FROM github.issue_stats
WHERE issue_type = 'pr'
GROUP BY DATE_TRUNC('week', created_at)

ORDER BY type, timestamp; 