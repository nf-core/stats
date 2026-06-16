USE nf_core_stats_bot;

WITH pipelines AS (
    SELECT *
    FROM strict_syntax.strict_syntax_pipelines
    UNION ALL BY NAME
    SELECT
        NULL::INTEGER as workflow_output_count,
        NULL::INTEGER as publishdir_count,
        NULL::VARCHAR as workflow_output_report
    WHERE FALSE
)
SELECT
    pipeline_name,
    full_name,
    html_url,
    '/code/strict_syntax/' || pipeline_name as detail_url,
    CASE WHEN lint_output IS NOT NULL THEN '/code/strict_syntax/' || pipeline_name || '#lint-output' END as lint_output_url,
    CASE WHEN help_output IS NOT NULL THEN '/code/strict_syntax/' || pipeline_name || '#help-output' END as help_output_url,
    CASE
        WHEN workflow_output_report IS NOT NULL THEN '/code/strict_syntax/' || pipeline_name || '#workflow-outputs-report'
    END as workflow_output_report_url,
    parse_error,
    CASE WHEN parse_error THEN 'Yes' ELSE 'No' END as parse_error_label,
    errors,
    warnings,
    prints_help,
    CASE
        WHEN prints_help IS TRUE THEN 'Yes'
        WHEN prints_help IS FALSE THEN 'No'
        ELSE '-'
    END as prints_help_label,
    workflow_output_state,
    CASE workflow_output_state
        WHEN 'pass' THEN 'Fully migrated'
        WHEN 'warn' THEN 'In progress'
        WHEN 'error' THEN 'Not started'
        ELSE 'Unknown'
    END as workflow_output_state_label,
    CASE workflow_output_state
        WHEN 'pass' THEN 1
        WHEN 'warn' THEN 2
        WHEN 'error' THEN 3
        ELSE 4
    END as workflow_output_state_sort,
    workflow_output,
    CASE WHEN workflow_output THEN 'Yes' ELSE 'No' END as workflow_output_label,
    workflow_output_count,
    publishdir,
    CASE
        WHEN publishdir AND publishdir_count IS NOT NULL THEN 'Yes (' || publishdir_count || ')'
        WHEN publishdir THEN 'Yes'
        ELSE 'No'
    END as publishdir_label,
    publishdir_count,
    commit_sha,
    nextflow_version,
    lint_output,
    help_output,
    workflow_output_report,
    updated_at
FROM pipelines
ORDER BY
    parse_error DESC,
    errors DESC NULLS LAST,
    warnings DESC NULLS LAST;
