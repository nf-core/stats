USE nf_core_stats_bot;

-- Pipeline development timeline - showing development periods for each pipeline
-- Uses first_release_date/number_of_releases collected directly by the GitHub pipeline
-- (previously joined against the external nf_core_dev.tap_github.releases
SELECT
    p.name as pipeline_name,
    p.gh_created_at as development_start,
    p.first_release_date as development_end,
    COALESCE(p.number_of_releases, 0) as total_releases,
    CASE
        WHEN p.first_release_date IS NOT NULL THEN 'Released'
        ELSE 'In Development'
    END as status,
    -- Calculate development duration in days to FIRST release
    CASE
        WHEN p.first_release_date IS NOT NULL THEN DATE_DIFF('day', p.gh_created_at, p.first_release_date)
        ELSE DATE_DIFF('day', p.gh_created_at, CURRENT_DATE)
    END as development_days,
    -- Extract year for grouping
    EXTRACT(year FROM p.gh_created_at) as start_year,
    p.stargazers_count,
    p.archived
FROM github.nfcore_pipelines p
WHERE NOT p.archived AND p.category = 'pipeline'
ORDER BY p.gh_created_at;
