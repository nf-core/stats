USE nf_core_stats_bot;

SELECT * EXCLUDE (description, last_release_date) 
FROM github.nfcore_pipelines 
WHERE NOT list_contains(topics, 'pipeline');
