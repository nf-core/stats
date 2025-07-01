---
title: Contributors
sidebar_position: 4
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

