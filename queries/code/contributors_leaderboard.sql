-- Contributors leaderboard with separation between pipeline and core repository contributions
WITH contributor_totals AS (
  SELECT
    author,
    avatar_url,
    SUM(CASE WHEN contribution_type = 'pipeline' THEN total_sum_commits ELSE 0 END) AS pipeline_commits,
    SUM(CASE WHEN contribution_type = 'core' THEN total_sum_commits ELSE 0 END) AS core_commits,
    SUM(CASE WHEN contribution_type = 'pipeline' THEN total_sum_additions ELSE 0 END) AS pipeline_additions,
    SUM(CASE WHEN contribution_type = 'core' THEN total_sum_additions ELSE 0 END) AS core_additions,
    SUM(CASE WHEN contribution_type = 'pipeline' THEN total_sum_deletions ELSE 0 END) AS pipeline_deletions,
    SUM(CASE WHEN contribution_type = 'core' THEN total_sum_deletions ELSE 0 END) AS core_deletions,

    SUM(total_sum_commits) AS total_commits,
    SUM(total_sum_additions) AS total_additions,
    SUM(total_sum_deletions) AS total_deletions,
    MIN(first_commit_week) AS first_commit_week,
    MAX(last_commit_week) AS last_commit_week

  FROM nfcore_db.gh_contributors
  GROUP BY author, avatar_url
)
SELECT
  '<div style="display: flex; align-items: center;"><img src="' || avatar_url || '" style="width: 40px; height: 40px; border-radius: 50%; margin-right: 8px;" alt="' || author || '" /><a href="https://github.com/' || author || '" target="_blank" style="text-decoration: none;">@' || author || '</a></div>' AS contributor,
  total_commits,
  pipeline_commits,
  core_commits,
  ROUND(
    CASE
      WHEN total_commits > 0 THEN (core_commits * 100.0 / total_commits)
      ELSE 0
    END, 1
  ) AS core_commits_percentage,
  total_additions,
  pipeline_additions,
  core_additions,
  total_deletions,
  pipeline_deletions,
  core_deletions,
  author AS github_username,
  first_commit_week,
  last_commit_week
FROM contributor_totals
ORDER BY total_commits DESC
LIMIT 100  -- Show top 100 contributors
