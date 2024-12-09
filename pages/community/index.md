---
title: Community
sidebar_position: 1
queries:
  - community/growth_github_members.sql
  - community/growth_slack_users.sql
---

The numbers below track our growth over the various channels that the nf-core community operates in.

<BigValue 
  data={community_growth_github_members} 
  value=members
  title="GitHub Organisation Members"
  sparkline=month
  comparison=growth_rate
  comparisonFmt=pct1
  comparisonTitle="vs. Last Month"
  link="/community/github"
/>

```sql growth_slack_users
select
    date_trunc('month', to_timestamp(timestamp)::timestamp) as month,
    total_users as members,
    lag(total_users) over (order by date_trunc('month', to_timestamp(timestamp)::timestamp)) as prev_month_members,
    round(cast((total_users / nullif(lag(total_users) over (order by date_trunc('month', to_timestamp(timestamp)::timestamp)), 0) - 1) * 100 as numeric), 1) as growth_rate
from nfcore_db.slack
where to_timestamp(timestamp)::timestamp >= '2020-01-01'
group by 1, 2, date_trunc('month', to_timestamp(timestamp)::timestamp), total_users
order by date_trunc('month', to_timestamp(timestamp)::timestamp) desc
```

<BigValue 
  data={growth_slack_users}
  value=members
  title="Slack Users"
  sparkline=month
  comparison=growth_rate
  comparisonFmt=pct1
  comparisonTitle="vs. Last Month"
  link='/community/slack'
/>

<!-- <BigValue 
  data={total_gh_contributors}
  title="GitHub Contributors"
/>

<BigValue 
  data={total_twitter_followers}
  value="count"
  title="Twitter Followers"
/> -->
