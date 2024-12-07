---
title: Pull Requests
sidebar_position: 2
queries:
  - prs_over_time: github/prs_over_time.sql
  - pr_response_times: github/pr_response_times.sql
---

When people contribute code to a nf-core repository, we conduct a "Pull request" - other members of the nf-core community review the proposed code and make suggestions, before merging into the main repository.

## Pull Requests Over Time

<LineChart
    data={prs_over_time}
    x=month
    y=num_prs
    title="Number of Pull Requests per Month"
/>

## Pull Request Response Times

Pull-requests are reviewed by the nf-core community - they can contain discussion on the code and can be merged and closed. We aim to be prompt with reviews and merging. Note that some PRs can be a simple type and so very fast to merge, others can be major pipeline updates.

<BigValue
    data={pr_response_times}
    value=median_hours
    title="Median PR Response Time (Hours)"
/>

<BarChart 
    data={pr_response_times}
    x=month
    y=median_hours
    title="Monthly Median PR Response Time (Hours)"
/>
