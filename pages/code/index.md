---
title: Code stats
sidebar_position: 2
queries:
  - code/growth_gh_repos.sql
  - code/growth_gh_prs.sql
  - code/growth_gh_commits.sql
---

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
    sparkline=month
    comparison=growth_rate
    comparisonFmt=pct1
    comparisonTitle="vs. Last Month"
/>

8.21K Issues
