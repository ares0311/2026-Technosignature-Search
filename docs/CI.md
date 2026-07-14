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
techno-search operations-readiness-summary
techno-search operations-action-plan-summary
techno-search operations-action-resolution-summary
techno-search operations-blocker-detail-summary
techno-search operations-blocker-review-summary
techno-search operations-blocker-followup-summary
techno-search operations-blocker-followup-progress-summary
techno-search operations-blocker-progress-review-summary
techno-search operations-blocker-progress-next-actions-summary
techno-search operations-blocker-progress-execution-summary
techno-search operations-blocker-progress-execution-review-summary
techno-search operations-blocker-progress-execution-followup-summary
```

The launcher distributes pytest files across six xdist workers, aggregates
package coverage, and, after the tests pass, runs Ruff, mypy, and `validate-all`
concurrently. It is the default for future full-suite CI work; direct serial
pytest remains appropriate only for small focused reproductions or a verified
shared-state incompatibility.

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
current action-plan ID has a corresponding local resolution record. The
blocker-detail summary expands current action-plan items into fixture-backed
source records for review without clearing blockers or authorizing external
workflow. The blocker-review summary records local operator review status for
those evidence bundles while preserving residual blockers and zero live-data
and external-submission authorization counts. The blocker-followup summary
derives next local operator actions from those review records without clearing
blockers or changing authorization gates. The blocker-followup progress summary
records local progress notes against those next actions while preserving
residual blockers and disabled authorization gates. The blocker progress-review
summary reviews only unresolved progress records, leaves verified-local items
closed, and keeps live-data and external-submission authorization counts at
zero. The blocker progress next-actions summary turns unresolved progress-review
records into an ordered local work queue without clearing blockers or changing
authorization gates. The blocker progress-execution summary records local
execution notes against that queue while preserving residual blockers, verified
local exclusions, and disabled authorization gates. The blocker
progress-execution review summary reviews those execution notes without
clearing blockers or changing authorization gates. The blocker
progress-execution follow-up summary plans local follow-up for those reviewed
execution notes while preserving residual blockers, verified-local exclusions,
and disabled authorization gates.

## Promotion Checklist

Before copying the template into `.github/workflows/ci.yml`:

- confirm the publishing token has GitHub `workflow` scope
- confirm no live-data secrets or API keys are required
- confirm generated SQLite databases, logs, artifacts, and caches remain ignored
- run the local validation gate from `docs/VALIDATION.md`
- preserve conservative scientific language in workflow names and logs
