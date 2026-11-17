USE nf_core_stats_bot;

-- Pull requests opened by each person. github.issue_stats already stores every PR.
-- GitHub App accounts use a [bot] login suffix; they are left out of the leaderboard.
SELECT
    created_by AS login,
    COUNT(*) AS prs_opened,
    '<div style="display: flex; align-items: center;"><img src="https://github.com/' || created_by || '.png?size=80" style="width: 40px; height: 40px; border-radius: 50%; margin-right: 8px;" alt="' || created_by || '" /><a href="https://github.com/' || created_by || '" target="_blank" style="text-decoration: none;">@' || created_by || '</a></div>' AS contributor
FROM github.issue_stats
WHERE issue_type = 'pr'
    AND created_by IS NOT NULL
    AND NOT ends_with(created_by, '[bot]')
    -- nf-core-bot and Copilot open pull requests without the [bot] login suffix.
    AND lower(created_by) NOT IN ('nf-core-bot', 'copilot')
GROUP BY created_by
ORDER BY prs_opened DESC, login
