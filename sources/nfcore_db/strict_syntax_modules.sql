USE nf_core_stats_bot;

SELECT
    module_name,
    html_url,
    parse_error,
    errors,
    warnings,
    commit_sha,
    nextflow_version,
    updated_at
FROM strict_syntax.strict_syntax_modules
ORDER BY
    parse_error DESC,
    errors DESC NULLS LAST,
    warnings DESC NULLS LAST;
