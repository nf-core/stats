import pandas as pd
import numpy as np

# Calculate pipeline status
def calculate_status(row):
    if row.get('archived', False):
        return 'Archived'
    elif not row.get('has_release', False):
        return 'In Development'
    else:
        if pd.notna(row['last_release_date']):
            days_since_release = (pd.Timestamp.now(tz='UTC') - row['last_release_date']).days
            if days_since_release < 180:
                return 'Active'
            elif days_since_release < 365:
                return 'Maintenance'
            else:
                return 'Legacy'
        else:
            return 'In Development'

# First attempt at defining the Pipeline Trust/Confidence Score
# Just a suggestion, open for discussion.
# Calculate Pipeline Trust Score
def calculate_trust_score(row):
    """
    Calculate a pipeline confidence/trust score (0-100) based on multiple metrics.
    
    Scoring components and their weights:
    1. Maintenance Activity (30%): Based on last release time
    2. Issue Resolution (25%): Based on closed issue ratio and median resolution time
    3. PR Management (20%): Based on closed PR ratio and median PR closure time
    4. Community Engagement (25%): Based on stars and forks
    """
    
    components = {}
    
    # Maintenance Activity
    if pd.notna(row.get('last_release_date')):
        days_since_release = (pd.Timestamp.now(tz='UTC') - row['last_release_date']).days
        # Exponential decay: score decreases as time increases
        # Half-life at 240 days (8 months)
        maintenance_score = 100 * np.exp(-days_since_release / 240)
    else:
        maintenance_score = 0  # No releases yet
    components['maintenance'] = maintenance_score
    
    # Issue Resolution (combination of closure rate and speed)
    issue_count = row.get('issue_count', 0)
    closed_issue_count = row.get('closed_issue_count', 0)
    median_issue_time = row.get('median_seconds_to_issue_closed')
    
    if pd.notna(issue_count) and issue_count > 0:
        # Closure rate (0-100)
        close_ratio = closed_issue_count / issue_count if pd.notna(closed_issue_count) else 0
        closure_score = close_ratio * 100
        
        # Resolution speed (exponential decay, half-life at 45 days)
        if pd.notna(median_issue_time):
            days_to_close = median_issue_time / 86400
            speed_score = 100 * np.exp(-days_to_close / 45)
        else:
            speed_score = 50  # Neutral if no data
        
        # Combined: 70% closure rate, 30% speed (closure more important)
        issue_resolution_score = 0.7 * closure_score + 0.3 * speed_score
    else:
        issue_resolution_score = 70  # Good default if no issues
    components['issue_resolution'] = issue_resolution_score
    
    # PR Management (combination of merge rate and review speed)
    pr_count = row.get('pr_count', 0)
    closed_pr_count = row.get('closed_pr_count', 0)
    median_pr_time = row.get('median_seconds_to_pr_closed')
    
    if pd.notna(pr_count) and pr_count > 0:
        # Merge rate (0-100)
        pr_close_ratio = closed_pr_count / pr_count if pd.notna(closed_pr_count) else 0
        merge_score = pr_close_ratio * 100
        
        # Review speed (exponential decay, half-life at 14 days)
        if pd.notna(median_pr_time):
            days_to_merge = median_pr_time / 86400
            review_speed_score = 100 * np.exp(-days_to_merge / 14)
        else:
            review_speed_score = 50  # Neutral if no data
        
        # Combined: 70% merge rate, 30% speed (merge rate more important)
        pr_management_score = 0.7 * merge_score + 0.3 * review_speed_score
    else:
        pr_management_score = 70
    components['pr_management'] = pr_management_score
    
    # Community Engagement (logarithmic scale for stars and forks)
    stars = row.get('stargazers_count', 0) if pd.notna(row.get('stargazers_count')) else 0
    forks = row.get('forks_count', 0) if pd.notna(row.get('forks_count')) else 0
    
    # Logarithmic scaling with more realistic thresholds
    # Stars: 50 stars = 50 points, 500 stars = 100 points
    star_score = min(100, (np.log1p(stars) / np.log1p(500)) * 100)
    
    # Forks: 20 forks = 50 points, 200 forks = 100 points
    fork_score = min(100, (np.log1p(forks) / np.log1p(200)) * 100)
    
    # Combined: 60% stars, 40% forks
    community_score = 0.6 * star_score + 0.4 * fork_score
    components['community'] = community_score
    
    # Calculate weighted final score
    weights = {
        'maintenance': 0.30,
        'issue_resolution': 0.25,
        'pr_management': 0.20,
        'community': 0.25,
    }
    
    final_score = sum(components[key] * weights[key] for key in weights.keys())
    
    # Store components for debugging
    row['_score_components'] = components
    
    return round(final_score, 1)