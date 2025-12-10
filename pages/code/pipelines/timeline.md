---
title: Pipeline Development Timeline
sidebar_position: 6
---

This timeline shows when each nf-core pipeline was in development and when they had their **first release**. It helps answer whether old pipelines are finally being released or if there are a lot of quick-fire pipelines being added and released quickly.

> **Note**: This analysis tracks time to **first release**, not the most recent release, to better understand the development lifecycle of each pipeline.

## Pipeline Lifecycle Timeline

Each pipeline's lifecycle is visualized with three complementary bar charts:

- **📊 Total Timeline**: Complete tracked time from repository creation to today
- **🔨 Development Period**: Time from initial commit to **first release**
- **🚀 Post-Release Period**: Time since **first release** (ongoing development)

```sql lifecycle_summary
-- Show complete lifecycle for each pipeline with bar chart data
-- Now showing time to FIRST release, not last release
SELECT
    pipeline_name,
    development_start::DATE as start_date,
    CASE
        WHEN status = 'Released' AND development_end IS NOT NULL
        THEN STRFTIME(development_end::DATE, '%b %Y')
        ELSE '—'
    END as first_release_date,
    status,
    -- Add grouping columns
    EXTRACT(YEAR FROM development_start) as start_year,
    development_days,
    CASE
        WHEN status = 'Released' AND development_end IS NOT NULL
        THEN DATE_DIFF('day', development_end, CURRENT_DATE)
        ELSE 0
    END as days_since_first_release,
    CASE
        WHEN status = 'Released' AND development_end IS NOT NULL
        THEN development_days + DATE_DIFF('day', development_end, CURRENT_DATE)
        ELSE development_days
    END as total_days_tracked,
    -- Bar chart values for visualization
    development_days as dev_duration,
    CASE
        WHEN status = 'Released' AND development_end IS NOT NULL
        THEN DATE_DIFF('day', development_end, CURRENT_DATE)
        ELSE 0
    END as release_duration
FROM nfcore_db.pipeline_timeline
WHERE development_start >= '2017-01-01'
ORDER BY start_year DESC, development_start DESC
```

<DataTable
title="Pipeline Development Timeline by Year"
data={lifecycle_summary}
search=true
compact=true
rowShading=true
wrapTitles=true
groupBy=start_year
groupType=accordion
groupsOpen=true
subtotals=false
colorPalette={["#accent", "warning", "primary"]}

>

    <Column id=pipeline_name title="Pipeline" align=left/>
    <Column id=start_date title="Development Started" fmt="mmm yyyy" align=center />
    <Column id=total_days_tracked title="📊 Total Timeline in days" contentType=bar backgroundColor="base-300" align=center description="Complete timeline from start to today" />
    <Column id=dev_duration title="🔨 Dev Duration" contentType=bar labelColor="black"  backgroundColor="base-300" align=center description="Time to first release"  />
    <Column id=release_duration title="🚀 Days Since First Release" contentType=bar  backgroundColor="base-300" align=center description="Time since first release" />
    <Column id=first_release_date title="First Release" align=center />
    <Column id=status title="Status" align=center />

</DataTable>

## Development vs Released Time Analysis

```sql duration_stats
-- Calculate statistics about development vs time since first release
SELECT
    status,
    COUNT(*) as pipeline_count,
    ROUND(AVG(development_days), 0) as avg_development_days,
    ROUND(AVG(CASE WHEN status = 'Released' THEN DATE_DIFF('day', development_end, CURRENT_DATE) END), 0) as avg_days_since_first_release,
    ROUND(MEDIAN(development_days), 0) as median_development_days,
    MIN(development_days) as min_development_days,
    MAX(development_days) as max_development_days,
    -- Note: total_releases temporarily removed due to query issues
FROM nfcore_db.pipeline_timeline
WHERE development_start >= '2018-01-01'
GROUP BY status
ORDER BY avg_development_days DESC
```

<DataTable data={duration_stats} />

```sql quick_vs_slow
-- Categorize pipelines by development speed
SELECT
    CASE
        WHEN development_days <= 180 THEN 'Quick (≤6 months)'
        WHEN development_days <= 365 THEN 'Medium (6-12 months)'
        WHEN development_days <= 730 THEN 'Slow (1-2 years)'
        ELSE 'Very Long (>2 years)'
    END as development_speed,
    COUNT(*) as count,
    ROUND(AVG(development_days), 0) as avg_days
FROM nfcore_db.pipeline_timeline
GROUP BY 1
ORDER BY avg_days
```

### Development Speed Distribution

