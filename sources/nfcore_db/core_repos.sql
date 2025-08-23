USE nf_core_stats_bot;

SELECT 
  name,
  description,
  gh_created_at,
  gh_updated_at,
  gh_pushed_at,
  stargazers_count,
  watchers_count,
  forks_count,
  open_issues_count,
  topics,
  default_branch,
  archived,
  category
FROM github.nfcore_pipelines 
WHERE category = 'core'
ORDER BY stargazers_count DESC;
