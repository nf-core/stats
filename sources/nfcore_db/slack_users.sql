USE nf_core_stats_bot;

SELECT
    timestamp::date as timestamp,
    CASE 
        WHEN timestamp::date BETWEEN '2024-01-25' AND '2025-07-07' THEN 0
        ELSE active_users 
    END AS value,
    'active_users' AS category
from slack.workspace_stats
UNION ALL

SELECT
    timestamp::date as timestamp,
    CASE 
        WHEN timestamp::date BETWEEN '2024-01-25' AND '2025-07-07' THEN 0
        ELSE inactive_users 
    END AS value,
    'inactive_users' AS category
from slack.workspace_stats

-- Add explicit 0 records at the boundary dates for proper chart visualization
UNION ALL
SELECT '2024-01-25'::date as timestamp, 0 as value, 'active_users' as category
UNION ALL
SELECT '2024-01-25'::date as timestamp, 0 as value, 'inactive_users' as category
UNION ALL
SELECT '2025-07-07'::date as timestamp, 0 as value, 'active_users' as category
UNION ALL
SELECT '2025-07-07'::date as timestamp, 0 as value, 'inactive_users' as category

-- "timestamp","value","category"