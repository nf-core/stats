USE nf_core_stats_bot;

SELECT
    pipeline_name,
    COUNT(DISTINCT author) AS number_of_contributors
FROM github.contributor_stats
GROUP BY pipeline_name
ORDER BY pipeline_name;
