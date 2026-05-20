# Continuous Integration

## Purpose

This project keeps a GitHub Actions CI template under `docs/templates/ci.yml`.
The template mirrors the local validation contract without enabling live
provider access.

Do not copy the template into `.github/workflows/ci.yml` until the publishing
token has GitHub `workflow` scope. Keeping the template under `docs/templates/`
prevents push failures while still preserving the intended CI contract.

## Default Checks

The template runs:

```bash
python -m pytest -m "not integration_live" --cov=techno_search --cov-report=term-missing
python -m ruff check .
python -m mypy src
git diff --check
techno-search validate-all
techno-search health
techno-search operations-readiness-summary
techno-search operations-action-plan-summary
techno-search operations-action-resolution-summary
```

The workflow sets `TECHNO_SEARCH_ENABLE_LIVE_DATA=0`. CI must remain
non-networked by default and must not contact live providers, ingest real
observations, approve external submission, or claim detections. The operations
readiness summary is informational in CI; a `blocked_for_real_data`
recommendation is expected while real-data policy, provenance, licensing,
labeling, and external-review prerequisites remain incomplete. The action-plan
summary translates those blockers into local review tasks without clearing them
or authorizing external workflow. The action-resolution summary reports local
operator status records without clearing blockers or authorizing live data,
network access, or external submission. Its coverage fields must show every
current action-plan ID has a corresponding local resolution record.

## Promotion Checklist

Before copying the template into `.github/workflows/ci.yml`:

- confirm the publishing token has GitHub `workflow` scope
- confirm no live-data secrets or API keys are required
- confirm generated SQLite databases, logs, artifacts, and caches remain ignored
- run the local validation gate from `docs/VALIDATION.md`
- preserve conservative scientific language in workflow names and logs
