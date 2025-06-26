USE nf_core_stats_bot;

select 
author as username,
week_date as timestamp, -- FIXME change column name in md
from github.contributor_stats;
