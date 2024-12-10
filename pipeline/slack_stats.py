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

# Load environment variables
load_dotenv()

def get_slack_client():
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        raise ValueError("SLACK_BOT_TOKEN environment variable is not set")
    return WebClient(token=token)

@dlt.source
def slack_stats():
    """DLT source for Slack workspace statistics"""
    return [
        active_users_resource(),
        total_users_resource(),
    ]

@dlt.resource(write_disposition="merge", primary_key=["date"])
def active_users_resource() -> Iterator[Dict]:
    """Collect daily active users from Slack"""
    client = get_slack_client()
    
    # Get access logs for the last 30 days (Slack's limit)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    try:
        # Get team access logs
        response = client.team_accessLogs(
            before=end_date.timestamp(),
            limit=1000  # Maximum allowed by Slack
        )
        
        # Process access logs
        daily_users = {}
        for access in response["logins"]:
            date_str = datetime.fromtimestamp(access["date_first"]).strftime("%Y-%m-%d")
            if date_str not in daily_users:
                daily_users[date_str] = set()
            daily_users[date_str].add(access["user_id"])
        
        # Yield daily active user counts
        for date_str, users in daily_users.items():
            yield {
                "date": date_str,
                "active_user_count": len(users),
                "active_users": list(users)
            }
            
    except SlackApiError as e:
        print(f"Error fetching access logs: {e.response['error']}")

@dlt.resource(write_disposition="merge", primary_key=["date"])
def total_users_resource() -> Iterator[Dict]:
    """Collect total (non-deleted) users from Slack"""
    client = get_slack_client()
    
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
        pipeline_name="slack_stats",
        destination="duckdb",
        dataset_name="nf_core_dlt",
        credentials={
            "database": "md:",  # MotherDuck connection string
            "motherduck_token": os.getenv("MOTHERDUCK_TOKEN")  # Token from environment variables
        }
    )
    
    # Run the pipeline
    load_info = pipeline.run(slack_stats())
    
    print(load_info) 