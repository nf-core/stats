---
title: Introduction
queries:
  - community/growth_gh_members.sql
  - community/growth_slack_users.sql
  - community/growth_gh_contributors.sql
  - code/growth_gh_repos.sql
  - code/growth_gh_released_repos.sql
  - code/growth_gh_commits.sql
  - code/growth_issues_and_prs.sql
  - code/growth_gh_prs.sql
  - code/growth_gh_issues.sql
---

On this page you can see the beating heart of nf-core - the size of our community and the output of our work.

## Community

The numbers below track our growth over the various channels that the nf-core community operates in.

<BigValue
  data={community_growth_gh_members}
  value=members
  title="GitHub Organisation Members"
  sparkline=month
  link="/community/github"
  minWidth=30%
/>

<BigValue
  data={community_growth_slack_users}
  value=members
  title="Active Slack Users"
  sparkline=month
  link='/community/slack'
  minWidth=30%
/>

<BigValue
  data={community_growth_gh_contributors}
  value=cumulative_contributors
  title="GitHub Contributors"
  sparkline=month
  link="/community/github"
  fmt=num0
  minWidth=30%
/>

<!-- TODO Add Bluesky followers -->

## Code Stats

Whilst we always prefer quality over quantity, these numbers reflect the work output from the nf-core community.

<BigValue
    data={code_growth_gh_repos}
    value=num_repos
    title="Pipelines"
    sparkline=month
    minWidth=30%
/>
<BigValue
    data={code_growth_gh_released_repos}
    value=num_repos
    title="Released Pipelines"
    sparkline=month
    minWidth=30%
/>
<BigValue
    data={code_growth_gh_commits}
    value=num_commits
    title="Commits"
    sparkline=month
    fmt=num0
    minWidth=30%
/>
<BigValue
    data={code_growth_gh_prs}
    value=num_prs
    title="Total Pull Requests"
    sparkline=month
    link="/code/pull_requests"
    minWidth=30%
/>
<BigValue
    data={code_growth_gh_issues}
    value=num_issues
    title="Total Issues"
    sparkline=month
    fmt=num0
    minWidth=30%
/>
