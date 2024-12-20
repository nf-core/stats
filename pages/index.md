---
title: Introduction
queries:
  - community/growth_github_members.sql
  - community/growth_slack_users.sql
  - community/growth_gh_contributors.sql
  - community/growth_twitter.sql
---

On this page you can see the beating heart of nf-core - the size of our community and the output of our work.

## Community

The numbers below track our growth over the various channels that the nf-core community operates in.

NOTE: These numbers are not updated in real-time yet.

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

<BigValue
  data={community_growth_gh_contributors}
  value=members
  title="GitHub Contributors"
  link="/community/github"
/>

<BigValue
  data={community_growth_twitter}
  value=followers
  title="Twitter Followers"
  sparkline=month
  comparison=growth_rate
  comparisonFmt=pct1
  comparisonTitle="vs. Last Month"
  link="/community/twitter"
/>

<!-- TODO Add Bluesky followers -->
