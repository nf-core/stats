---
name: Add DLT Data Source
description: Scaffold new DLT pipeline for data ingestion to MotherDuck
---

# Add DLT Data Source

## When to Use
- Adding new external data source (API, file, webhook)
- Creating new tables in MotherDuck database

## File Structure
```
pipeline/src/nf_core_stats/
├── __init__.py          # Add command registration
├── _<source>.py         # Optional: API helpers
└── <source>_pipeline.py # Main pipeline
```

## Pipeline Template

```python
"""DLT pipeline for <source> data."""

from collections.abc import Iterator
from typing import Annotated

import dlt

from ._logging import log_pipeline_stats, logger


@dlt.source(name="<source>")
def <source>_source():
    """Initialize <source> data source."""
    logger.info("Initialized <source> source")
    return [
        dlt.resource(<table_name>_resource(), name="<table_name>"),
    ]


@dlt.resource(write_disposition="merge", primary_key=["id"])
def <table_name>_resource() -> Iterator[dict]:
    """Collect <table_name> data."""
    # Fetch data from API/file/etc
    yield {"id": 1, "field": "value"}


def main(
    *,
    destination: str = "motherduck",
    # Add pipeline-specific params here
):
    """Run the <source> data ingestion pipeline.

    Args:
        destination: dlt backend. Use 'motherduck' for production. Can use 'duckdb' for local testing
    """
    logger.info("Starting <source> data pipeline...")

    pipeline = dlt.pipeline(
        pipeline_name="<source>_pipeline",
        destination=destination,
        dataset_name="<source>",
    )

    load_info = pipeline.run(<source>_source())
    log_pipeline_stats(pipeline, load_info)

    logger.info("<Source> data pipeline completed!")
```

## CLI Registration

Add to `pipeline/src/nf_core_stats/__init__.py`:
```python
from . import <source>_pipeline
app.command(<source>_pipeline.main, "<source>")
```

## Workflow Integration

Add to `.github/workflows/run_pipelines.yml` matrix:
```yaml
- pipeline: <source>
  uuid: <generate-new-uuid>  # for runitor monitoring
```

Or create separate workflow if pipeline needs special dependencies (like Nextflow).

## Write Dispositions

| Mode | Use When |
|------|----------|
| `merge` | Update existing rows by primary_key |
| `replace` | Full table reload each run |
| `append` | Insert-only, keep all history |

## Secrets Pattern

Environment variable: `SOURCES__<PIPELINE>__<SERVICE>__<KEY>`

Access in code:
```python
api_token: str = dlt.secrets["sources.<pipeline>.<service>.<key>"]
```

## Testing

```bash
cd pipeline
uv run nf_core_stats <source> --destination duckdb
```

## Checklist

1. [ ] Create `<source>_pipeline.py` with source + resources
2. [ ] Register CLI command in `__init__.py`
3. [ ] Add to workflow matrix (or create separate workflow)
4. [ ] Add secrets to GitHub repo settings
5. [ ] Create Evidence SQL sources for new tables
6. [ ] Test locally with `--destination duckdb`
