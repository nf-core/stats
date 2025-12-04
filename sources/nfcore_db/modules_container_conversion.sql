USE nf_core_stats_bot;

SELECT
    timestamp,
    total_modules,
    modules_old_container_syntax as modules_with_old_pattern,
    modules_new_container_syntax as modules_converted,
    modules_with_topics_version,
    modules_without_topics_version,
    modules_with_wave_containers,
    modules_without_wave_containers,
    (modules_old_container_syntax::FLOAT / total_modules) as conversion_percentage
FROM github.modules_container_conversion
ORDER BY timestamp DESC;
