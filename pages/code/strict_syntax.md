---
title: Strict Syntax Health
sidebar_position: 10
---

# nf-core Pipeline Strict Syntax Health

This page tracks the adoption of [Nextflow strict syntax](https://www.nextflow.io/docs/latest/strict-syntax.html) across nf-core pipelines. **Fixing all errors from `nextflow lint` will be required by early spring 2026.**

```sql history
select * from nfcore_db.strict_syntax_history
```

```sql pipelines
select * from nfcore_db.strict_syntax_pipelines
```

## Current Status

<BigValue
    data={history}
    value=total_pipelines
    title="Total Pipelines"
    sparkline=date
/>
<BigValue
    data={history}
    value=errors_zero
    title="Zero Errors"
    sparkline=date
/>
<BigValue
    data={history}
    value=parse_errors
    title="Parse Errors"
    sparkline=date
/>

## Error Distribution Over Time

<Tabs>
    <Tab label="Percentage">
        <AreaChart
            data={history}
            x=date
            y={['errors_zero_pct', 'errors_low_pct', 'errors_high_pct']}
            title="Pipeline Error Distribution (%)"
            yFmt="pct0"
            yMax={1}
            seriesColors={['#2ecc71', '#f39c12', '#e74c3c']}
        />
    </Tab>
    <Tab label="Counts">
        <AreaChart
            data={history}
            x=date
            y={['errors_zero', 'errors_low', 'errors_high']}
            title="Pipeline Error Distribution"
            yAxisTitle="Number of Pipelines"
            seriesColors={['#2ecc71', '#f39c12', '#e74c3c']}
        />
    </Tab>
</Tabs>

## Warning Distribution Over Time

<Tabs>
    <Tab label="Percentage">
        <AreaChart
            data={history}
            x=date
            y={['warnings_zero_pct', 'warnings_low_pct', 'warnings_high_pct']}
            title="Pipeline Warning Distribution (%)"
            yFmt="pct0"
            yMax={1}
            seriesColors={['#1abc9c', '#3498db', '#9b59b6']}
        />
    </Tab>
    <Tab label="Counts">
        <AreaChart
            data={history}
            x=date
            y={['warnings_zero', 'warnings_low', 'warnings_high']}
            title="Pipeline Warning Distribution"
            yAxisTitle="Number of Pipelines"
            seriesColors={['#1abc9c', '#3498db', '#9b59b6']}
        />
    </Tab>
</Tabs>

## Per-Pipeline Breakdown

<DataTable
    data={pipelines}
    search=true
>
    <Column id=pipeline_name title="Pipeline" />
    <Column id=parse_error title="Parse Error" />
    <Column id=errors title="Errors" contentType=colorscale colorScale=negative />
    <Column id=warnings title="Warnings" contentType=colorscale colorScale=warning />
    <Column id=html_url title="Repository" contentType=link linkLabel="View" />
</DataTable>

## Historical Trend Data

<DataTable
    data={history}
    search=false
    defaultSort={[{ id: 'date', desc: true }]}
>
    <Column id=date title="Date" />
    <Column id=total_pipelines title="Total" />
    <Column id=parse_errors title="Parse Errors" />
    <Column id=errors_zero title="0 Errors" contentType=colorscale colorScale=positive />
    <Column id=errors_low title="1-5 Errors" contentType=colorscale colorScale=warning />
    <Column id=errors_high title=">5 Errors" contentType=colorscale colorScale=negative />
</DataTable>

## About

Data sourced from [nf-core/strict-syntax-health](https://github.com/nf-core/strict-syntax-health), which runs `nextflow lint` nightly on all nf-core pipelines.

- **Zero errors**: Pipelines fully compliant with strict syntax
- **1-5 errors**: Minor issues to fix
- **>5 errors**: Significant work needed
- **Parse errors**: Pipelines that couldn't be linted (likely syntax errors)
