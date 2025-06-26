USE nf_core_stats_bot;

select count(*) as total_gh_org_members from github.org_members;
