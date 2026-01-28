USE nf_core_stats_bot;

SELECT
  name,
  archived,
  gh_created_at,
  COALESCE(last_release_date, gh_created_at) as last_release_date,
  COALESCE(stargazers_count, 0) as stargazers_count
FROM github.nfcore_pipelines
WHERE name IS NOT NULL
  AND gh_created_at IS NOT NULL
