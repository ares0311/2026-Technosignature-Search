# VALIDATION

## Purpose

Central guide for local validation, schema checks, score regression snapshots, and example regeneration.

Validation is a scientific guardrail. It helps keep outputs reproducible, conservative, and explicit about false positives.

---

## Local Validation Gate

Run:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src
git diff --check
```

---

## CLI Validators

Validate one candidate:

```bash
.venv/bin/techno-search validate-candidate examples/candidates/radio_clean_candidate.json
```

Validate generated reports:

```bash
.venv/bin/techno-search validate-reports examples/reports
```

Run local validation summaries:

```bash
.venv/bin/techno-search validate-all
```

Print a compact local health dashboard:

```bash
.venv/bin/techno-search validation-summary
```

Validate catalog cache commit paths:

```bash
.venv/bin/techno-search catalog-cache-validate docs/CATALOG_CACHE_POLICY.md
```

`validate-all` includes a `catalog_cache_validation` block for Git-tracked paths.
Use `catalog-cache-validate` directly for pre-commit checks on a proposed path list.

---

## Schemas

Schema artifact paths:

```bash
.venv/bin/techno-search schema-paths
```

Committed schemas:

- `schemas/candidate_packet.schema.json`
- `schemas/report_manifest.schema.json`
- `schemas/batch_manifest.schema.json`
- `schemas/review_queue.schema.json`
- `schemas/consensus_labels.schema.json`
- `schemas/consensus_export.schema.json`
- `schemas/validation_dataset_manifest.schema.json`
- `schemas/benchmark_metadata.schema.json`
- `schemas/benchmark_run_results.schema.json`
- `schemas/background_targets.schema.json`
- `schemas/background_search_ledger.schema.json`
- `schemas/background_reviewed_log.schema.json`
- `schemas/background_needs_follow_up_log.schema.json`
- `schemas/background_follow_up_tests.schema.json`
- `schemas/background_draft_follow_up_reports.schema.json`
- `schemas/background_draft_report_manifest.schema.json`
- `schemas/background_report_readiness.schema.json`
- `schemas/background_user_decisions.schema.json`
- `schemas/candidate_extraction_handoff.schema.json`
- `schemas/validation_readiness.schema.json`

---

## Score Regression Snapshots

Review snapshot coverage:

```bash
.venv/bin/techno-search score-regression-summary
```

Review synthetic false-positive class coverage:

```bash
.venv/bin/techno-search false-positive-summary
```

Review synthetic calibration fixture coverage by track:

```bash
.venv/bin/techno-search calibration-track-summary
```

Review synthetic injection-recovery fixture coverage:

```bash
.venv/bin/techno-search injection-recovery-summary
```

Review synthetic reliability-curve fixture coverage:

```bash
.venv/bin/techno-search reliability-summary
```

Review synthetic precision-recall fixture coverage:

```bash
.venv/bin/techno-search precision-recall-summary
```

Review synthetic human-review queue fixture coverage:

```bash
.venv/bin/techno-search review-queue-summary
```

Review synthetic human-review consensus label coverage:

```bash
.venv/bin/techno-search consensus-summary
```

Review synthetic human-review consensus export coverage:

```bash
.venv/bin/techno-search consensus-export-summary
```

Review validation dataset manifest coverage:

```bash
.venv/bin/techno-search validation-dataset-summary
```

Review curated non-synthetic dataset readiness:

```bash
.venv/bin/techno-search validation-readiness-summary
```

Review local synthetic benchmark metadata:

```bash
.venv/bin/techno-search benchmark-metadata-summary
```

Review local synthetic benchmark run-result metadata:

```bash
.venv/bin/techno-search benchmark-run-summary
```

Append one local synthetic benchmark run-result entry to an ignored output path:

```bash
.venv/bin/techno-search benchmark-run-append \
  --results-path artifacts/benchmark_run_results.json \
  --run-id pytest-coverage-local-001 \
  --command-name "pytest coverage gate" \
  --command-kind test \
  --status passed \
  --worker-count 1 \
  --input-case-count 194 \
  --duration-seconds 1.58 \
  --git-commit "$(git rev-parse --short HEAD)" \
  --config-version scoring_v0
