USE nfcore_db;

select 
username,
to_timestamp(gh_id) as timestamp, -- FIXME change column name in md
from gh_contributors;
