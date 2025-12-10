USE nf_core_stats_bot;

select count(*) as total_slack_users from slack.workspace_stats;
select count(*) as total_gh_org_members from github.org_members;
select count(*) as total_gh_contributors from github.contributor_stats;
