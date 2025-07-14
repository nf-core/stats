---
title: Contributors
sidebar_position: 2
queries:
  - code/contributors_leaderboard.sql
---

## Contributor Leaderboard

We value each and every contribution to nf-core, no matter how small. However, that doesn't mean that we can't get competitive!

Here are the latest stats of who has contributed the greatest number of commits. The yellow bars show "core repositories" - repositories that are not pipelines (such as the code for this website!). A list of these repositories can be found below.

Remember:

- There is more to contributing than commits! We're not counting issue comments, reviews or anything else here.
- People merging pull-requests get bonus commit counts from those merge commits.
- Some people commit often, others not so much. So it's not a perfect representation of amount of work - just a bit of fun!
- master branch only, and all of the other caveats..


<DataTable 
    data={code_contributors_leaderboard}
    search=true
    wrapTitles=true
    defaultSort={[{ id: 'total_commits', desc: true }]}
>
    <Column id="contributor" title="Contributor" align="left" contentType="html"/>
    <Column id="total_commits" title="Total Commits" align="right"/>
    <Column id="total_additions" title="Total Additions" align="right"/>
    <Column id="total_deletions" title="Total Deletions" align="right"/>
    <Column id="first_commit_week" title="First Commit Week" align="right"/>
    <Column id="last_commit_week" title="Last Commit Week" align="right"/>
</DataTable>

```sql time_range
SELECT 
    timestamp
FROM nfcore_db.community_github_contributors
WHERE week_commits > 0
```

<DateRange
    name="date_range"
    data={time_range}
    dates="timestamp"
    defaultValue="All Time"
    presetRanges={['Last 7 Days', 'Last Month', 'Last 3 Months', 'Last 6 Months', 'Last Year', 'All Time']}
/>

```sql top_contributors_commits_filtered
SELECT 
    username,
    CAST(timestamp AS DATE) AS timestamp,
    week_commits
FROM nfcore_db.community_github_contributors
WHERE username IN (SELECT author FROM nfcore_db.gh_contributors ORDER BY total_sum_commits DESC LIMIT 10) 
AND week_commits > 0
AND timestamp >= '${inputs.date_range.start}' 
AND timestamp <= '${inputs.date_range.end}'
ORDER BY timestamp, username
```

```sql top_contributors_additions_filtered
SELECT 
    username,
    CAST(timestamp AS DATE) AS timestamp,
    week_additions
FROM nfcore_db.community_github_contributors
WHERE username IN (SELECT author FROM nfcore_db.gh_contributors ORDER BY total_sum_additions DESC LIMIT 10) 
AND week_additions > 0
AND timestamp >= '${inputs.date_range.start}' 
AND timestamp <= '${inputs.date_range.end}'
ORDER BY timestamp, username
```

```sql top_contributors_deletions_filtered
SELECT 
    username,
    CAST(timestamp AS DATE) AS timestamp,
    -1 * week_deletions as week_deletions
FROM nfcore_db.community_github_contributors
WHERE username IN (SELECT author FROM nfcore_db.gh_contributors ORDER BY total_sum_deletions DESC LIMIT 10) 
AND week_deletions > 0
AND timestamp >= '${inputs.date_range.start}' 
AND timestamp <= '${inputs.date_range.end}'
ORDER BY timestamp, username
```


<Tabs>
    <Tab label="Commits">

<LineChart
    data={top_contributors_commits_filtered}
    x="timestamp"
    y="week_commits"
    series="username"
    sort=false
    yMin=0
/>

</Tab>
<Tab label="Additions">

<LineChart
    data={top_contributors_additions_filtered}
    x="timestamp"
    y="week_additions"
    series="username"
    sort=false
/>

</Tab>
<Tab label="Deletions">

<LineChart
    data={top_contributors_deletions_filtered}
    x="timestamp"
    y="week_deletions"
    series="username"
    sort=false
/>

</Tab>
</Tabs>
