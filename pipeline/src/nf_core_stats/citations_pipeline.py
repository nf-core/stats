import logging
from collections.abc import Iterator
from datetime import datetime, timedelta
from typing import Literal
from cyclopts import run

import dlt
import requests
from dlt.sources.helpers.requests import Client
from dotenv import load_dotenv

load_dotenv()



def _get_pipeline_names():
    pipeline_names_url = "https://raw.githubusercontent.com/nf-core/website/main/public/pipeline_names.json"
    try:
        pipeline_names = github_request(pipeline_names_url, headers).json()
    except requests.RequestException as e:
        logger.warning(f"Failed to get pipeline names from nf-core website: {e}")
        return

@dlt.source(name="semanticscholar")
def semanticscholar_source():



@dlt.resource(write_disposition="merge", primary_key=["pipeline_name", "doi", "timestamp"])
def pipeline_citations(pipelines):
    from semanticscholar import SemanticScholar

    # Initialize client
    sch = SemanticScholar()

    # Get a paper by its DOI or Semantic Scholar ID
    paper_id = "10.1101/2021.08.29.458094"

    paper = sch.get_paper(paper_id)

    # Print paper information
    print("Title:", paper.title)
    print("Citation Count:", paper["citationCount"])
    print("Influential Paper Citation Count:", paper["influentialCitationCount"])
    yield {
        "pipeline_name": pipeline["name"],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "doi": doi
    }
    pass


def log_pipeline_stats(pipeline, load_info):
    """Log pipeline completion statistics (similar to GitHub pipeline)"""
    logger.info("=== PIPELINE COMPLETION SUMMARY ===")

    # Get row counts from the normalize info
    if pipeline.last_trace and pipeline.last_trace.last_normalize_info:
        row_counts = pipeline.last_trace.last_normalize_info.row_counts
        total_rows = sum(row_counts.values())
        logger.info(f"Total rows processed: {total_rows}")

        for table_name, count in row_counts.items():
            logger.info(f"  {table_name}: {count} rows")
    else:
        logger.info("No row count information available")

    # Log package information from load_info
    if load_info.load_packages:
        for package in load_info.load_packages:
            logger.info(f"Load package {package.load_id}: {package.state}")
            for job_type, jobs in package.jobs.items():
                if jobs:
                    logger.info(f"  {job_type}: {len(jobs)} jobs")

    logger.info("=== DLT LOAD INFO ===")
    print(load_info)


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


if __name__ == "__main__":
    run(main)
