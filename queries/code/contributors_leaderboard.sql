SELECT 
  '<div style="display: flex; align-items: center;"><img src="' || avatar_url || '" style="width: 40px; height: 40px; border-radius: 50%; margin-right: 8px;" alt="' || author || '" /><a href="https://github.com/' || author || '" target="_blank" style="text-decoration: none;">@' || author || '</a></div>' AS contributor,
  total_sum_commits AS total_commits,
  total_sum_additions AS total_additions,
  total_sum_deletions AS total_deletions,
  author AS github_username,
  first_commit_week,
  last_commit_week
FROM nfcore_db.gh_contributors
ORDER BY total_sum_commits DESC
LIMIT 100  -- Show top 100 contributors 