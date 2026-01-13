---
name: Add Evidence Page
description: Create new Evidence.dev dashboard page with charts and tables
---

# Add Evidence Page

## When to Use
- Adding new visualization/dashboard
- Creating charts for existing DLT data

## File Structure
```
├── pages/<category>/<page>.md    # Page with charts
└── sources/nfcore_db/<query>.sql # SQL data source
```

## Page Template

```markdown
---
title: Page Title
sidebar_position: 1
---

Brief description of what this page shows.

```sql summary_query
SELECT COUNT(*) as total FROM nfcore_db.<table_name>
```

<BigValue
  data={summary_query}
  value=total
  title="Total Items"
/>

```sql time_series
SELECT
  date_trunc('week', created_at) as week,
  COUNT(*) as count
FROM nfcore_db.<table_name>
GROUP BY 1
ORDER BY 1
```

<LineChart
  data={time_series}
  x=week
  y=count
  title="Items Over Time"
/>

<LastRefreshed prefix="Data last updated"/>
```

## SQL Source Template

File: `sources/nfcore_db/<query>.sql`
```sql
SELECT
  column1,
  column2,
  COUNT(*) as count
FROM <table_name>
GROUP BY 1, 2
ORDER BY count DESC
```

## Component Reference

| Component | Use Case | Key Props |
|-----------|----------|-----------|
| BigValue | KPI cards | `data`, `value`, `title`, `sparkline`, `fmt` |
| LineChart | Time series | `data`, `x`, `y`, `title`, `yAxisTitle` |
| AreaChart | Stacked trends | `data`, `x`, `y`, `series`, `seriesColors` |
| BarChart | Comparisons | `data`, `x`, `y`, `type=grouped`, `yFmt` |
| DataTable | Tabular data | `data`, `search`, `totalRow`, `<Column>` |
| CalendarHeatmap | Daily heatmap | `data`, `date`, `value` |
| Tabs/Tab | Tabbed views | `<Tab label="Name">` |
| DateRange | Date filter | `name`, `data`, `dates`, `defaultValue` |

## DataTable with Columns

```svelte
<DataTable data={query} search=true totalRow=true>
  <Column id="name" title="Name"/>
  <Column id="count" title="Count" align="right"/>
  <Column id="url" contentType=link linkLabel="View"/>
  <Column id="score" contentType=colorscale colorScale=negative/>
</DataTable>
```

## Stacked AreaChart with Colors

```svelte
<AreaChart
  data={query}
  x=date
  y={["category_a", "category_b", "category_c"]}
  seriesColors={['#2ecc71', '#f39c12', '#e74c3c']}
  title="Distribution Over Time"
/>
```

## Date Filtering Pattern

```markdown
<DateRange name="date_range" data={base_query} dates=timestamp defaultValue="Last 90 Days"/>

```sql filtered_query
SELECT * FROM nfcore_db.<table>
WHERE timestamp >= '${inputs.date_range.start}'
  AND timestamp <= '${inputs.date_range.end}'
```

<LineChart data={filtered_query} x=timestamp y=value/>
```

## Testing

```bash
npm run dev
# Open http://localhost:3000/path/to/page
```

## Checklist

1. [ ] Create SQL source in `sources/nfcore_db/`
2. [ ] Create page in `pages/<category>/`
3. [ ] Add frontmatter (title, sidebar_position)
4. [ ] Add summary metrics (BigValue)
5. [ ] Add time series chart (LineChart/AreaChart)
6. [ ] Add detail table (DataTable)
7. [ ] Test with `npm run dev`
