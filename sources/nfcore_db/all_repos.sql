USE nfcore_db;

-- FIXME Error: Unsupported object type: null
SELECT * EXCLUDE (description, last_release_date) FROM nfcore_pipelines;
