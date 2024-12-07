WITH first_responses AS (
    SELECT
        pr_id,
        created_at,
        date_trunc('month', created_at) as month,
        EXTRACT(EPOCH FROM (first_response_at - created_at))/3600 as hours_to_response
    FROM github_pull_requests
    WHERE 
        org = 'nf-core'
        AND first_response_at IS NOT NULL
)
SELECT
    month,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY hours_to_response) as median_hours,
    COUNT(*) as num_prs
FROM first_responses
GROUP BY 1
ORDER BY 1 