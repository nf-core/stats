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

### Views per day

<!-- https://github.com/nf-core/website/blob/33acd6a2fab2bf9251e14212ce731ef3232b5969/public_html/stats.php#L1423C29-L1423C42 -->

```views_by_day_2021
select * from nfcore_db.view_counts
```

<CalendarHeatmap 
    data={views_by_day_2021}
    date=timestamp
    value=sum_total_views_unique
    title="Visitors: All nf-core repositories"
    subtitle="Unique views per day"
    legend=true
/>
