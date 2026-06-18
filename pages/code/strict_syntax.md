---
title: Strict Syntax Health
sidebar_position: 10
---

# nf-core Strict Syntax Health

This page tracks adoption of [Nextflow strict syntax](https://www.nextflow.io/docs/latest/strict-syntax.html) across nf-core pipelines, modules, and subworkflows. **Fixing all errors from `nextflow lint` will be required by early spring 2026.**

## Current Snapshot

<DataTable data={current_summary} rows=all>
    <Column id=component title="Component" />
    <Column id=total title="Total" />
    <Column id=parse_errors title="Parse Errors" />
    <Column id=zero_errors_label title="Zero Errors" />
</DataTable>

<Tabs>
    <Tab label="Pipelines">

## Pipeline Status

Latest snapshot: <Value data={pipeline_latest} column=parse_errors /> parse errors, <Value data={pipeline_latest} column=total_errors /> errors, and <Value data={pipeline_latest} column=total_warnings /> warnings across <Value data={pipeline_latest} column=total /> pipelines.

<BigValue
    data={pipeline_latest}
    value=total
    title="Total Pipelines"
/>
<BigValue
    data={pipeline_latest}
    value=errors_zero
    title="Zero Errors"
/>
<BigValue
    data={pipeline_latest}
    value=total_errors
    title="Total Errors"
/>
<BigValue
    data={pipeline_latest}
    value=total_warnings
    title="Total Warnings"
/>
<BigValue
    data={pipeline_latest}
    value=workflow_output_pass
    title="Workflow Outputs Migrated"
/>
<BigValue
    data={pipeline_latest}
    value=nextflow_version
    title="Nextflow Version"
/>
<BigValue
    data={pipeline_updated_at}
    value=last_updated
    title="Last Updated"
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

## Pipeline Warning Distribution

<Tabs>
    <Tab label="Percentage">
        <AreaChart
            data={pipeline_history}
            x=date
            y={['warnings_zero_pct', 'warnings_low_pct', 'warnings_high_pct']}
            title="Pipeline Warning Distribution (%)"
            yFmt="pct0"
            yMax={1}
            seriesColors={['#2ecc71', '#f39c12', '#e74c3c']}
        />
    </Tab>
    <Tab label="Counts">
        <AreaChart
            data={pipeline_history}
            x=date
            y={['warnings_zero', 'warnings_low', 'warnings_high']}
            title="Pipeline Warning Distribution"
            yAxisTitle="Number of Pipelines"
            seriesColors={['#2ecc71', '#f39c12', '#e74c3c']}
        />
    </Tab>
</Tabs>

## Workflow Outputs Migration

Adoption of the new [workflow outputs](https://docs.seqera.io/nextflow/tutorials/workflow-outputs) syntax (`output {}`) and migration away from legacy `publishDir`.

- **Fully migrated:** <Value data={pipeline_latest} column=workflow_output_pass /> pipelines (<Value data={pipeline_latest} column=workflow_output_pass_pct fmt=pct1 />)
- **In progress:** <Value data={pipeline_latest} column=workflow_output_warn /> pipelines (<Value data={pipeline_latest} column=workflow_output_warn_pct fmt=pct1 />)
- **Not started:** <Value data={pipeline_latest} column=workflow_output_error /> pipelines (<Value data={pipeline_latest} column=workflow_output_error_pct fmt=pct1 />)

<Tabs>
    <Tab label="Percentage">
        <AreaChart
            data={pipeline_history}
            x=date
            y={['workflow_output_pass_pct', 'workflow_output_warn_pct', 'workflow_output_error_pct']}
            title="Workflow Outputs Migration (%)"
            yFmt="pct0"
            yMax={1}
            seriesColors={['#2ecc71', '#f39c12', '#e74c3c']}
        />
    </Tab>
    <Tab label="Counts">
        <AreaChart
            data={pipeline_history}
            x=date
            y={['workflow_output_pass', 'workflow_output_warn', 'workflow_output_error']}
            title="Workflow Outputs Migration"
            yAxisTitle="Number of Pipelines"
            seriesColors={['#2ecc71', '#f39c12', '#e74c3c']}
        />
    </Tab>
</Tabs>

<DataTable data={pipelines} search=true sort="workflow_output_state_sort asc">
    <Column id=pipeline_name title="Pipeline" />
    <Column id=workflow_output_state_label title="Status" />
    <Column id=workflow_output_label title="Output Block" />
    <Column id=publishdir_label title="publishDir" />
    <Column id=workflow_output_report_url title="Report" contentType=link linkLabel="View" />
    <Column id=html_url title="Repository" contentType=link linkLabel="View" />
</DataTable>

## Per-Pipeline Breakdown

Open a pipeline row, lint link, or help link for captured output details.

<DataTable data={pipelines} search=true link=detail_url>
    <Column id=pipeline_name title="Pipeline" />
    <Column id=parse_error_label title="Parse Error" />
    <Column id=errors title="Errors" contentType=colorscale colorScale=negative />
    <Column id=warnings title="Warnings" contentType=colorscale colorScale=warning />
    <Column id=prints_help_label title="Prints Help" />
    <Column id=lint_output_url title="Lint Output" contentType=link linkLabel="View" />
    <Column id=help_output_url title="Help Output" contentType=link linkLabel="View" />
    <Column id=workflow_output_state_label title="Workflow Outputs" />
    <Column id=html_url title="Repository" contentType=link linkLabel="View" />
</DataTable>

    </Tab>
    <Tab label="Modules">

## Module Status

<BigValue
    data={module_latest}
    value=total
    title="Total Modules"
/>
<BigValue
    data={module_latest}
    value=errors_zero
    title="Zero Errors"
/>
<BigValue
    data={module_latest}
    value=total_errors
    title="Total Errors"
/>
<BigValue
    data={module_latest}
    value=total_warnings
    title="Total Warnings"
/>

## Module Error Distribution

<Tabs>
    <Tab label="Percentage">
        <AreaChart
            data={module_history}
            x=date
            y={['errors_zero_pct', 'errors_low_pct', 'errors_high_pct']}
            title="Module Error Distribution (%)"
            yFmt="pct0"
            yMax={1}
            seriesColors={['#2ecc71', '#f39c12', '#e74c3c']}
        />
    </Tab>
    <Tab label="Counts">
        <AreaChart
            data={module_history}
            x=date
            y={['errors_zero', 'errors_low', 'errors_high']}
            title="Module Error Distribution"
            yAxisTitle="Number of Modules"
            seriesColors={['#2ecc71', '#f39c12', '#e74c3c']}
        />
    </Tab>
</Tabs>

## Module Warning Distribution

<Tabs>
    <Tab label="Percentage">
        <AreaChart
            data={module_history}
            x=date
            y={['warnings_zero_pct', 'warnings_low_pct', 'warnings_high_pct']}
            title="Module Warning Distribution (%)"
            yFmt="pct0"
            yMax={1}
            seriesColors={['#2ecc71', '#f39c12', '#e74c3c']}
        />
    </Tab>
    <Tab label="Counts">
        <AreaChart
            data={module_history}
            x=date
            y={['warnings_zero', 'warnings_low', 'warnings_high']}
            title="Module Warning Distribution"
            yAxisTitle="Number of Modules"
            seriesColors={['#2ecc71', '#f39c12', '#e74c3c']}
        />
    </Tab>
</Tabs>

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
    data={subworkflow_latest}
    value=total
    title="Total Subworkflows"
/>
<BigValue
    data={subworkflow_latest}
    value=errors_zero
    title="Zero Errors"
/>
<BigValue
    data={subworkflow_latest}
    value=total_errors
    title="Total Errors"
/>
<BigValue
    data={subworkflow_latest}
    value=total_warnings
    title="Total Warnings"
/>

## Subworkflow Error Distribution

<Tabs>
    <Tab label="Percentage">
        <AreaChart
            data={subworkflow_history}
            x=date
            y={['errors_zero_pct', 'errors_low_pct', 'errors_high_pct']}
            title="Subworkflow Error Distribution (%)"
            yFmt="pct0"
            yMax={1}
            seriesColors={['#2ecc71', '#f39c12', '#e74c3c']}
        />
    </Tab>
    <Tab label="Counts">
        <AreaChart
            data={subworkflow_history}
            x=date
            y={['errors_zero', 'errors_low', 'errors_high']}
            title="Subworkflow Error Distribution"
            yAxisTitle="Number of Subworkflows"
            seriesColors={['#2ecc71', '#f39c12', '#e74c3c']}
        />
    </Tab>
</Tabs>

## Subworkflow Warning Distribution

<Tabs>
    <Tab label="Percentage">
        <AreaChart
            data={subworkflow_history}
            x=date
            y={['warnings_zero_pct', 'warnings_low_pct', 'warnings_high_pct']}
            title="Subworkflow Warning Distribution (%)"
            yFmt="pct0"
            yMax={1}
            seriesColors={['#2ecc71', '#f39c12', '#e74c3c']}
        />
    </Tab>
    <Tab label="Counts">
        <AreaChart
            data={subworkflow_history}
            x=date
            y={['warnings_zero', 'warnings_low', 'warnings_high']}
            title="Subworkflow Warning Distribution"
            yAxisTitle="Number of Subworkflows"
            seriesColors={['#2ecc71', '#f39c12', '#e74c3c']}
        />
    </Tab>
</Tabs>

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

Nightly `nextflow lint` runs via the stats repo pipeline, migrated from [nf-core/strict-syntax-health](https://github.com/nf-core/strict-syntax-health). See the [nf-core roadmap blog post](https://nf-co.re/blog/2025/nextflow_syntax_nf-core_roadmap) for the strict syntax timeline.

- **Parse errors** indicate items where `nextflow lint` could not run, typically because syntax errors prevent Nextflow from parsing the code.
- **Errors** indicate syntax issues that will cause problems in future Nextflow versions.
- **Warnings** indicate deprecated patterns that should be updated; warnings are allowed, but still worth fixing.
- **Prints Help** tests whether a zero-error pipeline can print help with the v2 parser: `NXF_SYNTAX_PARSER=v2 nextflow run . --help`.
- **Workflow Outputs Migration** tracks adoption of the new [workflow outputs](https://docs.seqera.io/nextflow/tutorials/workflow-outputs) syntax and migration away from `publishDir`. A pipeline is fully migrated once it uses `output {}` with no `publishDir`.

## Running Locally

Run strict syntax linting in a pipeline repository:

```bash
nextflow lint .
```

Until [nextflow-io/nextflow#6716](https://github.com/nextflow-io/nextflow/pull/6716) is included in a Nextflow edge release, you may need to exclude nf-test files manually:

```bash
nextflow lint . -exclude ".git,.nf-test,nf-test.config"
```

## Getting Help

If you need help fixing strict syntax errors, ask in the [Seqera community forum](https://community.seqera.io/).

```sql pipeline_history
select * from nfcore_db.strict_syntax_history
where component_type = 'pipelines'
order by date
```

```sql pipeline_latest
select * from nfcore_db.strict_syntax_history
where component_type = 'pipelines'
order by date desc
limit 1
```

```sql module_history
select * from nfcore_db.strict_syntax_history
where component_type = 'modules'
order by date
```

```sql module_latest
select * from nfcore_db.strict_syntax_history
where component_type = 'modules'
order by date desc
limit 1
```

```sql subworkflow_history
select * from nfcore_db.strict_syntax_history
where component_type = 'subworkflows'
order by date
```

```sql subworkflow_latest
select * from nfcore_db.strict_syntax_history
where component_type = 'subworkflows'
order by date desc
limit 1
```

```sql current_summary
with latest as (
    select
        *,
        row_number() over (partition by component_type order by date desc) as row_num
    from nfcore_db.strict_syntax_history
)
select
    case component_type
        when 'pipelines' then 'Pipelines'
        when 'modules' then 'Modules'
        when 'subworkflows' then 'Subworkflows'
    end as component,
    total,
    parse_errors,
    errors_zero::INTEGER::VARCHAR || ' (' ||
        case
            when total - parse_errors > 0 then printf('%.1f%%', 100 * errors_zero / (total - parse_errors)::float)
            else '0.0%'
        end ||
    ')' as zero_errors_label
from latest
where row_num = 1
order by
    case component_type
        when 'pipelines' then 1
        when 'modules' then 2
        when 'subworkflows' then 3
    end
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

```sql pipeline_updated_at
select max(updated_at) as last_updated from nfcore_db.strict_syntax_pipelines
```

<div style="position: absolute; left: -9999px;" aria-hidden="true">
{#each pipelines as pipeline}
<a href="/code/strict_syntax/{pipeline.pipeline_name}">Pipeline detail {pipeline.pipeline_name}</a>
{/each}
</div>
