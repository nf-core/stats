# Regulatory

This folder contains resources developed by the regulatory working group at the nf-core hackathon
October 2025 in Barcelona. 

The goal was to collate pipeline metrics that are relevant for pipeline risk assessment in a regulatory context. 

We developed the following components: 
 * additional pipeline metrics (integrated into the main `dlt` data loading pipeline, not in this folder)
 * script to dump selected pipeline metrics into a json object (`get_stats.py`)
 * quarto reports summarizing metrics of a specific pipeline in a PDF document

## Get stats

To dump a current snapshot of the stats into a json object, follow these steps:

1. Obtain a motherduck token. The database is stored in the nf-core motherduck instance. You need a token
   with read permissions. Export it to the `MOTHERDUCK_TOKEN` env variable. 

2. Execute the python script with

   ```bash
   uv run get_stats.py
   ```

