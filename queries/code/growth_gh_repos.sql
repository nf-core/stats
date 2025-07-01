with monthly_counts as (
    select date_trunc('month', gh_created_at) as month,
        count(*) as new_repos,
    from nfcore_db.all_repos
    where gh_created_at is not null
    group by 1
)
select month,
    sum(new_repos) over (
        order by month
    ) as num_repos,
    new_repos,
    lag(new_repos) over (
        order by month
    ) as prev_month_new_repos,
    round(
        cast(
            (
                new_repos / nullif(
                    lag(new_repos) over (
                        order by month
                    ),
                    0
                ) - 1
            )  as numeric
        ),
        1
    ) as growth_rate
from monthly_counts
order by month desc