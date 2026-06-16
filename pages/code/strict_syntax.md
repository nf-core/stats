---
title: Strict Syntax Health
sidebar_position: 10
---

# nf-core Strict Syntax Health

This page tracks adoption of [Nextflow strict syntax](https://www.nextflow.io/docs/latest/strict-syntax.html) across nf-core pipelines, modules, and subworkflows. **Fixing all errors from `nextflow lint` will be required by early spring 2026.**

```sql pipeline_history
select * from nfcore_db.strict_syntax_history
where component_type = 'pipelines'
order by date desc
```

```sql module_history
select * from nfcore_db.strict_syntax_history
where component_type = 'modules'
order by date desc
```

```sql subworkflow_history
select * from nfcore_db.strict_syntax_history
where component_type = 'subworkflows'
order by date desc
```

```sql pipelines
select * from nfcore_db.strict_syntax_pipelines
```

```sql modules
select * from nfcore_db.strict_syntax_modules
```

```sql subworkflows
select * from nfcore_db.strict_syntax_subworkflows
```

<Tabs>
    <Tab label="Pipelines">

## Pipeline Status

<BigValue
    data={pipeline_history}
    value=total
    title="Total Pipelines"
    sparkline=date
/>
<BigValue
    data={pipeline_history}
    value=errors_zero
    title="Zero Errors"
    sparkline=date
/>
<BigValue
    data={pipeline_history}
    value=workflow_output_pass
    title="Workflow Outputs Migrated"
    sparkline=date
/>

## Pipeline Error Distribution

<Tabs>
    <Tab label="Percentage">
        <AreaChart
            data={pipeline_history}
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
            data={pipeline_history}
            x=date
            y={['errors_zero', 'errors_low', 'errors_high']}
            title="Pipeline Error Distribution"
            yAxisTitle="Number of Pipelines"
            seriesColors={['#2ecc71', '#f39c12', '#e74c3c']}
        />
    </Tab>
</Tabs>

## Per-Pipeline Breakdown

<DataTable data={pipelines} search=true>
    <Column id=pipeline_name title="Pipeline" />
    <Column id=parse_error title="Parse Error" />
    <Column id=errors title="Errors" contentType=colorscale colorScale=negative />
    <Column id=warnings title="Warnings" contentType=colorscale colorScale=warning />
    <Column id=prints_help title="Prints Help" />
    <Column id=workflow_output_state title="Workflow Outputs" />
    <Column id=html_url title="Repository" contentType=link linkLabel="View" />
</DataTable>

    </Tab>
    <Tab label="Modules">

## Module Status

<BigValue
    data={module_history}
    value=total
    title="Total Modules"
    sparkline=date
/>
<BigValue
    data={module_history}
    value=errors_zero
    title="Zero Errors"
    sparkline=date
/>

## Module Error Distribution

<AreaChart
    data={module_history}
    x=date
    y={['errors_zero', 'errors_low', 'errors_high']}
    title="Module Error Distribution"
    yAxisTitle="Number of Modules"
    seriesColors={['#2ecc71', '#f39c12', '#e74c3c']}
/>

## Per-Module Breakdown

<DataTable data={modules} search=true>
    <Column id=module_name title="Module" />
    <Column id=parse_error title="Parse Error" />
    <Column id=errors title="Errors" contentType=colorscale colorScale=negative />
    <Column id=warnings title="Warnings" contentType=colorscale colorScale=warning />
    <Column id=html_url title="Repository" contentType=link linkLabel="View" />
</DataTable>

    </Tab>
    <Tab label="Subworkflows">

## Subworkflow Status

<BigValue
    data={subworkflow_history}
    value=total
    title="Total Subworkflows"
    sparkline=date
/>
<BigValue
    data={subworkflow_history}
    value=errors_zero
    title="Zero Errors"
    sparkline=date
/>

## Subworkflow Error Distribution

<AreaChart
    data={subworkflow_history}
    x=date
    y={['errors_zero', 'errors_low', 'errors_high']}
    title="Subworkflow Error Distribution"
    yAxisTitle="Number of Subworkflows"
    seriesColors={['#2ecc71', '#f39c12', '#e74c3c']}
/>

## Per-Subworkflow Breakdown

<DataTable data={subworkflows} search=true>
    <Column id=subworkflow_name title="Subworkflow" />
    <Column id=parse_error title="Parse Error" />
    <Column id=errors title="Errors" contentType=colorscale colorScale=negative />
    <Column id=warnings title="Warnings" contentType=colorscale colorScale=warning />
    <Column id=html_url title="Repository" contentType=link linkLabel="View" />
</DataTable>

    </Tab>
</Tabs>

## About

Nightly `nextflow lint` runs via the stats repo pipeline (migrated from [nf-core/strict-syntax-health](https://github.com/nf-core/strict-syntax-health)).

- **Zero errors**: Fully compliant with strict syntax
- **1-5 errors**: Minor issues to fix
- **>5 errors**: Significant work needed
- **Workflow outputs**: Migration from `publishDir` to the new `output {}` block
