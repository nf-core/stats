---
title: Core Repos
sidebar_position: 6
---

```sql core_repos_table
select
  name,
  description,
  gh_created_at,
  gh_updated_at,
  stargazers_count,
  watchers_count,
  forks_count,
  open_issues_count,
  topics,
  archived,
  default_branch,
  'https://github.com/nf-core/' || name as github_url
from nfcore_db.core_repos
where archived = false
```

We have several repositories that are not pipelines, but contain code for everything around nf-core (including this page itself).

<DataTable
data={core_repos_table}
defaultSort={[{ id: 'stargazers_count', desc: true }]}
search=true
wrapTitles=true
totalRow=true
link=github_url
>
</DataTable>
