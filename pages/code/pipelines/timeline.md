---
title: Pipeline Development Timeline
sidebar_position: 6
---

This timeline shows when each nf-core pipeline was in development and when they were released. It helps answer whether old pipelines are finally being released or if there are a lot of quick-fire pipelines being added and released quickly.

## Pipeline Lifecycle Timeline

Each row shows a pipeline's complete lifecycle with visual timeline bars:
- **Timeline** (blue): Total tracked time from creation to today
- **Development** (red): Time from creation to first release 
- **Released Time** (green): Time since first release

## Pipeline Lifecycle Summary

```sql lifecycle_summary
-- Show complete lifecycle for each pipeline with bar chart data
SELECT 
    pipeline_name,
    development_start::DATE as start_date,
    CASE WHEN status = 'Released' THEN development_end::DATE END as release_date,
    status,
    development_days,
    CASE 
        WHEN status = 'Released' THEN DATE_DIFF('day', development_end, CURRENT_DATE)
        ELSE 0
    END as days_since_release,
    CASE 
        WHEN status = 'Released' THEN development_days + DATE_DIFF('day', development_end, CURRENT_DATE)
        ELSE development_days
    END as total_days_tracked,
    -- Bar chart values for visualization
    development_days as dev_duration,
    CASE 
        WHEN status = 'Released' THEN DATE_DIFF('day', development_end, CURRENT_DATE)
        ELSE 0
    END as release_duration
FROM nfcore_db.pipeline_timeline
WHERE development_start >= '2018-01-01'
ORDER BY development_start DESC
```

<DataTable 
    data={lifecycle_summary} 
    search=true
    defaultSort={[{ id: 'start_date', desc: true }]}
>
    <Column id=pipeline_name title="Pipeline" />
    <Column id=start_date title="Started" />
    <Column id=release_date title="Released" />
    <Column id=status title="Status" />
    <Column id=development_days title="Dev Days" fmt=num0 />
    <Column id=days_since_release title="Days Released" fmt=num0 />
    <Column id=total_days_tracked title="Timeline" contentType=bar barColor="#3b82f6" />
    <Column id=dev_duration title="Development" contentType=bar barColor="#ef4444" />
    <Column id=release_duration title="Released Time" contentType=bar barColor="#10b981" />
</DataTable>

## Development vs Released Time Analysis

```sql duration_stats
-- Calculate statistics about development vs released time
SELECT 
    status,
    COUNT(*) as pipeline_count,
    ROUND(AVG(development_days), 0) as avg_development_days,
    ROUND(AVG(CASE WHEN status = 'Released' THEN DATE_DIFF('day', development_end, CURRENT_DATE) END), 0) as avg_days_released,
    ROUND(MEDIAN(development_days), 0) as median_development_days,
    MIN(development_days) as min_development_days,
    MAX(development_days) as max_development_days
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

Based on this timeline analysis, you can see:

1. **Development Speed**: Most pipelines fall into different speed categories
2. **Historical Trends**: Whether development times are getting shorter or longer over time
3. **Release Patterns**: Which pipelines have been in development the longest
4. **Quick vs Slow**: The distribution between quick-fire releases and long development cycles 