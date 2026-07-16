# Continuous Integration

## Purpose

This project keeps a GitHub Actions CI template under `docs/templates/ci.yml`.
The template mirrors the local validation contract without enabling live
provider access.

Do not copy the template into `.github/workflows/ci.yml` until the publishing
token has GitHub `workflow` scope. Keeping the template under `docs/templates/`
prevents push failures while still preserving the intended CI contract.

## Default Checks

The template uses the canonical six-worker/six-shard validation launcher, then
runs the remaining operator summaries:

```bash
python scripts/run_parallel_validation.py -- -m "not integration_live"
git diff --check
techno-search health
```

The launcher distributes pytest files across six xdist workers, aggregates
package coverage, and, after the tests pass, runs the base-aware app-version
gate, Ruff, mypy, and `validate-all`
concurrently. It is the default for future full-suite CI work; direct serial
pytest remains appropriate only for small focused reproductions or a verified
shared-state incompatibility.

The workflow sets `TECHNO_SEARCH_ENABLE_LIVE_DATA=0`. CI must remain
non-networked by default and must not contact live providers, ingest real
observations, approve external submission, or claim detections.

## Promotion Checklist

Before copying the template into `.github/workflows/ci.yml`:

- confirm the publishing token has GitHub `workflow` scope
- confirm no live-data secrets or API keys are required
- confirm generated SQLite databases, logs, artifacts, and caches remain ignored
- run the local validation gate from `docs/VALIDATION.md`
- preserve conservative scientific language in workflow names and logs
