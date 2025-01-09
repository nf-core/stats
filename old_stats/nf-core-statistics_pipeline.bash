# Clone the repository
git clone https://github.com/MatthiasZepper/nf-core-statistics.git
cd nf-core-statistics

# Use Python conversion function to extract the data we want
uvx git-history file nf-core-stats.db metrics.json \
--convert '
try:
    data = json.loads(content)
    return [{
        "id": "metrics",
        "numberOfPullRequestNew": data.get("numberOfPullRequestNew"),
        "p50NumberOfNewPullsPerWeek": data.get("p50NumberOfNewPullsPerWeek"),
        "meanNumberOfNewPullsPerWeek": data.get("meanNumberOfNewPullsPerWeek"),
        "p50SecondsToClosePulls": data.get("p50SecondsToClosePulls"),
        "meanSecondsToClosePulls": data.get("meanSecondsToClosePulls")
    }]
except Exception as ex:
    return []
' \
--full-versions \
--id id