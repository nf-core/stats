---
title: Pipeline Development Timeline
sidebar_position: 6
---

This timeline shows when each nf-core pipeline was in development and when they had their **first release**. It helps answer whether old pipelines are finally being released or if there are a lot of quick-fire pipelines being added and released quickly.

> **Note**: This analysis tracks time to **first release**, not the most recent release, to better understand the development lifecycle of each pipeline.

## Pipeline Lifecycle Timeline

Each pipeline's lifecycle is visualized with three complementary bar charts:
- **📊 Total Timeline** (nf-core blue): Complete tracked time from repository creation to today
- **🔨 Development Period** (amber): Time from initial commit to **first release** 
- **🚀 Post-Release Period** (nf-core green): Time since **first release** (ongoing development)

```sql lifecycle_summary
-- Show complete lifecycle for each pipeline with bar chart data
-- Now showing time to FIRST release, not last release
SELECT 
    pipeline_name,
    development_start::DATE as start_date,
    development_end::DATE as first_release_date,
    status,
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
ORDER BY development_start
```

<DataTable 
    title="Pipeline Lifecycle Summary"
    data={lifecycle_summary} 
    rows=20
    search=true
    compact=true
    rowShading=true
    wrapTitles=true
    defaultSort={[{ id: 'start_date', desc: true }]}
>
    <Column id=pipeline_name title="Pipeline" align=left />
    <Column id=start_date title="Development Started" fmt="mmm dd, yyyy" align=center />
         <Column id=total_days_tracked title="Total Timeline" contentType=bar barColor="#215EBE" align=center description="Complete timeline from start to today" />
     <Column id=dev_duration title="Dev Duration" contentType=bar barColor="#A16207" align=center description="Time to first release" />
     <Column id=release_duration title="Days Since First Release" contentType=bar barColor="#53A451" align=center description="Time since first release" />
    <Column id=first_release_date title="First Release" fmt="mmm dd, yyyy" align=center />
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
        WHEN development_days <= 90 THEN 'Quick (≤3 months)'
        WHEN development_days <= 365 THEN 'Medium (3-12 months)'
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
/>

## Year-over-Year Analysis

```sql yearly_analysis
-- Analysis by start year to see trends
SELECT 
    start_year,
    COUNT(*) as pipelines_started,
    COUNT(CASE WHEN status = 'Released' THEN 1 END) as pipelines_released,
    ROUND(AVG(development_days), 0) as avg_development_days,
    ROUND(COUNT(CASE WHEN status = 'Released' THEN 1 END) * 100.0 / COUNT(*), 1) as release_rate_percent
FROM nfcore_db.pipeline_timeline
WHERE start_year >= 2018
GROUP BY start_year
ORDER BY start_year DESC
```

<LineChart 
    data={yearly_analysis}
    x=start_year
    y=avg_development_days
    title="Average Development Time by Start Year"
    xAxisTitle="Year Pipeline Started"
    yAxisTitle="Average Development Days"
/>

<DataTable data={yearly_analysis} />

## Timeline View (Gantt-style)

```sql timeline_gantt_data
-- Create timeline data showing development periods
SELECT 
    pipeline_name,
    development_start,
    development_end,
    status,
    development_days,
    -- Create timeline positions for better visualization
    ROW_NUMBER() OVER (ORDER BY development_start) as timeline_position
FROM nfcore_db.pipeline_timeline
WHERE development_start >= '2018-01-01'
ORDER BY development_start
```

<ScatterPlot 
    data={timeline_gantt_data}
    x=development_start
    y=timeline_position
    size=development_days
    series=status
    title="Pipeline Development Timeline (Gantt View)"
    xAxisTitle="Development Start Date"
    yAxisTitle="Pipeline (by start order)"
    legend=true
/>

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

## Key Insights

Based on this timeline analysis using **first release dates**, you can see:

1. **Development Speed**: Time from initial commit to first stable release for each pipeline
2. **Historical Trends**: Whether development times to first release are getting shorter or longer over time
3. **Release Patterns**: Which pipelines took longest to reach their first release
4. **Quick vs Slow**: The distribution between quick-fire first releases and long development cycles
5. **Post-Release Activity**: How many total releases each pipeline has had since their first release

> **Important**: This analysis focuses on **first release** rather than most recent release to better understand the initial development effort required for each pipeline. Pipelines with many total releases indicate active ongoing development after the initial release. 