```

Compare repeated local benchmark entries:

```bash
.venv/bin/techno-search benchmark-run-compare \
  --results-path artifacts/benchmark_run_results.json
```

Review fixture-backed background target prioritization:

```bash
.venv/bin/techno-search target-priority-summary
.venv/bin/techno-search target-priority-summary \
  --ledger-path artifacts/background_search_ledger.json
```

Run one explicit local-only background ledger append in an ignored output path:

```bash
.venv/bin/techno-search background-run-once \
  --ledger-path artifacts/background_search_ledger.json \
  --reviewed-log-path artifacts/background_reviewed_log.json \
  --needs-follow-up-log-path artifacts/background_needs_follow_up_log.json \
  --sqlite-log-path logs/techno_search.sqlite3 \
  --acknowledge-local-run
```

Review passive/background search ledger coverage:

```bash
.venv/bin/techno-search background-ledger-summary
```

Review background reviewed-workflow state:

```bash
.venv/bin/techno-search background-reviewed-workflow-summary
```

Review reviewed and needs-follow-up outcome logs:

```bash
.venv/bin/techno-search reviewed-log-summary
.venv/bin/techno-search needs-follow-up-summary
.venv/bin/techno-search follow-up-test-summary
.venv/bin/techno-search report-readiness-summary
.venv/bin/techno-search submission-recommendation-summary
.venv/bin/techno-search draft-follow-up-report-summary
.venv/bin/techno-search draft-follow-up-report-write \
  --output-dir artifacts/background_draft_reports
.venv/bin/techno-search validate-draft-reports artifacts/background_draft_reports
.venv/bin/techno-search user-decision-summary
.venv/bin/techno-search init-logs \
  --db-path logs/techno_search.sqlite3
.venv/bin/techno-search sqlite-log-summary \
  --db-path logs/techno_search.sqlite3
.venv/bin/techno-search sqlite-log-integrity-summary \
  --db-path logs/techno_search.sqlite3
.venv/bin/techno-search sqlite-recent-runs \
  --db-path logs/techno_search.sqlite3
.venv/bin/techno-search sqlite-needs-follow-up \
  --db-path logs/techno_search.sqlite3
.venv/bin/techno-search sqlite-log-export \
  --db-path logs/techno_search.sqlite3
.venv/bin/techno-search sqlite-migration-summary \
  --db-path logs/techno_search.sqlite3
.venv/bin/techno-search sqlite-log-pragmas \
  --db-path logs/techno_search.sqlite3
.venv/bin/techno-search sqlite-log-backup \
  --db-path logs/techno_search.sqlite3
.venv/bin/techno-search sqlite-log-retention-summary \
  --db-path logs/techno_search.sqlite3
.venv/bin/techno-search sqlite-log-vacuum \
  --db-path logs/techno_search.sqlite3
.venv/bin/techno-search sqlite-log-commit-guard
.venv/bin/techno-search validate-sqlite-logs \
  --db-path logs/techno_search.sqlite3
.venv/bin/techno-search scheduler-dry-run \
  --artifact-dir artifacts/background_scheduler_dry_run
