USE nf_core_stats_bot;

SELECT
  p.name,
  p.description,
  p.gh_created_at,
  p.gh_updated_at,
  p.stargazers_count,
  p.watchers_count,
  p.forks_count,
  p.open_issues_count,
  LIST(t.value) as topics,
  p.default_branch,
  p.archived,
FROM github.nfcore_pipelines p
LEFT JOIN github.nfcore_pipelines__topics t ON p._dlt_id = t._dlt_parent_id
WHERE p.category = 'core'
GROUP BY ALL
ORDER BY p.stargazers_count DESC;
