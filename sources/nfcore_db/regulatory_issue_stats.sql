USE nf_core_stats_bot;

SELECT
    COALESCE(i.pipeline_name, c.pipeline_name, p.pipeline_name, pc.pipeline_name) AS pipeline_name,
    i.issue_count,
    c.closed_issue_count,
    c.median_seconds_to_issue_closed,
    p.pr_count,
    pc.closed_pr_count,
    pc.median_seconds_to_pr_closed
FROM (
    SELECT
        pipeline_name,
        COUNT(issue_number) AS issue_count
    FROM github.issue_stats
    WHERE issue_type = 'issue'
    GROUP BY pipeline_name
) AS i
FULL JOIN (
    SELECT
        pipeline_name,
        COUNT(issue_number) AS closed_issue_count,
        MEDIAN(closed_wait_seconds) AS median_seconds_to_issue_closed
    FROM github.issue_stats
    WHERE issue_type = 'issue' AND state = 'closed'
    GROUP BY pipeline_name
) AS c ON i.pipeline_name = c.pipeline_name
FULL JOIN (
    SELECT
        pipeline_name,
        COUNT(issue_number) AS pr_count
    FROM github.issue_stats
    WHERE issue_type = 'pr'
    GROUP BY pipeline_name
) AS p ON COALESCE(i.pipeline_name, c.pipeline_name) = p.pipeline_name
FULL JOIN (
    SELECT
        pipeline_name,
        COUNT(issue_number) AS closed_pr_count,
        MEDIAN(closed_wait_seconds) AS median_seconds_to_pr_closed
    FROM github.issue_stats
    WHERE issue_type = 'pr' AND state = 'closed'
    GROUP BY pipeline_name
) AS pc ON COALESCE(i.pipeline_name, c.pipeline_name, p.pipeline_name) = pc.pipeline_name
ORDER BY pipeline_name;
