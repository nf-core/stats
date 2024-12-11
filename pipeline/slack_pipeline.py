"""DLT pipeline for collecting Slack workspace statistics.

This module uses the Slack SDK instead of direct API calls (unlike the old PHP implementation) for several benefits:
1. Better error handling through SlackApiError
2. Type safety and structured data handling
3. Automatic rate limiting management
4. Secure authentication and token management
5. Future API compatibility through SDK updates
"""

import dlt
from typing import Dict, Iterator
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

@dlt.source(name="slack")
def slack_source():
    """DLT source for Slack workspace statistics"""
    # Get token explicitly from secrets
    access_token = dlt.secrets.get("sources.slack_pipeline.access_token")
    if not access_token:
        raise ValueError("Slack access token not found in secrets")
    
    client = WebClient(token=access_token)
    return slack_stats(client)

@dlt.resource(write_disposition="merge", primary_key=["timestamp"])
def slack_stats(client: WebClient) -> Iterator[Dict]:
    """Collect combined Slack statistics in a single table"""
    try:
        # Get total users
        users_response = client.users_list()
        active_account_users = [user for user in users_response["members"] if not user.get("deleted", False)]
        total_users = len(active_account_users)

        # Get active users from channels
        channels_response = client.conversations_list(types="public_channel")
        active_channel_users = set()
        
        for channel in channels_response["channels"]:
            try:
                members = client.conversations_members(channel=channel["id"])
                active_channel_users.update(members["members"])
            except SlackApiError as e:
                print(f"Error fetching members for channel {channel['id']}: {e.response['error']}")

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
            
    except SlackApiError as e:
        print(f"Error fetching Slack data: {e.response['error']}")

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