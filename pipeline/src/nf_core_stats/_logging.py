import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


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
