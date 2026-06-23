USE nf_core_stats_bot;

-- Daily snapshot of the AWS SES newsletter contact list.
-- One row per category per day (taking the max value for the day, in case the
-- pipeline ran more than once).
SELECT
    timestamp::date AS timestamp,
    MAX(subscribed) AS value,
    'subscribed' AS category
FROM ses.newsletter_stats
GROUP BY timestamp::date

UNION ALL

SELECT
    timestamp::date AS timestamp,
    MAX(pending) AS value,
    'pending' AS category
FROM ses.newsletter_stats
GROUP BY timestamp::date

ORDER BY 1 DESC

-- "timestamp","value","category"
