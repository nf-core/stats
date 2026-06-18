---
title: Strict Syntax Pipeline Detail
---

```sql pipeline_detail
select *
from nfcore_db.strict_syntax_pipelines
where pipeline_name = '${params.pipeline}'
```

# Strict syntax: {params.pipeline}

[Back to strict syntax health](/code/strict_syntax)

<BigValue data={pipeline_detail} value=errors title="Errors" />
<BigValue data={pipeline_detail} value=warnings title="Warnings" />
<BigValue data={pipeline_detail} value=prints_help_label title="Prints Help" />
<BigValue data={pipeline_detail} value=workflow_output_state_label title="Workflow Outputs" />

## Pipeline Status

- **Repository:** <Value data={pipeline_detail} column=html_url />
- **Parse error:** <Value data={pipeline_detail} column=parse_error_label />
- **Nextflow version:** <Value data={pipeline_detail} column=nextflow_version />
- **Workflow `output {}`:** <Value data={pipeline_detail} column=workflow_output_label />
- **Legacy `publishDir`:** <Value data={pipeline_detail} column=publishdir_label />

<div id="lint-output"></div>

<StrictSyntaxReport
    data={pipeline_detail}
    column="lint_output"
    title="Lint Output"
    emptyMessage="No lint output was captured for this pipeline."
/>

<div id="help-output"></div>

<StrictSyntaxReport
    data={pipeline_detail}
    column="help_output"
    title="Help Output"
    format="text"
    emptyMessage="Help output is only captured for pipelines with zero lint errors."
/>

<div id="workflow-outputs-report"></div>

<StrictSyntaxReport
    data={pipeline_detail}
    column="workflow_output_report"
    title="Workflow Outputs Report"
    emptyMessage="No workflow outputs report was captured for this pipeline."
/>
