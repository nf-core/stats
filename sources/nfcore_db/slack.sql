USE nf_core_stats_bot;

SELECT DISTINCT * FROM slack.workspace_stats;
-- "timestamp","total_users","active_users","inactive_users"