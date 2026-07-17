# VALIDATION

## Purpose

Central guide for local validation, schema checks, score regression snapshots, and example regeneration.

Validation is a scientific guardrail. It helps keep outputs reproducible, conservative, and explicit about false positives.

---

## Local Validation Gate

Run:

```bash
git pull origin main
caffeinate -i .venv/bin/python scripts/run_parallel_validation.py
git diff --check
```

The launcher runs six pytest-xdist workers as six non-overlapping `loadfile`
shards and aggregates `techno_search` coverage. After pytest succeeds, it runs
the base-aware app-version gate, Ruff, mypy, and `validate-all` concurrently. Use direct
`.venv/bin/python -m pytest ...` only for a small, focused reproduction where
startup/distribution overhead would not save time.

The non-networked CI template in `docs/templates/ci.yml` mirrors these checks
and also runs:

```bash
.venv/bin/techno-search validate-all
.venv/bin/techno-search health
```

Keep the template under `docs/templates/` until the publishing token has GitHub
`workflow` scope. CI and local validation must keep live provider access
disabled by default.

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
.venv/bin/techno-search sqlite-log-bootstrap-summary \
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
.venv/bin/techno-search sqlite-log-consistency-summary \
  --db-path logs/techno_search.sqlite3
.venv/bin/techno-search sqlite-operational-log-registry-summary
.venv/bin/techno-search sqlite-operational-log-adapter-plan-summary
.venv/bin/techno-search sqlite-operational-log-adapter-contract-summary
.venv/bin/techno-search sqlite-operational-log-adapter-ddl-preview-summary
.venv/bin/techno-search sqlite-operational-log-adapter-row-preview-summary
.venv/bin/techno-search sqlite-operational-log-adapter-insert-preview-summary
.venv/bin/techno-search sqlite-operational-log-adapter-execution-preview-summary
.venv/bin/techno-search sqlite-operational-log-adapter-dry-run-manifest-summary
.venv/bin/techno-search sqlite-operational-log-adapter-readiness-preflight-summary
.venv/bin/techno-search sqlite-operational-log-adapter-authorization-gate-summary
.venv/bin/techno-search validate-sqlite-logs \
  --db-path logs/techno_search.sqlite3
.venv/bin/techno-search scheduler-dry-run \
  --artifact-dir artifacts/background_scheduler_dry_run
```

Review candidate-extraction handoff readiness:

```bash
.venv/bin/techno-search candidate-extraction-handoff-summary
```

`validate-all` and `validation-summary` include calibration-by-track, false-positive class, validation dataset, validation readiness, curated dataset admission, project status consistency, MCP bootstrap consistency, MCP server policy, benchmark metadata, benchmark run-result metadata, background target-priority, background search ledger, background reviewed-workflow, reviewed outcome log, needs-follow-up outcome log, follow-up test results, report-readiness gates, conservative draft report summaries, persisted draft-report validation, user decision records, top-level SQLite log validation, SQLite integrity checks, SQLite migration checks, SQLite export checks, SQLite PRAGMA diagnostics, SQLite backup and retention checks, SQLite vacuum checks, generated SQLite commit-path guardrails, candidate extraction handoff, injection-recovery, reliability, precision-recall, human-review queue, consensus-label, and consensus-export coverage. Benchmark append and compare commands are local workflow helpers for ignored output paths. The reported calibration-by-track coverage, false-positive class coverage, validation dataset coverage, validation readiness counts, curated dataset admission counts, project status consistency counts, MCP bootstrap consistency counts, MCP server policy counts, benchmark metadata, benchmark run-result metadata, benchmark deltas, target-priority ranking, background ledger counts, background reviewed-workflow counts, reviewed outcome counts, needs-follow-up counts, follow-up test counts, report-readiness counts, draft report counts, user decision counts, SQLite run and outcome counts, SQLite backup counts, candidate extraction handoff counts, recovery rate, false-alarm fraction, reliability errors, precision, recall, F1 score, review queue counts, consensus counts, and consensus export counts are synthetic development diagnostics only; they are not calibrated survey contamination, sensitivity, reliability, per-track survey performance, classification performance estimates, discovery claims, external validation, detections, submission approvals, or scientific performance claims.

Route coverage now requires every `Pathway` enum value to appear in synthetic
coverage fixtures. The `external_followup_candidate` fixture is enum coverage
only and does not approve external follow-up.

Top-level SQLite logs under `logs/` are the operational source of truth for local background automation. Validation checks that each run has exactly one outcome, metadata is present, migrations are not required, PRAGMA integrity is healthy, timestamped backups can be written under ignored `logs/backups/`, retention state is inspectable, vacuum maintenance is runnable, network access remains disabled by default, generated databases are not committed, and no external submission approval is present unless explicitly recorded by the user. JSON files remain fixtures, compatibility artifacts, or review-safe exports.

Removed synthetic score snapshot fixture:

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

Removed synthetic false-positive class diagnostics previously reused:

```text
tests/fixtures/calibration_false_positives.json
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

