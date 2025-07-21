SELECT p.*
FROM github.nfcore_pipelines p
WHERE p._dlt_id NOT IN (
  SELECT t._dlt_parent_id 
  FROM github.nfcore_pipelines__topics t 
  WHERE t.value != 'pipeline'
);
