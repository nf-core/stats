# AGENTS.md

General project, build, and architecture guidance lives in `README.md`, `CLAUDE.md`,
`pipeline/README.md`, and `docs/architecture.md`. Read those first.

## Cursor Cloud specific instructions

This repo has two services:

1. **Evidence.dev frontend** (root) — the data dashboard. Node ≥18. Standard commands are in
   `package.json` (`npm run sources`, `npm run dev`, `npm run build`). Dev server runs on port 3000.
2. **DLT data pipelines** (`pipeline/`) — Python collectors (GitHub / Slack / citations), managed
   with `uv`. Standard commands are in `pipeline/README.md` (`uv run nf_core_stats <cmd> --help`).
   Lint with `uvx ruff check` (config in `pipeline/pyproject.toml`); full hooks in `.pre-commit-config.yaml`.

The update script already installs `uv`, runs `npm install`, and `uv sync --project pipeline`.

### Data source / MotherDuck caveat (most important)

The committed `sources/nfcore_db/connection.yaml` points at **MotherDuck** (cloud DuckDB, database
`nf_core_stats_bot`). `npm run sources` and `npm run build` need a MotherDuck token to fetch data;
without it those queries fail. There is no local Postgres/Redis to start — the only data backend is MotherDuck.

Supply the token with the env var **`EVIDENCE_SOURCE__nfcore_db__token`** (set it to the MotherDuck
token, e.g. `export EVIDENCE_SOURCE__nfcore_db__token="$MOTHERDUCK_TOKEN"`), then run `npm run sources`
/ `npm run dev`. Gotcha: do **not** put the raw token in `sources/nfcore_db/connection.options.yaml` —
Evidence runs that file's values through a base64 decode, so a raw JWT makes it throw
"Error parsing connection.options.yaml". The env-var form is set verbatim and is the reliable path.
With the token, all source queries (GitHub, Slack, Twitter, traffic, issues, contributors) populate.

#### Supplying the token via 1Password + direnv (recommended)

The token lives in **1Password**; share it between developers and agents by *reference*, never by
value. The committed `.envrc` resolves it with the 1Password CLI (`op`) and exports
`EVIDENCE_SOURCE__nfcore_db__token`, so anything launched from this directory inherits it — the
secret never lands on disk and **no agent config holds the token**.

One-time per machine: install `direnv` + `op`, sign in to `op`, confirm the `op://…` reference in
`.envrc` matches where the team stores the token, then run `direnv allow`. After that
`npm run sources`, `npm run dev:preview`, and the Claude preview pick the token up automatically.

Per runtime:

- **Claude Code / Cursor (local):** launched from a shell in this repo, so they inherit the direnv
  environment — nothing else to configure. If you launch the desktop app *outside* a direnv shell,
  start it from a terminal in this repo, or (Claude only) paste the raw token into the gitignored
  `.claude/settings.local.json` `env` block as a fallback.
- **Cursor Cloud / other headless agents:** no interactive `op`. Set
  `EVIDENCE_SOURCE__nfcore_db__token` directly in the environment settings, or use an `op`
  service-account token (`OP_SERVICE_ACCOUNT_TOKEN`) with `op run`.
- **CI / Netlify:** unchanged. GitHub Actions reads `secrets.MOTHERDUCK_TOKEN`
  (`.github/workflows/run_pipelines.yml`); the Netlify build reads its own env var set in the
  Netlify UI. Never commit the token.

### Running fully locally without MotherDuck

You can exercise both services end-to-end without the MotherDuck token:

- The DLT CLI resolves `SOURCES__GITHUB_PIPELINE__GITHUB__API_TOKEN` at **import time**, so even
  `--help` fails unless it is set. In Cloud, `gh` is authenticated, so
  `export SOURCES__GITHUB_PIPELINE__GITHUB__API_TOKEN=$(gh auth token)` works for the `github` and
  `citations` pipelines (the `slack` pipeline needs a real Slack admin token).
- Run a pipeline into a local DuckDB file named `nf_core_stats_bot.duckdb` so the `USE nf_core_stats_bot;`
  prefix in `sources/nfcore_db/*.sql` resolves (DuckDB's catalog name is the file stem):
  `DESTINATION__DUCKDB__CREDENTIALS="$PWD/nf_core_stats_bot.duckdb" uv run nf_core_stats github --destination duckdb --resources nfcore_pipelines --resources org_members`
- Temporarily point the frontend at that file (do **not** commit this) by setting
  `sources/nfcore_db/connection.yaml` to `type: duckdb` with `options.filename` **relative to the
  source directory** (e.g. `../../pipeline/nf_core_stats_bot.duckdb`), then `npm run sources && npm run dev`.

Note: several source queries reference tables only filled by heavier pipeline runs
(`github.traffic_stats`, `github.issue_stats`, `github.contributor_stats`, `slack.workspace_stats`,
legacy `twitter.account_stats`) and one references a legacy `nf_core_dev` catalog (`pipeline_timeline`).
These error when that data is absent — that is expected, not a setup failure. Pages backed only by
`github.nfcore_pipelines` / `github.org_members` (e.g. `/code/pipelines`) render fully with just the
lightweight pipeline run above.