Stable score, evidence, and pathway changes should be reviewed against real or
realistic non-training fixtures. Do not restore
`tests/fixtures/score_regressions.json`.

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

Check top-level SQLite log consistency:

```bash
.venv/bin/techno-search sqlite-log-consistency-summary
.venv/bin/techno-search sqlite-log-consistency-summary --db-path logs/techno_search.sqlite3
.venv/bin/techno-search sqlite-log-consistency-summary --fixture-path tests/fixtures/top_level_sqlite_log_consistency.json
```

The summary verifies database visibility, validation, integrity, migration
state, weekly digest state, retention state, PRAGMA diagnostics, commit-guard
state, run/outcome alignment, and disabled network/external authorization
counts. It is a local workflow/provenance gate only.

Check operational log registry consistency:

```bash
.venv/bin/techno-search sqlite-operational-log-registry-summary
.venv/bin/techno-search sqlite-operational-log-registry-summary --fixture-path tests/fixtures/sqlite_operational_log_registry.json
```

The summary verifies that each operational log family has a module, JSON
schema, fixture, CLI summary, `SCHEMA_FILENAMES` entry, and explicit
top-level SQLite production policy. It does not migrate fixture logs or mutate
SQLite databases.

Check non-destructive operational log adapter planning:

```bash
.venv/bin/techno-search sqlite-operational-log-adapter-plan-summary
.venv/bin/techno-search sqlite-operational-log-adapter-plan-summary --fixture-path tests/fixtures/sqlite_operational_log_adapter_plan.json
```

The summary maps registered operational log families to future SQLite adapter
phases and verifies that every family remains planned, policy-aligned, and
non-mutating.

Check non-mutating operational log adapter contracts:

```bash
.venv/bin/techno-search sqlite-operational-log-adapter-contract-summary
.venv/bin/techno-search sqlite-operational-log-adapter-contract-summary --fixture-path tests/fixtures/sqlite_operational_log_adapter_contract.json
```

The summary verifies planned phase-table names and required provenance columns
for future SQLite adapters without creating tables, migrating fixture records,
or mutating databases.

Preview non-executing operational log adapter DDL:

```bash
.venv/bin/techno-search sqlite-operational-log-adapter-ddl-preview-summary
.venv/bin/techno-search sqlite-operational-log-adapter-ddl-preview-summary --fixture-path tests/fixtures/sqlite_operational_log_adapter_ddl_preview.json
```

The preview renders deterministic `CREATE TABLE` SQL text from the adapter
contract for review only. It does not execute SQL, create tables, migrate
fixtures, or mutate databases.

Preview non-executing operational log adapter rows:

```bash
.venv/bin/techno-search sqlite-operational-log-adapter-row-preview-summary
.venv/bin/techno-search sqlite-operational-log-adapter-row-preview-summary --fixture-path tests/fixtures/sqlite_operational_log_adapter_row_preview.json
```

The preview renders deterministic row payloads from registry, phase-plan, and
contract records for review only. It does not insert rows, create tables,
migrate fixtures, or mutate databases.

Preview non-executing operational log adapter inserts:

```bash
.venv/bin/techno-search sqlite-operational-log-adapter-insert-preview-summary
.venv/bin/techno-search sqlite-operational-log-adapter-insert-preview-summary --fixture-path tests/fixtures/sqlite_operational_log_adapter_insert_preview.json
```

