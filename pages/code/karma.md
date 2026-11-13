---
title: Karma
sidebar_position: 3
---

Karma points reward the work that keeps nf-core going, reviews included. They count since 13 November 2026, when review collection started.

| Activity                                       | Points |
| ---------------------------------------------- | ------ |
| Merged pull request                            | 3      |
| Review of someone else's pull request (per PR) | 2      |
| Opened issue                                   | 1      |

Bot and LLM agent accounts are excluded.

```sql karma
SELECT
    '<div style="display: flex; align-items: center;"><img src="https://github.com/' || login || '.png?size=80" style="width: 40px; height: 40px; border-radius: 50%; margin-right: 8px;" alt="' || login || '" /><a href="https://github.com/' || login || '" target="_blank" style="text-decoration: none;">@' || login || '</a></div>' AS contributor,
    karma,
    prs_merged,
    reviews,
    issues
FROM nfcore_db.karma
```

<DataTable
data={karma}
search=true
rows=25
defaultSort={[{ id: 'karma', desc: true }]}>

    <Column id="contributor" title="Contributor" align="left" contentType="html"/>
    <Column id="karma" title="Karma" align="right"/>
    <Column id="prs_merged" title="Merged PRs" align="right"/>
    <Column id="reviews" title="Reviews" align="right"/>
    <Column id="issues" title="Issues" align="right"/>

</DataTable>

<LastRefreshed prefix="Data last updated"/>
