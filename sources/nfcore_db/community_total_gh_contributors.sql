USE nf_core_stats_bot;

select count(*) as total_gh_contributors from github.contributor_stats;