The preview renders deterministic parameterized `INSERT` statements and bound
values from row-preview records for review only. It does not execute SQL,
insert rows, create tables, migrate fixtures, or mutate databases.

Preview non-executing operational log adapter execution ordering:

```bash
.venv/bin/techno-search sqlite-operational-log-adapter-execution-preview-summary
.venv/bin/techno-search sqlite-operational-log-adapter-execution-preview-summary --fixture-path tests/fixtures/sqlite_operational_log_adapter_execution_preview.json
```

The preview renders deterministic transaction ordering around insert-preview
records for review only. It does not open databases, execute SQL, insert rows,
create tables, migrate fixtures, or mutate databases.

Preview non-executing operational log adapter dry-run manifest:

```bash
.venv/bin/techno-search sqlite-operational-log-adapter-dry-run-manifest-summary
.venv/bin/techno-search sqlite-operational-log-adapter-dry-run-manifest-summary --fixture-path tests/fixtures/sqlite_operational_log_adapter_dry_run_manifest.json
```

The manifest reconciles deterministic DDL and execution previews for review
only. It does not open databases, execute SQL, insert rows, create tables,
migrate fixtures, mutate databases, authorize live data, or authorize external
submission.

Preview non-mutating operational log adapter readiness preflight:

```bash
.venv/bin/techno-search sqlite-operational-log-adapter-readiness-preflight-summary
.venv/bin/techno-search sqlite-operational-log-adapter-readiness-preflight-summary --fixture-path tests/fixtures/sqlite_operational_log_adapter_readiness_preflight.json
```

The preflight reconciles registry, planning, contract, preview, and dry-run
gates before any future adapter implementation. It does not open databases,
execute SQL, insert rows, create tables, migrate fixtures, mutate databases,
authorize live data, or authorize external submission.

Preview disabled operational log adapter authorization gate:

```bash
.venv/bin/techno-search sqlite-operational-log-adapter-authorization-gate-summary
.venv/bin/techno-search sqlite-operational-log-adapter-authorization-gate-summary --fixture-path tests/fixtures/sqlite_operational_log_adapter_authorization_gate.json
```

The authorization gate keeps adapter implementation, database opening, fixture
migration, execution, mutation, live data, and external submission blocked
pending explicit approval. It does not open databases, execute SQL, insert
rows, create tables, migrate fixtures, mutate databases, authorize live data,
or authorize external submission.

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

---

## Score Determinism

```bash
.venv/bin/techno-search score-determinism-check
```

Verifies that `score_candidate` produces identical posteriors, scores, and recommended pathways across three repeated runs for all example candidates. This is a local reliability diagnostic, not a detection claim, calibration result, or scientific evaluation. Gate: all example candidates must be deterministic.

---

## Candidate Lifecycle And Observation Schedule

```bash
.venv/bin/techno-search candidate-lifecycle-summary
.venv/bin/techno-search observation-schedule-summary
```

Gates in `validate-all`: at least 3 lifecycle entries across all 3 tracks; at least 4 observation windows. These are scheduling and provenance records only.

---

## False-Negative Summary

```bash
.venv/bin/techno-search false-negative-summary
```

Gate in `validate-all`: `synthetic_missed_injection_rate < 1.0` (at least one injection must be recovered per track). Values are synthetic development diagnostics only.

---

## Scoring Config

```bash
.venv/bin/techno-search scoring-config-summary
```

Gate in `validate-all`: at least 1 scoring threshold present. Scoring config summary reports current v0 thresholds only — not calibrated detection limits.

---

## Lifecycle Transition Validation

```bash
.venv/bin/techno-search lifecycle-transition-summary
```

Gate in `validate-all`: `invalid_transition_count == 0`. Validates that all candidate lifecycle stage progressions follow the allowed ordering (`initial_detection` → `archived`). Any backward-moving stage transition is reported as invalid. Scheduling/provenance aid only.

---

## Observation Efficiency

```bash
.venv/bin/techno-search observation-efficiency-summary
```

Reports completion rate, cancellation rate, and per-track efficiency from the committed schedule fixture. Gate in `validate-all`: `completion_rate >= 0.0` (always passes; the gate confirms the summary runs cleanly). Scheduling aid only — not a survey efficiency estimate or external submission authorization.

