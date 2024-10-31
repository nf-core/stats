---
title: Community
sidebar_position: 1
---

The numbers below track our growth over the various channels that the nf-core community operates in.

```total_slack_users
select count(*) from slack;
```

<Value data={total_slack_users} />
<!-- 8090 -->
Slack users

```total_gh_org_members
select * from community_total_gh_org_members;
```

<!-- 916 -->
<Value data={total_gh_org_members} />
GitHub organisation members

```total_gh_contributors
select * from community_total_gh_contributors;
```

<!-- 2418 -->
<Value data={total_gh_contributors} />
GitHub contributors

```total_twitter_followers
select count(*) from twitter;
```

<!-- 3705 -->
<Value data={total_twitter_followers} />
Twitter followers
