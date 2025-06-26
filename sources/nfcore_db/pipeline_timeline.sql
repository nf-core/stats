USE nf_core_stats_bot;

-- Pipeline development timeline - showing development periods for each pipeline
SELECT 
    name as pipeline_name,
    gh_created_at as development_start,
    last_release_date as development_end,
    CASE 
        WHEN last_release_date IS NOT NULL THEN 'Released'
        ELSE 'In Development'
    END as status,
    -- Calculate development duration in days
    CASE 
        WHEN last_release_date IS NOT NULL THEN DATE_DIFF('day', gh_created_at, last_release_date)
        ELSE DATE_DIFF('day', gh_created_at, CURRENT_DATE)
    END as development_days,
    -- Extract year for grouping
    EXTRACT(year FROM gh_created_at) as start_year,
    stargazers_count,
    archived
FROM github.nfcore_pipelines 
WHERE NOT archived
ORDER BY gh_created_at; 