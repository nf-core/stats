---
title: Pull Requests
sidebar_position: 2
---

When people contribute code to a nf-core repository, we conduct a "Pull request" - other members of the nf-core community review the proposed code and make suggestions, before merging into the main repository.

## Pull Requests Over Time

## Pull Request Response Times

Pull-requests are reviewed by the nf-core community - they can contain discussion on the code and can be merged and closed. We aim to be prompt with reviews and merging. Note that some PRs can be a simple type and so very fast to merge, others can be major pipeline updates.

<!-- TODO -->
<!-- <BigValue
    data={pr_response_times}
    value=median_hours
    title="Median PR Response Time (Hours)"
/> -->

```sql pr_response_times
select 
  label,
  time_to_close as value,
  'Time to merge/close' as category
from stats_static.github_pr_response_time

union all

select 
  label,
  time_to_first_response as value,
  'Time to First Response' as category
from stats_static.github_pr_response_time
```

<BarChart 
    data={pr_response_times}
    x=label
    y=value
    series=category
    type=grouped
    title="GitHub Pull Request Response Time"
    yAxisTitle="Percentage of PRs"
    colorPalette={[
        '#a4d5a6',  /* Green for Time to First Response */
        '#9d8ec7',  /* Purple for Time to Close */
    ]}
    yFmt=percent
    xType="category"
/>