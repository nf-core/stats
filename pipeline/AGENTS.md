# AGENTS.md — `pipeline/`

DLT data pipelines (GitHub / Slack / citations / newsletter), managed with `uv`.
Commands are in `pipeline/README.md` (`uv run nf_core_stats <cmd> --help`).
Lint with `uvx ruff check` (config in `pipeline/pyproject.toml`).

General project, build, and architecture guidance lives in the root `AGENTS.md`,
`README.md`, `CLAUDE.md`, and `docs/architecture.md`.

## dlt reference

For dlt-specific work — pagination, incremental loading, rate-limit/429 handling, and
debugging a pipeline run — the dltHub AI harness cheatsheet indexes the relevant skills:
<https://dlthub.com/ai-harness.md>

Directly useful pages:

- [REST API helpers / rate limits](https://dlthub.com/docs/dlt-ecosystem/verified-sources/rest_api/advanced#handling-api-rate-limits)
- [REST API incremental loading](https://dlthub.com/docs/dlt-ecosystem/verified-sources/rest_api/basic#incremental-loading)

Note: these `rest_api` docs describe dlt's *declarative* source. This project uses
hand-rolled `@dlt.resource` functions with `dlt.current.source_state()` for incremental
state, so the declarative config is reference material, not a drop-in.

## GitHub rate limits

`_github.py` configures the dlt requests client (`request_max_attempts=5`, backoff,
`raise_for_status=False`), so 429s are retried with `Retry-After` honoured automatically.

Do **not** gate work on `GET /rate_limit` as a preflight. Its reported `remaining`/`used`
can diverge substantially from the quota actually charged to subsequent calls, so a
"healthy" reading does not mean the next request will succeed. React to real `403`/`429`
responses instead.

GitHub also enforces **secondary rate limits** on bursty sequential traffic. These 403 with
their own `Retry-After`/reset, independent of the core bucket — a core bucket that still
reports thousands of remaining calls proves nothing about a secondary limit.

On any rate-limit-shaped `403` (remaining `0`, a `Retry-After` header, or a "secondary rate
limit" body marker) or a post-retry `429`, `raise_for_github_errors` raises `RateLimitError`.
Per-repo/per-item handlers **must** re-raise it (`except RateLimitError: raise` above the
existing `except requests.RequestException`) instead of swallowing it into a `continue`, so
`main()` stops the run. Otherwise a limited run fires thousands of doomed requests and still
goes green. Every resource is `write_disposition="merge"` with a `primary_key`, so an aborted
run resumes cleanly on the next schedule.

At the `pipeline.run()` boundary you cannot catch `RateLimitError` directly: dlt wraps
exceptions raised inside a resource generator as `PipelineStepFailed` ->
`ResourceExtractionError` -> `RateLimitError`. Use `find_rate_limit_error(exc)` to walk the
cause chain instead (never string-match the message).
