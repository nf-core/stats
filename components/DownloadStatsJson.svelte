<script>
  /** @type {Array<Object>} */
  export let pipelineStats = [];
  /** @type {Array<Object>} */
  export let issueStats = [];
  /** @type {Array<Object>} */
  export let contributorStats = [];

  /**
   * Build the stats JSON structure matching the regulatory report format.
   * Output is keyed by pipeline name with pipeline_stats, issue_stats,
   * and contributor_stats sub-objects.
   */
  function buildStatsJson() {
    // Index issue stats by pipeline name
    const issuesByPipeline = {};
    if (issueStats) {
      for (const row of issueStats) {
        issuesByPipeline[row.pipeline_name] = {
          pipeline_name: row.pipeline_name,
          issue_count: row.issue_count ?? null,
          closed_issue_count: row.closed_issue_count ?? null,
          median_seconds_to_issue_closed: row.median_seconds_to_issue_closed ?? null,
          pr_count: row.pr_count ?? null,
          closed_pr_count: row.closed_pr_count ?? null,
          median_seconds_to_pr_closed: row.median_seconds_to_pr_closed ?? null,
        };
      }
    }

    // Index contributor stats by pipeline name
    const contribByPipeline = {};
    if (contributorStats) {
      for (const row of contributorStats) {
        contribByPipeline[row.pipeline_name] = {
          pipeline_name: row.pipeline_name,
          number_of_contributors: row.number_of_contributors,
        };
      }
    }

    // Build the final structure keyed by pipeline name
    const result = {};
    if (pipelineStats) {
      for (const row of pipelineStats) {
        const name = row.name;
        result[name] = {
          pipeline_stats: {
            name: row.name,
            description: row.description,
            stargazers_count: row.stargazers_count,
            forks_count: row.forks_count,
            open_issues_count: row.open_issues_count,
            archived: row.archived,
            last_release_date: row.last_release_date ?? null,
            category: row.category,
          },
          issue_stats: issuesByPipeline[name] ?? null,
          contributor_stats: contribByPipeline[name] ?? null,
        };
      }
    }

    return result;
  }

  function downloadJson() {
    const data = buildStatsJson();
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "nf-core-stats.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  $: statsData = buildStatsJson();
  $: pipelineCount = Object.keys(statsData).length;
</script>

<div class="download-section">
  <button class="download-btn" on:click={downloadJson}>
    Download nf-core-stats.json
  </button>
  <span class="pipeline-count">{pipelineCount} pipelines included</span>
</div>

<style>
  .download-section {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin: 1.5rem 0;
  }

  .download-btn {
    background-color: var(--primary-color, #22ae63);
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 0.2s;
  }

  .download-btn:hover {
    background-color: var(--primary-color-dark, #1a9655);
  }

  .pipeline-count {
    color: var(--grey-600, #666);
    font-size: 0.9rem;
  }
</style>
