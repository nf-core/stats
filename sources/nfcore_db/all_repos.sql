USE nf_core_stats_bot;

SELECT * REPLACE (COALESCE(description, '') AS description) EXCLUDE (description) FROM github.nfcore_pipelines;
