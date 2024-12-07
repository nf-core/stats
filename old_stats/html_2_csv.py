# /// script
# dependencies = [
#   "pandas",
# "lxml",
# ]
# ///

import pandas as pd

# Read the HTML table
# If the HTML is in a file:
df = pd.read_html('contributor_leaderboard_table.html', header=0)[0]

# If you have the HTML as a string, save it to a file first or use:
# df = pd.read_html(html_string)[0]

# The table has these columns:
# 1. GitHub username (from the <a> tag)
# 2. Progress bar data (from the title attribute)
# 3. Most active repo (from the <a> tag)

# Save to CSV
df.to_csv('contributor_leaderboard.csv', index=False)