"""DLT pipeline for collecting Slack workspace statistics.

This module uses the Slack SDK instead of direct API calls (unlike the old PHP implementation) for several benefits:
1. Better error handling through SlackApiError
2. Type safety and structured data handling
3. Automatic rate limiting management
4. Secure authentication and token management
5. Future API compatibility through SDK updates
"""

from collections.abc import Iterator
from datetime import datetime
from typing import Dict

import dlt
from slack_sdk import WebClient


@dlt.source(name="slack")
def slack_source(api_token: str = dlt.secrets.value) -> Iterator[Dict]:
    """DLT source for Slack workspace statistics"""
    # Add debug logging
    print(f"Initializing Slack client with token starting with: {api_token[:5]}...")
    
    client = WebClient(token=api_token)
    
    # Test the connection
    auth_test = client.auth_test()
    print(f"Successfully authenticated as: {auth_test['user']} in workspace: {auth_test['team']}")

    return slack_stats_resource(client)

@dlt.resource(name="workspace_stats", write_disposition="merge", primary_key=["timestamp"])
def slack_stats_resource(client: WebClient) -> Iterator[Dict]:
    """Collect combined Slack statistics in a single table"""
    # Get total users
    users_response = client.users_list()
    active_account_users = [user for user in users_response["members"] if not user.get("deleted", False)]
    total_users = len(active_account_users)

    # Get active users from channels
    channels_response = client.conversations_list(types="public_channel")
    active_channel_users = set()
    
    for channel in channels_response["channels"]:
        members = client.conversations_members(channel=channel["id"])
        active_channel_users.update(members["members"])

    active_users = len(active_channel_users)
    inactive_users = total_users - active_users

    # Yield combined stats
    yield {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": inactive_users,
        # Optionally keep detailed user info as nested data
        "user_details": [
            {
                "id": user["id"],
                "name": user.get("real_name_normalized", user["name"]),
                "email": user.get("profile", {}).get("email"),
                "is_admin": user.get("is_admin", False),
                "is_bot": user.get("is_bot", False),
                "is_active": user["id"] in active_channel_users
            }
            for user in active_account_users
        ]
    }

if __name__ == "__main__":
    # Initialize the pipeline with MotherDuck destination
    pipeline = dlt.pipeline(
        pipeline_name="slack_stats",
        destination="motherduck",
        dataset_name="slack",
    )
    
    # Run the pipeline
    load_info = pipeline.run(slack_source())
    print(load_info) 