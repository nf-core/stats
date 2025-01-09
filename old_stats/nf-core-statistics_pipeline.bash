git clone https://github.com/MatthiasZepper/nf-core-statistics.git
cd nf-core-statistics

uvx git-history file metrics.db metrics.json \
  --convert '
data = json.loads(content)
return [{
    "id": "metrics",
    "numberOfPullRequestNew": data.get("numberOfPullRequestNew"),
    "p50NumberOfNewPullsPerWeek": data.get("p50NumberOfNewPullsPerWeek"), 
    "meanNumberOfNewPullsPerWeek": data.get("meanNumberOfNewPullsPerWeek"),
    "p50SecondsToClosePulls": data.get("p50SecondsToClosePulls")/3600,  # Convert to hours
    "meanSecondsToClosePulls": data.get("meanSecondsToClosePulls")/3600,
    "p50NumberOfNewContributorsPerWeek": data.get("p50NumberOfNewContributorsPerWeek"),
    "meanNumberOfNewContributorsPerWeek": data.get("meanNumberOfNewContributorsPerWeek")
}]
' \
  --id id