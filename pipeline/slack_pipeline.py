"""DLT pipeline for collecting Slack workspace statistics.

This module uses the Slack SDK and team.billableInfo API for several benefits:
1. Better error handling through SlackApiError
2. Type safety and structured data handling
3. Automatic rate limiting management
4. Secure authentication and token management
5. Future API compatibility through SDK updates
6. Uses Slack's official billing definition of active users

Token Requirements:
- Requires an admin user token with 'admin' scope to access team.billableInfo API
- Bot tokens are not supported and will cause the pipeline to fail
- User tokens without admin scope will also cause the pipeline to fail
"""

import logging
from collections.abc import Iterator
from datetime import datetime
from typing import Any, Callable

import dlt
from cyclopts import run
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Configuration constants
SLACK_API_LIMIT = 1000


def paginate_slack_api(api_call: Callable, data_key: str, description: str, **kwargs) -> list[Any]:
    """
    Generic pagination handler for Slack API calls

    Args:
        api_call: The Slack API method to call
        data_key: The key in the response containing the data (e.g., 'members', 'channels')
        description: Description for logging (e.g., 'users', 'channels')
        **kwargs: Additional arguments to pass to the API call

    Returns:
        List of all paginated results
    """
    all_results = []
    cursor = None

    while True:
        try:
            # Add cursor and limit to kwargs if not already present
            call_kwargs = {**kwargs, "cursor": cursor, "limit": SLACK_API_LIMIT}
            response = api_call(**call_kwargs)

            if not response.get("ok"):
                logger.error(f"Failed to get {description}: {response.get('error', 'Unknown error')}")
                break
            batch_data = response.get(data_key, [])
            all_results.extend(batch_data)

            # Check if there are more pages
            response_metadata = response.get("response_metadata", {})
            cursor = response_metadata.get("next_cursor")

            logger.info(f"Retrieved {len(batch_data)} {description} in this batch (total so far: {len(all_results)})")

            if not cursor:
                break

        except SlackApiError as e:
            logger.error(f"Slack API error getting {description}: {e}")
            break

    return all_results


def get_active_users_from_billing_info(client: WebClient, valid_user_ids: set[str]) -> set[str]:
    """Get active users using team.billableInfo API"""
    logger.info("Using team.billableInfo API to determine active users")

    try:
        # Get all billing info with pagination
        all_billing_info = {}
        cursor = None

        while True:
            response = client.team_billableInfo(cursor=cursor, limit=SLACK_API_LIMIT)

            if not response.get("ok"):
                raise ValueError(f"Failed to get billable info: {response.get('error', 'Unknown error')}")

            billing_info_batch: dict[str, Any] = response.get("billable_info", {})
            all_billing_info.update(billing_info_batch)

            response_metadata: dict[str, Any] = response.get("response_metadata", {})
            cursor = response_metadata.get("next_cursor")
            if not cursor:
                break

        logger.info(f"Retrieved billing info for {len(all_billing_info)} users")

        # Find active users
        active_users = {
            user_id
            for user_id, billing_info in all_billing_info.items()
            if billing_info.get("billing_active", False) and user_id in valid_user_ids
        }

        logger.info(f"Found {len(active_users)} billing-active users")
        return active_users

    except SlackApiError as e:
        if "not_allowed_token_type" in str(e):
            logger.error("team.billableInfo requires admin user token (not bot token)")
        elif "missing_scope" in str(e):
            logger.error("team.billableInfo requires 'admin' scope")
        else:
            logger.error(f"team.billableInfo API error: {e}")
        raise


def create_user_detail(user: dict[str, Any], active_user_ids: set[str]) -> dict[str, Any]:
    """Create user detail dictionary from user data"""
    return {
        "id": user["id"],
        "name": user.get("real_name_normalized", user["name"]),
        "email": user.get("profile", {}).get("email"),
        "is_admin": user.get("is_admin", False),
        "is_bot": user.get("is_bot", False),
        "is_active": user["id"] in active_user_ids,
    }


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


@dlt.source(name="slack")
def slack_source(api_token: str = dlt.secrets.value) -> list[Any]:
    """DLT source for Slack workspace statistics"""
    # Add debug logging
    logger.info(f"Initializing Slack client with token starting with: {api_token[:5]}...")

    client = WebClient(token=api_token)

    try:
        # Test the connection
        auth_test = client.auth_test()
        logger.info(f"Successfully authenticated as: {auth_test['user']} in workspace: {auth_test['team']}")
    except SlackApiError as e:
        logger.error(f"Failed to authenticate with Slack: {e}")
        raise

    return [slack_stats_resource(client)]


@dlt.resource(name="workspace_stats", write_disposition="merge", primary_key=["timestamp"])
def slack_stats_resource(client: WebClient) -> Iterator[dict[str, Any]]:
    """Collect combined Slack statistics in a single table"""
    try:
        # Get all users (excluding deleted ones)
        all_members = paginate_slack_api(client.users_list, "members", "users")
        if not all_members:
            return

        active_account_users = [user for user in all_members if not user.get("deleted", False)]
        valid_user_ids = {user["id"] for user in active_account_users}

        logger.info(f"Total users: {len(active_account_users)}")

        # Get billing-active users
        active_user_ids = get_active_users_from_billing_info(client, valid_user_ids)
        active_users = len(active_user_ids)
        inactive_users = len(active_account_users) - active_users

        logger.info(f"Active users: {active_users}, Inactive users: {inactive_users}")

        # Yield stats
        yield {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_users": len(active_account_users),
            "active_users": active_users,
            "inactive_users": inactive_users,
            "user_details": [create_user_detail(user, active_user_ids) for user in active_account_users],
        }

    except Exception as e:
        logger.error(f"Error collecting Slack stats: {e}")
        raise


def main(*, destination="motherduck"):
    """
    Run the slack data ingestion pipeline

    Args:
        destination: dlt backend. Use 'motherduck' for production. Can use 'duckdb' for local testing
    """
    logger.info("Starting Slack data pipeline...")

    # Initialize the pipeline with MotherDuck destination
    pipeline = dlt.pipeline(
        pipeline_name="slack_stats",
        destination=destination,
        dataset_name="slack",
    )

    # Run the pipeline
    load_info = pipeline.run(slack_source())

    # Log final summary using DLT's built-in statistics (similar to GitHub pipeline)
    log_pipeline_stats(pipeline, load_info)

    logger.info("Slack data pipeline completed successfully!")


if __name__ == "__main__":
    run(main)
