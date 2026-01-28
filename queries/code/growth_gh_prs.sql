select
    month,
    num_total as num_prs,
    num_open as num_open_prs,
    prev_month_total as prev_month_num_prs,
    prev_month_open as prev_month_num_open_prs,
    growth_rate,
    open_growth_rate
from ${code_growth_issues_and_prs}
where type = 'pr'
order by month desc
