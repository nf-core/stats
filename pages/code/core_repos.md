---
title: Core Repos
sidebar_position: 6
---

```sql core_repos_table
select
  *
from nfcore_db.core_repos
```

We have several repositories that are not pipelines, but contain code for everything around nf-core (including this page itself).

<DataTable
data={core_repos_table}
defaultSort={[{ id: 'stargazers_count', desc: true }]}
search=true
wrapTitles=true
totalRow=true
/>