select
timestamp,
sum(count(username)) over (order by timestamp) as members,
from community_github_contributors
group by timestamp