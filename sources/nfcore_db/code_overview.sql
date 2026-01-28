USE nf_core_stats_bot;

select
    count(*) as num_pipelines
from github.nfcore_pipelines
-- TODO issues
-- TODO prs
-- TODO commits
-- TODO contributors
