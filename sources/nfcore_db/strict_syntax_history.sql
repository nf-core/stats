USE nf_core_stats_bot;

SELECT
    date::DATE as date,
    component_type,
    nextflow_version,
    total,
    parse_errors,
    errors_zero,
    errors_low,
    errors_high,
    warnings_zero,
    warnings_low,
    warnings_high,
    total_errors,
    total_warnings,
    coalesce(prints_help_pass, 0) as prints_help_pass,
    coalesce(prints_help_fail, 0) as prints_help_fail,
    coalesce(workflow_output_pass, 0) as workflow_output_pass,
    coalesce(workflow_output_warn, 0) as workflow_output_warn,
    coalesce(workflow_output_error, 0) as workflow_output_error,
    errors_zero / nullif(total - parse_errors, 0)::float as errors_zero_pct,
    errors_low / nullif(total - parse_errors, 0)::float as errors_low_pct,
    errors_high / nullif(total - parse_errors, 0)::float as errors_high_pct,
    warnings_zero / nullif(total - parse_errors, 0)::float as warnings_zero_pct,
    warnings_low / nullif(total - parse_errors, 0)::float as warnings_low_pct,
    warnings_high / nullif(total - parse_errors, 0)::float as warnings_high_pct,
    coalesce(workflow_output_pass, 0) / nullif(total, 0)::float as workflow_output_pass_pct,
    coalesce(workflow_output_warn, 0) / nullif(total, 0)::float as workflow_output_warn_pct,
    coalesce(workflow_output_error, 0) / nullif(total, 0)::float as workflow_output_error_pct
FROM strict_syntax.strict_syntax_history
ORDER BY date DESC, component_type;
