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


<BigValue 
  data={community_growth_slack_users}
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
