# Deprecating nf-core/strict-syntax-health

The strict syntax health dashboard has been migrated into [nf-core/stats](https://github.com/nf-core/stats).

## After the stats PR merges

1. Update `README.md` in `nf-core/strict-syntax-health` to point at the live stats dashboard URL (e.g. `https://nf-co.re/stats/code/strict_syntax` or the Netlify deploy URL).
2. Disable the nightly workflow in `.github/workflows/lint-pipelines.yml` (delete the file or remove the `schedule` trigger).
3. Archive the repository or add an archive notice in the repo description.
4. Close open issues with a link to the stats repo and Evidence page.

## Historical data

Historical trend JSON from the old repo can be backfilled into MotherDuck:

```bash
cd pipeline
git clone --depth 1 https://github.com/nf-core/strict-syntax-health /tmp/strict-syntax-health
uv run nf_core_stats strict-syntax --backfill-history /tmp/strict-syntax-health/lint_results --destination motherduck
```
