USE nf_core_stats_bot;

SELECT
    pipeline_name,
    full_name,
    html_url,
    parse_error,
    errors,
    warnings,
    updated_at
FROM strict_syntax.strict_syntax_pipelines
ORDER BY
    parse_error DESC,
    errors DESC NULLS LAST,
    warnings DESC NULLS LAST;
