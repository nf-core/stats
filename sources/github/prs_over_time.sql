SELECT 
    date_trunc('month', created_at) as month,
    count(*) as num_prs
FROM github_pull_requests
WHERE org = 'nf-core'
GROUP BY 1
ORDER BY 1 