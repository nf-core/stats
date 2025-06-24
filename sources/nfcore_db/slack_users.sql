USE nf_core_stats_bot;

SELECT
    timestamp,
    inactive_users AS value,
    'inactive_users' AS category
from slack.workspace_stats

UNION ALL

SELECT
    timestamp,
    active_users AS value,
    'active_users' AS category
from slack.workspace_stats
-- "timestamp","value","category"