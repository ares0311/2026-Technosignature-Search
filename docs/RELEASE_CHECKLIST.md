# RELEASE CHECKLIST

## Purpose

Define a conservative release gate for repository updates.

This project is scientific software. A release or publication step must preserve uncertainty, provenance, negative evidence, and false-positive handling.

---

## Required Local Validation

Run from the project virtual environment:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src
git diff --check
```

---

## Artifact Checks

Before release, verify:

- candidate packet schemas parse
- report manifest schemas parse
- batch manifest schemas parse
- example reports regenerate cleanly
- score regression snapshots are reviewed when scores change
- benchmark run-result metadata is reviewed when validation run fixtures change
- calibration fixtures still route expected false positives conservatively
- generated packets include `config_version`
- generated packets include `schema_version`
- report manifests include `provenance_summary`
- live-provider request provenance includes service URL and cache key when applicable
- catalog cache policy and commit-path validator pass before real provider clients
- generated packets include the required disclaimer
- generated packets expose negative evidence and blocking issues
- background draft reports preserve limitations and keep external submission disabled
- persisted draft report manifests validate when draft reports are written
- user decision records do not imply submission approval unless explicitly recorded
- top-level SQLite logs validate one-run/one-outcome invariants
- generated `logs/*.sqlite3` databases are not committed
- SQLite review-safe exports preserve blockers, negative evidence, provenance, and uncertainty notes
- SQLite PRAGMA, backup, retention, and vacuum maintenance commands pass on local logs

Useful commands:

```bash
.venv/bin/techno-search validate-candidate examples/candidates/radio_clean_candidate.json
.venv/bin/techno-search validate-reports examples/reports
.venv/bin/techno-search schema-paths
.venv/bin/techno-search score-regression-summary
.venv/bin/techno-search catalog-cache-policy
.venv/bin/techno-search catalog-cache-validate docs/CATALOG_CACHE_POLICY.md
.venv/bin/techno-search sqlite-log-commit-guard
.venv/bin/techno-search sqlite-log-integrity-summary --db-path logs/techno_search.sqlite3
.venv/bin/techno-search sqlite-log-pragmas --db-path logs/techno_search.sqlite3
.venv/bin/techno-search sqlite-log-backup --db-path logs/techno_search.sqlite3
.venv/bin/techno-search sqlite-log-retention-summary --db-path logs/techno_search.sqlite3
.venv/bin/techno-search sqlite-log-vacuum --db-path logs/techno_search.sqlite3
.venv/bin/techno-search validate-sqlite-logs --db-path logs/techno_search.sqlite3
.venv/bin/techno-search validate-all
```

The `validate-all` output must include `catalog_cache_validation.ok: true`.

---

## Scientific Language Check

Do not claim a confirmed technosignature.

Use conservative language:

- candidate signal
- anomaly
- follow-up target
- technosignature-interest candidate

Avoid sensational or unsupported language.

---

## Live Data Check

Default validation must not require network access.

Only run live integrations when:

- the test is marked `integration_live`
- `TECHNO_SEARCH_ENABLE_LIVE_DATA=1` is set intentionally
- credentials and caches are excluded from git
- provenance is recorded

---

## GitHub Workflow Caveat

Do not add `.github/workflows/*.yml` unless the publishing token has GitHub `workflow` scope.

Until then, keep CI examples under:

```text
docs/templates/
```

Current template:

```text
docs/templates/ci.yml
```
