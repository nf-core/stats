USE nf_core_stats_bot;

SELECT * EXCLUDE (description, last_release_date),
       CASE
         WHEN last_release_date IS NULL THEN 'Not released'
         ELSE CAST(last_release_date AS VARCHAR)
       END AS last_release_date
FROM github.nfcore_pipelines;
