USE nf_core_stats_bot;

SELECT
    date::DATE as date,
    nextflow_version,
    total_pipelines,
    parse_errors,
    errors_zero,
    errors_low,
    errors_high,
    warnings_zero,
    warnings_low,
    warnings_high,
    total_errors,
    total_warnings,
    -- Calculated percentages (excluding parse errors from denominator)
    errors_zero / nullif(total_pipelines - parse_errors, 0)::float as errors_zero_pct,
    errors_low / nullif(total_pipelines - parse_errors, 0)::float as errors_low_pct,
    errors_high / nullif(total_pipelines - parse_errors, 0)::float as errors_high_pct,
    warnings_zero / nullif(total_pipelines - parse_errors, 0)::float as warnings_zero_pct,
    warnings_low / nullif(total_pipelines - parse_errors, 0)::float as warnings_low_pct,
    warnings_high / nullif(total_pipelines - parse_errors, 0)::float as warnings_high_pct
FROM strict_syntax.strict_syntax_history
ORDER BY date DESC;
