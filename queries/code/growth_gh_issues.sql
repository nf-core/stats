select
    month,
    num_total as num_issues,
    num_open as num_open_issues,
    prev_month_total as prev_month_num_issues,
    prev_month_open as prev_month_num_open_issues,
    growth_rate,
    open_growth_rate
from ${code_growth_issues_and_prs}
where type = 'issue'
order by month desc