---

## Sensitivity Config

```bash
.venv/bin/techno-search sensitivity-config-summary
```

Gate in `validate-all`: `track_count >= 3`. Confirms all three tracks (radio, infrared, anomaly) have configured sensitivity weights in `configs/scoring_v0.json`. These are synthetic v0 development coefficients only — not calibrated detection sensitivities.

---

## Candidate Triage Notes

```bash
.venv/bin/techno-search triage-summary
```

Gates in `validate-all`: `note_count >= 5` and `len(tracks_covered) >= 3`. Confirms operator triage notes are present for all three tracks. Triage notes are scheduling aids and provenance records only — they do not modify scores, posteriors, or pathway routing.

---

## Observation Notes Validation

```bash
.venv/bin/techno-search observation-notes-summary
```

Gate in `validate-all`: `note_count >= 5`. Verifies post-observation operator annotations exist across all three tracks. Notes are scheduling provenance records and do not affect candidate scoring.

---

## Epoch Plan Validation

```bash
.venv/bin/techno-search epoch-plan-summary
```

Gate in `validate-all`: `entry_count >= 4`. Verifies that epoch plan entries exist for targets needing follow-up observations. Entries are scheduling aids only.

---

## Aggregate Blockers Validation

```bash
.venv/bin/techno-search aggregate-blockers-summary
```

Included in `validate-all` for informational purposes. Collects blocking issues from triage, lifecycle, observation notes, and handoffs. No minimum blocker count is required — the gate passes as long as the summary is computable.

## Score History Validation

`validate-all` requires `score_history_entry_count >= 5` to confirm synthetic score evolution fixtures cover all three tracks with multi-epoch entries.

## Operator Assignment Validation

`validate-all` requires `operator_assignment_count >= 4` to confirm operator scheduling records are present across tracks.

## Pipeline Health Validation

`validate-all` requires `pipeline_total_blocked >= 0` (always passes; the gate confirms the health summary is reachable). Use `pipeline-health-summary` for the full per-track breakdown.

## Pipeline Input Validation

```bash
.venv/bin/techno-search validate-input tests/fixtures/radio/sample_hits.csv --track radio
.venv/bin/techno-search validate-input tests/fixtures/infrared/sample_gaia_wise.csv --track infrared
.venv/bin/techno-search validate-input tests/fixtures/anomaly/sample_archival_anomaly.csv --track anomaly
.venv/bin/techno-search run-pipeline tests/fixtures/radio/sample_hits.csv --track radio --output-dir artifacts/pipeline_smoke
```

`validate-input` performs structural checks before a local CSV file can be
used by `run-pipeline`. The pipeline runner refuses invalid input before
scoring and records the validation result, reader type, row count, and report
paths in its JSON output. These commands are local triage and provenance aids
only. They do not authorize live data access, external submission, or
scientific claims.

## RFI Database Guardrails

Use `rfi-database-summary` to inspect the local RFI database fixture:

```bash
.venv/bin/techno-search rfi-database-summary
.venv/bin/techno-search rfi-database-summary --fixture-path tests/fixtures/rfi_database.json
```

The summary reports record counts, active counts, reviewed/provisional counts,
synthetic-vs-real counts, source-class counts, site counts, and validation
issues. `validate-all` requires at least one record, at least one reviewed
record, and a clean validation result.

These records are false-positive screening aids only. They do not recalibrate
radio thresholds, confirm or reject candidate technosignature interest,
authorize live-provider access, authorize external submission, or constitute a
detection claim.

## RFI Database Admission Gates

Use `rfi-database-admission-summary` to inspect the local readiness records for
proposed RFI database sources:

```bash
.venv/bin/techno-search rfi-database-admission-summary
.venv/bin/techno-search rfi-database-admission-summary --fixture-path tests/fixtures/rfi_database_admission.json
```

The summary reports blocked counts, synthetic-only counts, real-data
authorization counts, external-review counts, blocker totals, status counts,
site counts, and validation issues. `validate-all` requires admission records
to exist, validation to be clean, and `real_data_authorized_count` to remain
zero in the committed fixture.

Admission records gate future RFI source lists only. They do not ingest real
monitoring data, calibrate thresholds, authorize live data, authorize external
submission, or constitute external validation.

