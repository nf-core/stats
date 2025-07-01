USE nf_core_stats_bot;

select distinct
author as username,
week_date as timestamp,
SUM(week_commits) as week_commits,
SUM(week_additions) as week_additions,
SUM(week_deletions) as week_deletions
from github.contributor_stats
group by author, week_date;
