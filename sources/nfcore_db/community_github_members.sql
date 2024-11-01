USE nfcore_db;

select 
to_timestamp(timestamp) as timestamp,
gh_org_members as total_github_members
from gh_org_members;
