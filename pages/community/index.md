---
title: Community
sidebar_position: 1
queries:
  - community_growth.sql
---

The numbers below track our growth over the various channels that the nf-core community operates in.

<BigValue 
  data={community_growth} 
  value=members
  title="GitHub Organisation Members"
  sparkline=month
  comparison=growth_rate
  comparisonFmt=pct1
  comparisonTitle="vs. Last Month"
  link="/community/github"
/>

<!-- <BigValue 
  data={total_slack_users}
  value="count"
  title="Slack Users"
  link='/community/slack'
/> -->

<!-- <BigValue 
  data={total_gh_contributors}
  title="GitHub Contributors"
/> -->

<!-- <BigValue 
  data={total_twitter_followers}
  value="count"
  title="Twitter Followers"
/> -->
