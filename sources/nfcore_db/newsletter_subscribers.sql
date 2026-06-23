USE nf_core_stats_bot;

-- Daily snapshot of the AWS SES newsletter contact list.
-- One row per category per day (taking the max value for the day, in case the
-- pipeline ran more than once).
SELECT timestamp::date AS timestamp, value, category
FROM (
    SELECT timestamp::date AS timestamp, MAX(subscribed) AS subscribed, MAX(pending) AS pending
    FROM ses.newsletter_stats
    GROUP BY 1
)
UNPIVOT (value FOR category IN (subscribed, pending))
ORDER BY timestamp DESC

-- "timestamp","value","category"
