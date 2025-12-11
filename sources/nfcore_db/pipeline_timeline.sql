USE nf_core_stats_bot;

-- Pipeline development timeline - showing development periods for each pipeline
-- Updated to use FIRST release date instead of last release date
WITH pipeline_first_releases AS (
    SELECT
        repo,
        MIN(published_at) as first_release_date,
        COUNT(*) as total_releases
    FROM nf_core_dev.tap_github.releases
    WHERE published_at IS NOT NULL
      AND draft = false
      AND prerelease = false
    GROUP BY repo
)
SELECT
    p.name as pipeline_name,
    p.gh_created_at as development_start,
    pfr.first_release_date as development_end,
    COALESCE(pfr.total_releases, 0) as total_releases,
    CASE
        WHEN pfr.first_release_date IS NOT NULL THEN 'Released'
        ELSE 'In Development'
    END as status,
    -- Calculate development duration in days to FIRST release
    CASE
        WHEN pfr.first_release_date IS NOT NULL THEN DATE_DIFF('day', p.gh_created_at, pfr.first_release_date)
        ELSE DATE_DIFF('day', p.gh_created_at, CURRENT_DATE)
    END as development_days,
    -- Extract year for grouping
    EXTRACT(year FROM p.gh_created_at) as start_year,
    p.stargazers_count,
    p.archived
FROM github.nfcore_pipelines p
LEFT JOIN pipeline_first_releases pfr ON pfr.repo = p.name
WHERE NOT p.archived AND p.category = 'pipeline'
ORDER BY p.gh_created_at;
