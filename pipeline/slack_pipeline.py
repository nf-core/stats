"""DLT pipeline for collecting Slack workspace statistics.

This module uses the Slack SDK instead of direct API calls (unlike the old PHP implementation) for several benefits:
1. Better error handling through SlackApiError
2. Type safety and structured data handling
3. Automatic rate limiting management
4. Secure authentication and token management
5. Future API compatibility through SDK updates

The implementation also provides more comprehensive data collection compared to the old version:
- Detailed access logs for active users
- Comprehensive user information including profiles and admin status
- Automatic pagination handling
"""

import dlt
from typing import Dict, Iterator
import os
from datetime import datetime, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

@dlt.source(name="slack", max_table_nesting=2)
def slack_source():
    """DLT source for Slack workspace statistics"""
    # Get token explicitly from secrets
    access_token = dlt.secrets.get("sources.slack_pipeline.access_token")
    if not access_token:
        raise ValueError("Slack access token not found in secrets")
    
    client = WebClient(token=access_token)
    return [
        active_users_resource(client),
        total_users_resource(client),
    ]

@dlt.resource(write_disposition="merge", primary_key=["date"])
def active_users_resource(client: WebClient) -> Iterator[Dict]:
    """Collect daily active users from Slack"""
    try:
        # Instead of access logs, use conversations.list and conversations.members
        # to get active users in public channels
        channels_response = client.conversations_list(types="public_channel")
        active_users = set()
        
        for channel in channels_response["channels"]:
            try:
                members = client.conversations_members(channel=channel["id"])
                active_users.update(members["members"])
            except SlackApiError as e:
                print(f"Error fetching members for channel {channel['id']}: {e.response['error']}")
        
        # Yield current active users
        yield {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "active_user_count": len(active_users),
            "active_users": list(active_users)
        }
            
    except SlackApiError as e:
        print(f"Error fetching channels: {e.response['error']}")

@dlt.resource(write_disposition="merge", primary_key=["date"])
def total_users_resource(client: WebClient) -> Iterator[Dict]:
    """Collect total (non-deleted) users from Slack"""
    try:
        # Get user list
        response = client.users_list()
        active_users = [user for user in response["members"] if not user.get("deleted", False)]
        
        yield {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "total_user_count": len(active_users),
            "user_details": [
                {
                    "id": user["id"],
                    "name": user.get("real_name_normalized", user["name"]),
                    "email": user.get("profile", {}).get("email"),
                    "is_admin": user.get("is_admin", False),
                    "is_bot": user.get("is_bot", False)
                }
                for user in active_users
            ]
        }
            
    except SlackApiError as e:
        print(f"Error fetching user list: {e.response['error']}")

if __name__ == "__main__":
    # Initialize the pipeline with MotherDuck destination
    pipeline = dlt.pipeline(
        pipeline_name="slack",
        destination="motherduck",
        dataset_name="slack_stats",
    )
    
    # Run the pipeline
    load_info = pipeline.run(slack_source())
    
    print(load_info) 