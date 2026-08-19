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
On a `403` with `X-RateLimit-Remaining: 0`, `github_request` fails fast on purpose: every
resource is `write_disposition="merge"` with a `primary_key`, so an aborted run resumes
cleanly on the next schedule. Do not convert that fail-fast into a silent `continue`.

Do **not** gate work on `GET /rate_limit` as a preflight. Its reported `remaining`/`used`
can diverge substantially from the quota actually charged to subsequent calls, so a
"healthy" reading does not mean the next request will succeed. React to real `403`/`429`
responses instead.
