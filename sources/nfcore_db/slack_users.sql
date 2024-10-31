USE nfcore_db;

SELECT
    to_timestamp(timestamp) as timestamp,
    inactive_users AS value,
    'inactive_users' AS category
from slack

UNION ALL

SELECT
    to_timestamp(timestamp) as timestamp,
    active_users AS value,
    'active_users' AS category
from slack
-- "timestamp","value","category"