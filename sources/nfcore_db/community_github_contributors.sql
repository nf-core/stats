USE nf_core_stats_bot;

select
author as username,
CAST(week_date as date) as timestamp,
SUM(week_commits) as week_commits,
SUM(week_additions) as week_additions,
SUM(week_deletions) as week_deletions
from github.contributor_stats
group by author, week_date;
