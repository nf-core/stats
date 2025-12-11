---
title: GitHub
sidebar_position: 2
queries:
 - code/growth_gh_commits.sql
---

## GitHub organisation members

We use GitHub to manage all of the code written for nf-core. It's a fantastic platform and provides a huge number of tools. We have a GitHub organisation called nf-core which anyone can join: drop us a note here or anywhere and we'll send you an invite.

It's not required to be a member of the nf-core GitHub organisation to contribute. However, members get the nf-core logo listed on their profile page and full write-access to all nf-core repositories.

```github_members
select * from community_github_members order by 1 desc
```

<AreaChart 
    data={github_members} 
    x=timestamp
    y=total_github_members
/>

> By default, organisation membership is private. This is why you'll see a lower number if you visit the nf-core organisation page and are not a member.

## GitHub Contributors

Anybody can fork nf-core repositories and open a pull-request. Here we count how many different people have contributed at least one commit to an nf-core repository, or created or commented on an issue or pull-request.

```contributors_over_time
with all_timestamps as (
  select distinct timestamp
  from community_github_contributors
  order by timestamp
),
cumulative_contributors as (
  select 
    t.timestamp,
    count(distinct c.username) as number_of_contributors
  from all_timestamps t
  left join community_github_contributors c 
    on c.timestamp <= t.timestamp
  group by t.timestamp
)
select 
  timestamp,
  number_of_contributors
from cumulative_contributors
order by timestamp
```

<AreaChart
    data={contributors_over_time}
    x=timestamp
    y=number_of_contributors
/>


### Commits and Issues

<!-- commits, commits and issues, issues area chart -->


<AreaChart
    data={code_growth_gh_commits}
    x=month
    y=num_commits
/>

