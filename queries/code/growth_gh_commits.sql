with combined_commits as (
    select sum(cast(commits as integer)) as num_commits
    from (
        -- select commits from nfcore_db.core_repos
        -- union all
        select commits from nfcore_db.nfcore_pipelines
    ) all_commits
)
select 
    num_commits
from combined_commits 