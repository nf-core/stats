## Hello Evidence

This is a new page in Evidence.

```view_counts_summary
select * from nfcore_db.view_counts
```

<DataTable data={view_counts_summary} />

```view_counts_summary_top100
select
*
from nfcore_db.view_counts
order by sum_total_views desc
limit 100
```

<DataTable data={view_counts_summary_top100}>
   <Column id=timestamp title="Date"/>
   <Column id=sum_total_views title = "Total Views" />
   <Column id=sum_total_views_unique title = "Total Unique Views" />
</DataTable>