```

Review candidate-extraction handoff readiness:

```bash
.venv/bin/techno-search candidate-extraction-handoff-summary
```

`validate-all` and `validation-summary` include calibration-by-track, false-positive class, validation dataset, validation readiness, benchmark metadata, benchmark run-result metadata, background target-priority, background search ledger, background reviewed-workflow, reviewed outcome log, needs-follow-up outcome log, follow-up test results, report-readiness gates, conservative draft report summaries, persisted draft-report validation, user decision records, top-level SQLite log validation, SQLite integrity checks, SQLite migration checks, SQLite export checks, SQLite PRAGMA diagnostics, SQLite backup and retention checks, SQLite vacuum checks, generated SQLite commit-path guardrails, candidate extraction handoff, injection-recovery, reliability, precision-recall, human-review queue, consensus-label, and consensus-export coverage. Benchmark append and compare commands are local workflow helpers for ignored output paths. The reported calibration-by-track coverage, false-positive class coverage, validation dataset coverage, validation readiness counts, benchmark metadata, benchmark run-result metadata, benchmark deltas, target-priority ranking, background ledger counts, background reviewed-workflow counts, reviewed outcome counts, needs-follow-up counts, follow-up test counts, report-readiness counts, draft report counts, user decision counts, SQLite run and outcome counts, SQLite backup counts, candidate extraction handoff counts, recovery rate, false-alarm fraction, reliability errors, precision, recall, F1 score, review queue counts, consensus counts, and consensus export counts are synthetic development diagnostics only; they are not calibrated survey contamination, sensitivity, reliability, per-track survey performance, classification performance estimates, discovery claims, external validation, detections, submission approvals, or scientific performance claims.

Top-level SQLite logs under `logs/` are the operational source of truth for local background automation. Validation checks that each run has exactly one outcome, metadata is present, migrations are not required, PRAGMA integrity is healthy, timestamped backups can be written under ignored `logs/backups/`, retention state is inspectable, vacuum maintenance is runnable, network access remains disabled by default, generated databases are not committed, and no external submission approval is present unless explicitly recorded by the user. JSON files remain fixtures, compatibility artifacts, or review-safe exports.

Snapshot fixture:

```text
tests/fixtures/score_regressions.json
```

Injection-recovery fixture:

```text
tests/fixtures/injection_recovery_summary.json
```

Reliability fixture:

```text
tests/fixtures/reliability_curves.json
```

Precision-recall fixture:

```text
tests/fixtures/precision_recall_summary.json
```

False-positive class diagnostics currently reuse:

```text
tests/fixtures/calibration_false_positives.json
```

Human-review queue fixture:

```text
tests/fixtures/review_queue.json
```

Human-review consensus fixture:

```text
tests/fixtures/consensus_labels.json
```

Human-review consensus export fixture:

```text
tests/fixtures/consensus_exports.json
```

Validation dataset manifest fixture:

```text
tests/fixtures/validation_dataset_manifest.json
```

Validation readiness fixture:

```text
tests/fixtures/validation_readiness.json
```

Benchmark metadata fixture:

```text
tests/fixtures/benchmark_metadata.json
```

Benchmark run-result fixture:

```text
tests/fixtures/benchmark_run_results.json
```

Background target-priority fixture:

```text
tests/fixtures/background_targets.json
```

Background search ledger fixture:

```text
tests/fixtures/background_search_ledger.json
```

The background ledger fixture includes completed synthetic candidate packets, a blocked review handoff, a no-candidate search, and a local scheduling-only runner entry.

Background reviewed and needs-follow-up fixtures:

```text
tests/fixtures/background_reviewed_log.json
tests/fixtures/background_needs_follow_up_log.json
```

The reviewed log records targets that do not currently require follow-up. The needs-follow-up log records reason codes, trigger types, mandatory follow-up tests, report requirements, human-review requirements, and the user-approval gate required before any external submission.

Background follow-up test and report-readiness fixtures:

```text
tests/fixtures/background_follow_up_tests.json
tests/fixtures/background_report_readiness.json
tests/fixtures/background_draft_follow_up_reports.json
tests/fixtures/background_user_decisions.json
```

The follow-up test fixture records deterministic local outcomes for each mandatory test. The report-readiness fixture records whether a conservative draft report can be prepared, whether more tests are required, and the ranked top-three review destinations. The draft report fixture preserves evidence, negative evidence, uncertainty, limitations, blockers, and next steps for report-ready and blocked records. The draft report writer persists Markdown plus `background_draft_report_manifest.json` into ignored artifact paths for operator review. The user decision fixture records `request_more_tests` and `close_as_reviewed` examples while keeping external submission approval false. External submission remains disabled until the user explicitly approves it.

External scheduler templates:

```text
docs/templates/background-search.cron
docs/templates/background-search.launchd.plist
```

These examples call `background-run-once` against ignored `artifacts/` paths and mirror operational state into `logs/techno_search.sqlite3`. They do not set live-data opt-in and they do not authorize external submission.

Background priority config:

```text
configs/background_priority_v0.json
```

Candidate extraction handoff fixture:

```text
tests/fixtures/candidate_extraction_handoffs.json
```

The handoff fixture links local target-selection outputs to candidate-extraction preconditions. It must stay local-only until live automation has an explicit, reviewed design.

When scores change, review whether the scoring model, thresholds, or example inputs changed intentionally.

---

## Example Regeneration

Regenerate committed example artifacts:

```bash
.venv/bin/techno-search regenerate-examples
```

Regenerated examples should keep stable fields identical unless there is an intentional scoring, schema, or reporting change.

Report plot artifacts are optional review context. Current generated examples include dependency-free synthetic SVG diagnostics for radio, infrared, and anomaly tracks, but validators should continue to accept manifests where `plot_artifacts` is absent or empty.

Examples should be regenerated when:

- `schema_version` changes
- `config_version` changes
- report packet fields change
- manifest fields change
- plot artifact manifest fields change
- example candidate inputs change

Stable score, evidence, and pathway changes should be reviewed against `tests/fixtures/score_regressions.json`.

---

## Reproducibility Verification

Re-score persisted candidate packets and report drift vs. their manifests:

```bash
.venv/bin/techno-search verify-report-reproducibility examples/reports
```

Reproducibility verification is read-only. It re-scores each persisted candidate packet using the current scoring implementation and reports drift in pathway, posterior values, derived scores, schema version, and config version. The command exits non-zero if drift is detected. Drift is reported, never auto-corrected; investigate intentional vs unintentional changes manually before regenerating artifacts.

---

## Cross-Track Cross-References

Cross-track references are operational metadata only. Inspect committed coverage:

```bash
.venv/bin/techno-search cross-track-summary
```

The fixture covers operational cross-references across multiple tracks, conflicting evidence, single-track-only entries, and known-object cross-matches. Cross-references must never modify candidate posteriors, false-positive probability, or pathway routing.

---

## Local Artifacts Cleanup

Plan or apply local cleanup of the ignored `artifacts/` directory:

```bash
.venv/bin/techno-search artifacts-cleanup
.venv/bin/techno-search artifacts-cleanup --apply --acknowledge-local-apply
```

The dry-run plan is the default. Apply mode requires the explicit acknowledgement flag and only deletes files under `artifacts/`. Committed roots (`examples/`, `schemas/`, `tests/`, `docs/`, `configs/`, `src/`, `logs/`, `cache/`, `data/`) are always rejected.

---

## SQLite Log Migration And Weekly Digest

Print a non-destructive SQLite log migration plan:

```bash
.venv/bin/techno-search sqlite-log-migrate
```

The plan is dry-run by default. Apply mode is intentionally blocked until a destructive migration is reviewed and added.

Print a review-safe rolling digest of the SQLite operational log:

```bash
.venv/bin/techno-search sqlite-log-weekly-digest
```

The digest reports run counts, reviewed and needs-follow-up counts, blocking-issue totals, network-access counts (must remain zero by default), and external-submission approval counts (must remain zero unless directly recorded by the user).

---

## Interpretable Baseline Validation

The rule-based baseline classifier is evaluated on every `validate-all` run:

```bash
.venv/bin/techno-search baseline-eval-summary
```

Gate: `pathway_accuracy >= 0.80` across calibration false-positive and clean example candidate fixtures. Results are synthetic development diagnostics only — not calibrated survey performance or external validation.

---

## Target Watchlist Validation

```bash
.venv/bin/techno-search target-watchlist-summary
```

Gate: at least 4 watchlist entries, zero elevated-and-blocked conflicts. Watchlist entries are scheduling metadata only and do not modify candidate scores or pathway routing.

---

## Weekly Review Template

```bash
.venv/bin/techno-search weekly-review-template
```

Assembles the weekly operator review template confirming network access is zero, external submission approval is absent, and cross-track references are current. Output is a local review artifact only.
