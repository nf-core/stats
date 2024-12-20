---
title: Introduction
queries:
  - community/growth_github_members.sql
  - community/growth_slack_users.sql
  - community/growth_gh_contributors.sql
  - community/growth_twitter.sql
  - code/growth_gh_repos.sql
  - code/growth_gh_prs.sql
  - code/growth_gh_commits.sql
  - code/growth_gh_issues.sql
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

## Code Stats

Whilst we always prefer quality over quantity, these numbers reflect the work output from the nf-core community.

NOTE: We're working on making these numbers live again. See [nf-core/stats#7](https://github.com/nf-core/stats/issues/7) for more details.

<BigValue
    data={code_growth_gh_repos}
    value=num_repos
    title="Repositories"
    sparkline=month
    comparison=growth_rate
    comparisonFmt=pct1
    comparisonTitle="vs. Last Month"
/>

<BigValue
    data={code_growth_gh_prs}
    value=num_prs
    title="Pull Requests"
    sparkline=month
    comparison=growth_rate
    comparisonFmt=pct1
    comparisonTitle="vs. Last Month"
/>

<BigValue
    data={code_growth_gh_commits}
    value=num_commits
    title="Commits"
/>

<BigValue
    data={code_growth_gh_issues}
    value=num_issues
    title="Issues"
    sparkline=month
    comparison=growth_rate
    comparisonFmt=pct1
    comparisonTitle="vs. Last Month"
/>
