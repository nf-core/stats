-- Create the output table
CREATE TABLE github_contributions AS
WITH raw_data AS (
  SELECT regexp_extract(line, '\{\s*x:\s*''([^'']+)''\s*,\s*y:\s*(\d+)\s*\}', 1) as date,
         CAST(regexp_extract(line, '\{\s*x:\s*''([^'']+)''\s*,\s*y:\s*(\d+)\s*\}', 2) AS INTEGER) as commits
  FROM read_csv_auto('sources/stats_static/gh_contribs.csv', lines=true)
  WHERE line LIKE '%{%x:%'
)
SELECT date, commits 
FROM raw_data 
WHERE date IS NOT NULL
ORDER BY date;

-- Export to CSV
-- SELECT * FROM github_contributions;