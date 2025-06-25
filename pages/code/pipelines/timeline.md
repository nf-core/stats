---
title: Pipeline Development Timeline
sidebar_position: 6
---

This timeline shows when each nf-core pipeline was in development and when they were released. It helps answer whether old pipelines are finally being released or if there are a lot of quick-fire pipelines being added and released quickly.

## Pipeline Development Timeline (Gantt-style)

```sql pipeline_timeline_data
-- Get timeline data for visualization
SELECT 
    pipeline_name,
    development_start,
    development_end,
    status,
    development_days,
    start_year,
    -- Create a label for the chart
    pipeline_name || ' (' || development_days || ' days)' as pipeline_label
FROM nfcore_db.pipeline_timeline
ORDER BY development_start
```

```sql timeline_chart_data
-- Transform data for timeline visualization - vertical bar chart showing development duration
SELECT 
    pipeline_name,
    development_days as duration,
    status,
    start_year,
    DATE_TRUNC('quarter', development_start) as start_quarter,
    pipeline_name || ' (' || 
    CASE 
        WHEN status = 'Released' THEN development_days || ' days to release)'
        ELSE development_days || ' days in dev)'
    END as label
FROM nfcore_db.pipeline_timeline
WHERE development_start >= '2018-01-01'
ORDER BY development_start
```

<BarChart 
    data={timeline_chart_data}
    x=pipeline_name
    y=duration
    series=status
    title="Pipeline Development Duration"
    xAxisTitle="Pipeline"
    yAxisTitle="Development Duration (Days)"
    legend=true
/>

```sql gantt_style_data
-- Create a timeline view by quarters to simulate Gantt chart
SELECT 
    DATE_TRUNC('quarter', development_start)::TEXT as quarter,
    COUNT(*) as pipelines_started,
    COUNT(CASE WHEN status = 'Released' THEN 1 END) as pipelines_released,
    AVG(development_days) as avg_development_days
FROM nfcore_db.pipeline_timeline
WHERE development_start >= '2020-01-01'
GROUP BY DATE_TRUNC('quarter', development_start)
ORDER BY DATE_TRUNC('quarter', development_start)
```

### Quarterly Pipeline Activity
<AreaChart 
    data={gantt_style_data}
    x=quarter
    y=pipelines_started
    y2=pipelines_released
    title="Pipeline Activity by Quarter"
    xAxisTitle="Quarter"
    yAxisTitle="Number of Pipelines"
/>

## Development Duration Analysis

```sql duration_stats
-- Calculate statistics about development durations
SELECT 
    status,
    COUNT(*) as pipeline_count,
    ROUND(AVG(development_days), 0) as avg_duration_days,
    ROUND(MEDIAN(development_days), 0) as median_duration_days,
    MIN(development_days) as min_duration_days,
    MAX(development_days) as max_duration_days
FROM nfcore_db.pipeline_timeline
GROUP BY status
ORDER BY avg_duration_days DESC
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

Based on this timeline analysis, you can see:

1. **Development Speed**: Most pipelines fall into different speed categories
2. **Historical Trends**: Whether development times are getting shorter or longer over time
3. **Release Patterns**: Which pipelines have been in development the longest
4. **Quick vs Slow**: The distribution between quick-fire releases and long development cycles 