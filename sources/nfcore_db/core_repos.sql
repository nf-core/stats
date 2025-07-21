USE nf_core_stats_bot;

SELECT * EXCLUDE (last_release_date)
FROM github.nfcore_pipelines WHERE category = 'core';
