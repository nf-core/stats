---
title: Core Repos
sidebar_position: 6
---

```sql core_repos_table
select
  *
from stats_static.core_repos
```

We're working on using live data for this table, but it's not quite ready yet. Check [this issue](https://github.com/nf-core/stats/issues/8) for updates.

<DataTable
data={core_repos_table}
defaultSort={[{ id: 'Stargazers', desc: true }]}
search=true
wrapTitles=true
totalRow=true
/>