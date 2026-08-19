USE nf_core_stats_bot;

-- Daily snapshot of the AWS SES newsletter contact list.
-- One row per category per day (taking the max value for the day, in case the
-- pipeline ran more than once).
-- "inactive" are unconfirmed contacts too old to still count as pending; the
-- pipeline stops counting those as pending after 7 days.
SELECT timestamp::date AS timestamp, value, category
FROM (
    SELECT
        timestamp::date AS timestamp,
        MAX(subscribed) AS subscribed,
        MAX(pending) AS pending,
        MAX(total_contacts - subscribed - pending - unsubscribed) AS inactive
    FROM newsletter.subscriber_stats
    GROUP BY 1
)
UNPIVOT (value FOR category IN (subscribed, pending, inactive))
ORDER BY timestamp DESC

-- "timestamp","value","category"
