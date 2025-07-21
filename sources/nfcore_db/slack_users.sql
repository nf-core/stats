USE nf_core_stats_bot;

WITH aggregated_data AS (
    SELECT
        timestamp::date as timestamp,
        CASE 
            WHEN timestamp::date BETWEEN '2024-01-25' AND '2025-07-07' THEN 0
            ELSE MAX(active_users)  -- Take the maximum value for the day
        END AS value,
        'active_users' AS category
    from slack.workspace_stats
    GROUP BY timestamp::date
    UNION ALL

    SELECT
        timestamp::date as timestamp,
        CASE 
            WHEN timestamp::date BETWEEN '2024-01-25' AND '2025-07-07' THEN 0
            ELSE MAX(inactive_users)  -- Take the maximum value for the day
        END AS value,
        'inactive_users' AS category
    from slack.workspace_stats
    GROUP BY timestamp::date
)

SELECT * FROM aggregated_data

-- Add explicit 0 records for the data outage periods for proper chart visualization
UNION ALL
SELECT 
    UNNEST(generate_series('2023-04-28'::timestamp, '2023-11-07'::timestamp, INTERVAL '1 day'))::date as timestamp,
    0 as value,
    'active_users' as category
UNION ALL
SELECT 
    UNNEST(generate_series('2023-04-28'::timestamp, '2023-11-07'::timestamp, INTERVAL '1 day'))::date as timestamp,
    0 as value,
    'inactive_users' as category
UNION ALL
SELECT 
    UNNEST(generate_series('2024-01-25'::timestamp, '2025-07-07'::timestamp, INTERVAL '1 day'))::date as timestamp,
    0 as value,
    'active_users' as category
UNION ALL
SELECT 
    UNNEST(generate_series('2024-01-25'::timestamp, '2025-07-07'::timestamp, INTERVAL '1 day'))::date as timestamp,
    0 as value,
    'inactive_users' as category

-- "timestamp","value","category"