import itertools
from datetime import datetime, timezone

import dlt
import requests
from semanticscholar import SemanticScholar, SemanticScholarException

from ._github import get_file_contents, get_github_headers, github_request
from ._logging import log_pipeline_stats, logger


def _get_pipeline_names(headers) -> list[str]:
    pipeline_names_url = "https://raw.githubusercontent.com/nf-core/website/main/public/pipeline_names.json"
    try:
        return github_request(pipeline_names_url, headers).json()["pipeline"]
    except (requests.RequestException, KeyError) as e:
        logger.warning(f"Failed to get pipeline names from nf-core website: {e}")
        raise


def _parse_doi_from_nextflow_config(file_contents) -> str | None:
    """Parse DOI from nextflow.config manifest section

    Extracts the DOI value from the manifest.doi field, removing any URL prefix.
    The DOI pattern typically looks like: 10.XXXX/...

    Args:
        file_contents: The contents of the nextflow.config file as a string

    Returns:
        The DOI string (e.g., '10.1371/journal.pcbi.1012265') or None if not found
    """
    import re

    # First, extract the manifest section
    # Match from 'manifest {' to the closing '}'
    manifest_pattern = r"manifest\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}"
    manifest_match = re.search(manifest_pattern, file_contents, re.DOTALL)

    if not manifest_match:
        return None

    manifest_content = manifest_match.group(1)

    # Now look for the doi field within the manifest section
    # Match: doi = 'https://doi.org/10.1371/journal.pcbi.1012265'
    # or:    doi = '10.1371/journal.pcbi.1012265'
    doi_pattern = r"doi\s*=\s*['\"](?:https?://doi\.org/)?([0-9]+\.[0-9]+/[^'\"]+)['\"]"

    doi_match = re.search(doi_pattern, manifest_content)
    if doi_match:
        return doi_match.group(1)

    return None


def _get_citations_for_pipeline(pipeline_name: str, github_headers: dict):
    try:
        nextflow_config = get_file_contents("nf-core", pipeline_name, "nextflow.config", github_headers)
    except (requests.HTTPError, ValueError) as e:
        logger.error(f"Failed to get nextflow.config for {pipeline_name}: {e}")
        return

    # multiple dois might be separated by commata
    doi_str = _parse_doi_from_nextflow_config(nextflow_config)
    if doi_str is None:
        logger.info(f"No doi found in `nextflow.config` for {pipeline_name}")
        return

    dois = [x.strip() for x in doi_str.split(",")]

    sch = SemanticScholar()
    for doi in dois:
        try:
            # TODO consider using a semantischolar API key for more reliable queries
            # > Most Semantic Scholar endpoints are available to the public without authentication,
            # > but they are rate-limited to 1000 requests per second shared among all unauthenticated users.
            # > Requests may also be further throttled during periods of heavy use.
            #
            # When using an API key we get an guaranteed rate limit of one request per second
            # (https://www.semanticscholar.org/product/api)
            paper = sch.get_paper(doi)
            yield {
                "pipeline_name": pipeline_name,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "doi": doi,
                "paper_title": paper.title,
                "citation_count": paper.citationCount,
                "influencial_paper_citation_count": paper.influentialCitationCount,
            }
        except SemanticScholarException.ObjectNotFoundException:
            logger.warning(f"DOI not found: {doi}")


@dlt.source(name="semanticscholar")
def semanticscholar_source():
    github_headers = get_github_headers()
    pipelines = _get_pipeline_names(github_headers)

    return [dlt.resource(pipeline_citations(pipelines, github_headers), name="pipeline_citations")]


@dlt.resource(write_disposition="merge", primary_key=["pipeline_name", "doi", "timestamp"])
def pipeline_citations(pipelines: list[str], github_headers: dict):
    yield from itertools.chain.from_iterable(
        _get_citations_for_pipeline(pipeline, github_headers) for pipeline in pipelines
    )


def main(*, destination="motherduck"):
    """
    Run the slack data ingestion pipeline

    Args:
        destination: dlt backend. Use 'motherduck' for production. Can use 'duckdb' for local testing
    """
    logger.info("Starting citation stats data pipeline...")

    # Initialize the pipeline with MotherDuck destination
    pipeline = dlt.pipeline(
        pipeline_name="citation_stats",
        destination=destination,
        dataset_name="citations",
    )

    # Run the pipeline
    load_info = pipeline.run(semanticscholar_source())

    # Log final summary using DLT's built-in statistics (similar to GitHub pipeline)
    log_pipeline_stats(pipeline, load_info)

    logger.info("Citation stats data pipeline completed successfully!")
