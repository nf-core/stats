---
title: Pull Requests
sidebar_position: 2
---

When people contribute code to a nf-core repository, we conduct a "Pull request" - other members of the nf-core community review the proposed code and make suggestions, before merging into the main repository.

## Pull Requests Over Time

```sql pull_requests_over_time
select timestamp, -closed_merged as "Closed / Merged", open as "Open"
from nfcore_db.issues_and_prs_over_time
where type = 'pr'
```

```sql pull_requests_cumulative
select
    timestamp,
    round(sum(closed_merged) over (order by timestamp)) as "Closed / Merged",
    round(sum(open) over (order by timestamp)) as "Open",
    round(sum(closed_merged + open) over (order by timestamp)) as "Total"
from nfcore_db.issues_and_prs_over_time
where type = 'pr'
```

<Tabs>

<Tab label="Per week">

<LineChart
data={pull_requests_over_time}
x=timestamp
y={["Closed / Merged", "Open"]}
title="GitHub Pull Requests over time"
yAxisTitle="Number of Pull Requests"
/>

</Tab>

<Tab label="Cumulative">

<LineChart
data={pull_requests_cumulative}
x=timestamp
y={[ "Total"]}
seriesColors={{"Total": "warning"}}
yLog=true
title="Cumulative GitHub Pull Requests over time"
yAxisTitle="Number of Pull Requests"
/>

</Tab>

</Tabs>

## Pull Request Response Times

Pull-requests are reviewed by the nf-core community - they can contain discussion on the code and can be merged and closed. We aim to be prompt with reviews and merging. Note that some PRs can be a simple type and so very fast to merge, others can be major pipeline updates.

The histogram below shows the distribution of response times split between pipeline repositories and core infrastructure repositories. Pipeline repos are those listed in the nf-core pipelines registry, while core repos include tools, website, and other infrastructure. This comparison helps identify if there are different response patterns between the scientific pipelines and the supporting infrastructure.

```sql pr_response_times
select *
from nfcore_db.response_times
where type = 'pr'
```

<BarChart
data={pr_response_times}
x=label
y={["pipeline_time_to_close", "core_time_to_close"]}
sort=false
type=grouped
title="GitHub Pull Request Response Time by Repository Type"
subtitle="Distribution of close times for pipeline repos vs core infrastructure repos"
yAxisTitle="Percentage of PRs"
yFmt=pct
xType="category"
xGridLines=true
xLabelWrap=true
legendPosition="bottom"
/>

## Who opened them

Each person is counted once per pull request they opened, across the full issue history. GitHub App accounts, nf-core-bot, and Copilot are left out.

```sql pr_authors
SELECT contributor, prs_opened
FROM nfcore_db.pr_authors
```

<DataTable
data={pr_authors}
search=true
rows=25
defaultSort={[{ id: 'prs_opened', desc: true }]}>

    <Column id="contributor" title="Contributor" align="left" contentType="html"/>
    <Column id="prs_opened" title="PRs opened" align="right"/>

</DataTable>

## Who reviewed them

A person is counted once per pull request they reviewed. Pending reviews are skipped. GitHub App accounts, nf-core-bot, and Copilot are left out.

The pipeline loads this with one GraphQL search per page of pull requests, rather than one REST call per pull request. Every run re-reads pull requests updated in the last two days, then walks older update dates back to January 2018, a few weeks at a time. A pull request contributes its full review history when its update week is scanned, so recent pull requests bring their older reviews along. Reviews on pull requests that have been quiet since then fill in as the walk proceeds.

```sql pr_reviewers
SELECT contributor, prs_reviewed
FROM nfcore_db.pr_reviewers
```

<DataTable
data={pr_reviewers}
search=true
rows=25
defaultSort={[{ id: 'prs_reviewed', desc: true }]}>

    <Column id="contributor" title="Contributor" align="left" contentType="html"/>
    <Column id="prs_reviewed" title="PRs reviewed" align="right"/>

</DataTable>

<LastRefreshed prefix="Data last updated"/>
