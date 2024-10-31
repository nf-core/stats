USE nfcore_db;

select count(*) as total_slack_users from slack;
select count(*) as total_gh_org_members from gh_org_members;
select count(*) as total_gh_contributors from gh_contributors;
select count(*) as total_twitter_followers from twitter;

