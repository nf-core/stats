USE nf_core_stats_bot;

-- Karma points per GitHub user since review collection started:
-- merged PR 3, review of someone else's PR 2 (once per PR), opened issue 1.
-- github.pr_reviews only holds reviews from that date on (see pr_reviews in github_pipeline.py).
-- Bot and LLM accounts follow BOT_NAMES in https://github.com/ewels/contributor-graphs/blob/main/src/identity.rs
WITH params AS (
    SELECT TIMESTAMPTZ '2026-11-13 00:00:00+00' AS since
),
events AS (
    SELECT created_by AS login, 'pr' AS kind
    FROM github.issue_stats, params
    WHERE issue_type = 'pr' AND merged_at >= since

    UNION ALL

    SELECT reviewer AS login, 'review' AS kind
    FROM (
        SELECT DISTINCT pipeline_name, pr_number, reviewer
        FROM github.pr_reviews
        WHERE reviewer <> pr_author
    )

    UNION ALL

    SELECT created_by AS login, 'issue' AS kind
    FROM github.issue_stats, params
    WHERE issue_type = 'issue' AND created_at >= since
)
SELECT
    login,
    COUNT(*) FILTER (WHERE kind = 'pr') AS prs_merged,
    COUNT(*) FILTER (WHERE kind = 'review') AS reviews,
    COUNT(*) FILTER (WHERE kind = 'issue') AS issues,
    3 * prs_merged + 2 * reviews + issues AS karma
FROM events
WHERE login IS NOT NULL
    AND NOT contains(lower(login), '[bot]')
    AND lower(login) NOT IN (
        'github-actions', 'dependabot', 'renovate', 'greenkeeper', 'snyk-bot', 'travis', 'runner',
        'nf-core-bot', 'semantic-release-bot', 'allcontributors', 'pre-commit-ci', 'imgbot', 'codecov',
        'whitesource', 'deepsource', 'pyup-bot', 'mergify', 'copilot'
    )
GROUP BY login
ORDER BY karma DESC, login;
