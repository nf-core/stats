"""DLT pipeline for collecting Twitter (X) account statistics.

This module replaces the old PHP Twitter stats collection with a modern DLT implementation.
Key differences from the PHP version:
1. Uses Twitter API v2 instead of v1.1
2. Implements proper error handling
3. Stores data in a structured format
4. Uses DLT's incremental loading capabilities
"""

import dlt
from typing import Dict, Iterator
import os
from datetime import datetime
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_twitter_headers():
    """Get Twitter API headers with bearer token authentication"""
    access_token = dlt.secrets.get("sources.twitter.bearer_token")
    if not access_token:
        raise ValueError("TWITTER_BEARER_TOKEN environment variable is not set")
    return {
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "nf-core-stats/1.0"
    }

@dlt.source(name="twitter")
def twitter_source(username: str = "nf_core"):
    """DLT source for Twitter account statistics"""
    return dlt.resource(
        twitter_stats_resource(username),
        name="account_stats",
        write_disposition="merge",
        primary_key=["timestamp"]
    )

def twitter_stats_resource(username: str) -> Iterator[Dict]:
    """Resource that fetches Twitter account statistics
    
    Args:
        username: Twitter username to fetch stats for
    
    Yields:
        Dict containing Twitter metrics with timestamp
    """
    # Twitter API v2 endpoint for user lookup
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    
    # Request user fields we want to track
    params = {
        "user.fields": "public_metrics"
    }
    
    try:
        # Make API request
        response = requests.get(
            url,
            headers=get_twitter_headers(),
            params=params
        )
        response.raise_for_status()
        
        # Extract metrics from response
        data = response.json()["data"]
        metrics = data["public_metrics"]
        
        # Create stats entry with timestamp
        stats = {
            "followers_count": metrics["followers_count"],
            "following_count": metrics["following_count"],
            "tweet_count": metrics["tweet_count"],
            "listed_count": metrics["listed_count"],
            "timestamp": datetime.now().timestamp()
        }
        
        yield stats

    except requests.exceptions.RequestException as e:
        print(f"Error fetching Twitter data: {e}")
        if hasattr(e.response, 'json'):
            print(f"Twitter API error: {e.response.json()}")

if __name__ == "__main__":
    # Initialize the pipeline with MotherDuck destination
    pipeline = dlt.pipeline(
        pipeline_name="twitter_stats",
        destination="motherduck",
        dataset_name="twitter"
    )
    
    # Run the pipeline
    load_info = pipeline.run(twitter_source())
    
    print(load_info)