#!/usr/bin/env sh
# Chains the Evidence data build into the dev server, used by `npm run dev:preview`
# and the Claude preview config (.claude/launch.json).
#
# `evidence sources` fetches data from MotherDuck and needs a token
# (EVIDENCE_SOURCE__nfcore_db__token — see AGENTS.md "Data source / MotherDuck caveat").
# Behaviour:
#   - token set:   build sources, then serve (a partial/failed build still serves)
#   - no token:    skip the fetch so the dev server starts instantly with no data,
#                  instead of hanging on a MotherDuck connection that can't authenticate
set -e

if [ -n "$EVIDENCE_SOURCE__nfcore_db__token" ]; then
  echo "[dev:preview] Building sources from MotherDuck…"
  evidence sources || echo "[dev:preview] some sources failed; serving with whatever built"
else
  echo "[dev:preview] EVIDENCE_SOURCE__nfcore_db__token not set — skipping sources; dashboard will show no data (see AGENTS.md)"
fi

exec evidence dev
