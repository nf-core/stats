# Regulatory report (planned, not yet implemented)

Design notes for a future workflow. Kept as Markdown rather than `.yml` because a
comments-only workflow file fails GitHub's parser ("workflow is empty") and reports
a failed run on every push.

On pipeline release:

- Pull from MotherDuck
- Dump to CSV
- Build the report with Quarto
- Attach the report as an artifact to the GitHub pipeline release