## Curated Dataset Admission Gates

Use `curated-dataset-admission-summary` to inspect local readiness records for
proposed curated validation datasets:

```bash
.venv/bin/techno-search curated-dataset-admission-summary
.venv/bin/techno-search curated-dataset-admission-summary --fixture-path tests/fixtures/curated_dataset_admission.json
```

The summary reports blocked counts, synthetic-only counts, real-data
authorization counts, external-review counts, blocker totals, track counts,
dataset-kind counts, and validation issues. `validate-all` requires admission
records to exist, validation to be clean, and `real_data_authorized_count` to
remain zero in the committed fixture.

Admission records gate future labeled-dataset supplements only. They do not
ingest real observation data, calibrate scoring thresholds, authorize live data,
authorize external submission, or constitute external validation.

## Project Status Consistency Gates

Use `project-status-consistency-summary` to inspect local documentation drift
checks for roadmap, decisions, production readiness, schema counts, and
real-data authorization gates:

```bash
.venv/bin/techno-search project-status-consistency-summary
.venv/bin/techno-search project-status-consistency-summary --fixture-path tests/fixtures/project_status_consistency.json
```

The summary reports expected and observed latest milestone numbers, latest
decision numbers, schema counts, production-readiness current milestone
metadata, and real-data authorization counts from the RFI and curated dataset
admission gates. `validate-all` requires the consistency check to pass.

Project status consistency records are documentation drift guards only. They do
not ingest real observation data, calibrate scoring thresholds, authorize live
data, authorize external submission, or constitute external validation.

## MCP Bootstrap Consistency Gates

Use `mcp-bootstrap-consistency-summary` to inspect local MCP config drift
against the bootstrap policy:

```bash
.venv/bin/techno-search mcp-bootstrap-consistency-summary
.venv/bin/techno-search mcp-bootstrap-consistency-summary --fixture-path tests/fixtures/mcp_bootstrap_consistency.json
```

The summary verifies project-local Claude Code and Codex MCP configs keep only
the expected project-files, read-only git, and fixed validation guard servers.
It checks `.venv` command use, expected server kinds, forbidden token patterns,
and disabled arbitrary-shell, live-provider, and external-submission defaults.
`validate-all` requires the consistency check to pass.

MCP bootstrap consistency records are local configuration drift guards only.
They do not authorize live data access, external submission, candidate score
changes, pathway changes, detections, discoveries, or external validation.

## MCP Server Policy Gates

Use `mcp-server-policy-summary` to inspect local MCP server implementation
policy drift against the allowlisted tool and command contract:

```bash
.venv/bin/techno-search mcp-server-policy-summary
.venv/bin/techno-search mcp-server-policy-summary --fixture-path tests/fixtures/mcp_server_policy.json
```

The summary verifies project-scoped MCP servers keep only expected tool names,
fixed read-only git commands, fixed local validation commands, denied private
and bulky repository paths, read-size limits, strict tool schemas, and local
`.venv` enforcement. It also reports forbidden command tokens, mutating git
commands, and disabled arbitrary-shell, live-provider, and external-submission
flags. `validate-all` requires the policy check to pass.

MCP server policy records are local implementation drift guards only. They do
not execute MCP commands, authorize live data access, authorize external
submission, change candidate scores, change pathways, create detections, claim
discoveries, or provide external validation.

## Production Blocker Consistency Gates

Use `production-blocker-consistency-summary` to inspect local production
blocker visibility across Tier 1 readiness blockers, RFI admission blockers,
curated-dataset admission blockers, and disabled authorization counts:

```bash
.venv/bin/techno-search production-blocker-consistency-summary
.venv/bin/techno-search production-blocker-consistency-summary --fixture-path tests/fixtures/production_blocker_consistency.json
```

The summary reports required Tier 1 blocker phrase coverage, missing blocker
phrases, admission blocker counts, real-data authorization totals, external-submission
authorization totals, and network-access counts. `validate-all` requires the
consistency check to pass.

Production blocker consistency records are local readiness visibility gates
only. They do not ingest real observation data, calibrate scoring thresholds,
clear blockers, authorize live data, authorize external submission, or
constitute external validation.
