USE nf_core_stats_bot;

select 
to_timestamp(timestamp) as timestamp,
num_members as total_github_members
from github.org_members 
