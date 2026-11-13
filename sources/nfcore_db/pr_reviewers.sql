USE nf_core_stats_bot;

-- Distinct pull requests reviewed by each person.
-- github.pr_reviews is filled newest-first back to 2018-01-01; until that walk finishes,
-- older reviews are absent. The last two days are re-read on every pipeline run.
-- GitHub App accounts use a [bot] login suffix; they are left out of the leaderboard.
SELECT
    reviewer AS login,
    COUNT(DISTINCT pipeline_name || '#' || CAST(pr_number AS VARCHAR)) AS prs_reviewed,
    '<div style="display: flex; align-items: center;"><img src="https://github.com/' || reviewer || '.png?size=80" style="width: 40px; height: 40px; border-radius: 50%; margin-right: 8px;" alt="' || reviewer || '" /><a href="https://github.com/' || reviewer || '" target="_blank" style="text-decoration: none;">@' || reviewer || '</a></div>' AS contributor
FROM github.pr_reviews
WHERE reviewer IS NOT NULL
    AND NOT ends_with(reviewer, '[bot]')
    -- nf-core-bot and Copilot act without the [bot] login suffix.
    AND lower(reviewer) NOT IN ('nf-core-bot', 'copilot')
GROUP BY reviewer
ORDER BY prs_reviewed DESC, login
