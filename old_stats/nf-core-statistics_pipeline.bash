# Clone the repository
git clone https://github.com/MatthiasZepper/nf-core-statistics.git
cd nf-core-statistics

# Use Python conversion function to extract all metrics
uvx git-history file nf-core-stats.db metrics.json \
--convert '
try:
    data = json.loads(content)
    return [{
        "id": "metrics",
        "namesOfAdopters": data.get("namesOfAdopters"),
        "namesOfContributors": data.get("namesOfContributors"),
        "namesOfContributorsNew": data.get("namesOfContributorsNew"),
        "numberOfPullRequestNew": data.get("numberOfPullRequestNew"),
        "p50NumberOfNewPullsPerWeek": data.get("p50NumberOfNewPullsPerWeek"),
        "p50NumberOfNewContributorsPerWeek": data.get("p50NumberOfNewContributorsPerWeek"),
        "p50SecondsToClosePulls": data.get("p50SecondsToClosePulls"),
        "p50SecondsToCloseIssues": data.get("p50SecondsToCloseIssues"),
        "meanNumberOfNewPullsPerWeek": data.get("meanNumberOfNewPullsPerWeek"),
        "meanNumberOfNewContributorsPerWeek": data.get("meanNumberOfNewContributorsPerWeek"),
        "meanSecondsToClosePulls": data.get("meanSecondsToClosePulls"),
        "meanSecondsToCloseIssues": data.get("meanSecondsToCloseIssues")
    }]
except Exception as ex:
    return []
' \
--full-versions \
--id id