<BarChart
    data={quick_vs_slow}
    x=development_speed
    y=count
    title="Pipeline Development Speed Distribution"
    xAxisTitle="Development Speed Category"
    yAxisTitle="Number of Pipelines"
    sort=false
/>

## Year-over-Year Analysis

```sql yearly_analysis
-- Analysis by start year to see trends - IMPROVED VERSION
SELECT
    CAST(start_year AS INTEGER) as start_year_int,
    DATE_TRUNC('year', MAKE_DATE(CAST(start_year AS INTEGER), 1, 1)) as start_year,
    COUNT(*) as pipelines_started,
    COUNT(CASE WHEN status = 'Released' THEN 1 END) as pipelines_released,
    COUNT(CASE WHEN status != 'Released' THEN 1 END) as pipelines_in_development,
    -- Only calculate averages for pipelines that have been released to avoid skewing data
    CAST(ROUND(AVG(CASE WHEN status = 'Released' THEN development_days END), 0) AS INTEGER) as avg_development_days_released,
    -- Show average for all pipelines (including in-development) for comparison
    CAST(ROUND(AVG(development_days), 0) AS INTEGER) as avg_development_days_all,
    -- Calculate median for better central tendency
    CAST(ROUND(MEDIAN(CASE WHEN status = 'Released' THEN development_days END), 0) AS INTEGER) as median_development_days_released,
    -- Calculate release rate as a percentage of total pipelines
    ROUND(COUNT(CASE WHEN status = 'Released' THEN 1 END)/ COUNT(*), 1) as release_rate_percent,
    -- Add min/max for context
    MIN(CASE WHEN status = 'Released' THEN development_days END) as min_dev_days_released,
    MAX(CASE WHEN status = 'Released' THEN development_days END) as max_dev_days_released,
    -- Filter out incomplete recent years for more accurate trending
    CASE
        WHEN start_year >= 2024 THEN 'Recent (Incomplete)'
        WHEN start_year >= 2020 THEN 'Recent'
        ELSE 'Historical'
    END as time_period
FROM nfcore_db.pipeline_timeline
WHERE start_year >= 2018
  AND start_year <= EXTRACT(YEAR FROM CURRENT_DATE) -- Don't include future years
GROUP BY start_year
ORDER BY start_year
```

### Development Time Trends

<Note>
Recent years (2024+) show lower average days until first release because many pipelines are still in development. The chart below shows trends for **released pipelines only** to avoid this bias.
</Note>

<LineChart
    data={yearly_analysis}
    x=start_year
    y=avg_development_days_released
    title="Average Days Until First Release by Start Year"
    subtitle="Based on pipelines that have actually been released"
    xAxisTitle="Year Pipeline Development Started"
    yAxisTitle="Average Days Until First Release"
    yMin=0
    xFmt="yyyy"
    yFmt="0"
/>

<DataTable
data={yearly_analysis}
title="Year-over-Year Pipeline Development Analysis"
compact=true
rowShading=true

>

    <Column id=start_year title="Year" align=center fmt="yyyy" />
    <Column id=pipelines_started title="Started Total" align=center />
    <Column id=pipelines_released title="Released" align=center />
    <Column id=pipelines_in_development title="In Dev" align=center />
    <Column id=avg_development_days_released title="Avg Days Until First Release" align=center fmt="#,##0" />
    <Column id=median_development_days_released title="Median Days Until First Release" align=center fmt="#,##0" />
    <Column id=release_rate_percent title="Percent Released by now" align=right fmt="0.0%" />
    <Column id=min_dev_days_released title="Min Days Until Release" align=right fmt="#,##0" />
    <Column id=max_dev_days_released title="Max Days Until Release" align=right fmt="#,##0" />
    <Column id=time_period title="Period" align=center />

</DataTable>

## Development Start vs Duration Analysis

```sql scatter_data
-- Scatter plot data showing start vs duration
SELECT
    development_start,
    development_days,
    status,
    pipeline_name,
    start_year
FROM nfcore_db.pipeline_timeline
WHERE development_start >= '2018-01-01'
```

<ScatterPlot
    data={scatter_data}
    x=development_start
    y=development_days
    series=status
    title="Development Start Date vs Duration"
    xAxisTitle="Development Start Date"
    yAxisTitle="Development Duration (Days)"
    legend=true
/>

<Alert status="warning">
This analysis focuses on <strong>first release</strong> rather than most recent release to better understand the initial development effort required for each pipeline.
Pipelines with many total releases indicate active ongoing development after the initial release.
</Alert>
