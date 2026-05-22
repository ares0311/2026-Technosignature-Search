# CLAUDE.md

## Purpose

Handoff and progress notes for Claude or other coding agents working in this repository.

Read `AGENTS.md` first. The scientific guardrails there remain authoritative.

---

## Current Iteration

User requested fifteen iterative steps completing Milestone 17 (alert resolution log, config version history, operator escalation log).

Current branch: `claude/general-session-Bb2dZ`.

Overall status: all fifteen steps implemented, tested, and validated.

Added:

- `src/techno_search/alert_resolution_log.py` — operational provenance records tracking how open candidate alerts are formally closed; resolution kinds: operator_review, automated_consistency_check, deadline_expiry, pathway_confirmed, watchlist_action; resolved_follow_up is a local scheduling action only
- `schemas/alert_resolution_log.schema.json`
- `tests/fixtures/alert_resolution_log.json` — 5 entries (2 resolved_false_positive, 1 resolved_follow_up, 1 resolved_archived, 1 open)
- `tests/test_alert_resolution_log.py` — 22 tests
- `src/techno_search/config_version_history.py` — append-only local provenance records of pipeline config lifecycle events (created, promoted, updated, deprecated)
- `schemas/config_version_history.schema.json`
- `tests/fixtures/config_version_history.json` — 4 entries (cfg-hist-001 created, cfg-hist-002 promoted, cfg-hist-003 created, cfg-hist-004 deprecated)
- `tests/test_config_version_history.py` — 22 tests
- `src/techno_search/operator_escalation_log.py` — scheduling coordination provenance records for operator-to-operator candidate/alert transfers; severity reflects scheduling priority, not scientific significance
- `schemas/operator_escalation_log.schema.json`
- `tests/fixtures/operator_escalation_log.json` — 4 entries (esc-001 critical/open, esc-002 urgent/acknowledged, esc-003 routine/resolved, esc-004 critical/resolved)
- `tests/test_operator_escalation_log.py` — 24 tests
- `alert_resolution_log`, `config_version_history`, `operator_escalation_log` added to `SCHEMA_FILENAMES` (total schemas: 73)
- `techno-search alert-resolution-summary`, `techno-search config-version-history-summary`, `techno-search operator-escalation-summary` CLI commands
- `validate-all` gates: `alert_resolution_entry_count >= 1`, `config_history_entry_count >= 1`, `operator_escalation_entry_count >= 1`
- `validation-summary` fields: `alert_resolution_entry_count`, `alert_resolution_open_count`, `config_history_entry_count`, `operator_escalation_entry_count`, `operator_escalation_open_count`
- DECISION-050: Alert Resolution Log, Config Version History, And Operator Escalation Log Complete Milestone 17
- Docs: CLI_USAGE.md, DECISIONS.md, ROADMAP.md updated; Milestone 17 fully checked off

Scientific guardrail:

- Alert resolution entries are operational provenance records — resolution does not constitute a detection claim, authorize external submission, or modify scores or pathway routing
- Config version history entries are append-only records — they do not re-run or re-route any candidate
- Operator escalation severity reflects scheduling priority only — not candidate scientific significance; escalation does not authorize external submission

Validation passed:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/ruff check .
.venv/bin/mypy src
git diff --check
.venv/bin/techno-search validate-all
```

Result:

- 1491 tests passed
- 5 tests skipped
- total coverage: 92%
- Ruff passed
- mypy passed (95 source files)
- diff whitespace check passed
- `validate-all` ok=True

Merge status: committed on `claude/general-session-Bb2dZ`, pushed, PR pending.

---

## Previous Iteration

User requested fifteen iterative steps completing Milestone 16 (candidate alert log, pipeline replay log, scoring threshold audit).

Current branch: `claude/general-session-Bb2dZ`.

Overall status: all fifteen steps implemented, tested, and validated.

Added:

- `src/techno_search/candidate_alert_log.py` — severity-classified operational alerts (info/warning/critical) for threshold crossings, pathway changes, provenance inconsistencies, and escalations; alerts are provenance records only
- `schemas/candidate_alert_log.schema.json`
- `tests/fixtures/candidate_alert_log.json` — 5 entries (2 resolved, 3 open; info×2, warning×2, critical×1)
- `tests/test_candidate_alert_log.py` — 21 tests
- `src/techno_search/pipeline_replay_log.py` — append-only reproducibility replay records for provenance verification; replays do not modify committed candidate packets
- `schemas/pipeline_replay_log.schema.json`
- `tests/fixtures/pipeline_replay_log.json` — 4 entries (2 score_matched, 1 score_diverged, 1 config_mismatch)
- `tests/test_pipeline_replay_log.py` — 20 tests
- `src/techno_search/scoring_threshold_audit.py` — local provenance consistency checks verifying pipeline config thresholds match active scoring config version
- `schemas/scoring_threshold_audit.schema.json`
- `tests/fixtures/scoring_threshold_audit.json` — 5 entries (3 pass, 1 warning, 1 not_checked)
- `tests/test_scoring_threshold_audit.py` — 21 tests
- `candidate_alert_log`, `pipeline_replay_log`, `scoring_threshold_audit` added to `SCHEMA_FILENAMES` (total schemas: 70)
- `techno-search candidate-alert-summary`, `techno-search pipeline-replay-summary`, `techno-search scoring-threshold-audit-summary` CLI commands
- `validate-all` gates: `alert_entry_count >= 1`, `replay_entry_count >= 1`, `threshold_pass_count >= 1`
- `validation-summary` fields: `candidate_alert_entry_count`, `candidate_alert_open_count`, `pipeline_replay_entry_count`, `pipeline_replay_matched_count`, `scoring_threshold_pass_count`, `scoring_threshold_fail_count`
- DECISION-049: Candidate Alert Log, Pipeline Replay Log, And Scoring Threshold Audit Complete Milestone 16
- Docs: CLI_USAGE.md, DECISIONS.md, ROADMAP.md updated; Milestone 16 fully checked off

Scientific guardrail:

- Alert entries are operational provenance records — an alert does not constitute a detection claim, modify scores or pathway routing, or authorize external submission
- Replay entries are append-only reproducibility records — replays do not modify committed candidate packets or authorize external submission
- Threshold audit pass means config consistency only — not that thresholds are scientifically calibrated; audit pass does not authorize external submission

Validation passed:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/ruff check .
.venv/bin/mypy src
git diff --check
.venv/bin/techno-search validate-all
```

Result:

- 1423 tests passed
- 5 tests skipped
- total coverage: 92%
- Ruff passed
- mypy passed (92 source files)
- diff whitespace check passed
- `validate-all` ok=True

Merge status: committed on `claude/general-session-Bb2dZ`, pushed, merged to `main` via PR #14.

---

## Previous Iteration

User requested fifteen iterative steps completing Milestone 15 (candidate comparison, pipeline telemetry, provenance audit).

Current branch: `claude/general-session-Bb2dZ`.

Overall status: all fifteen steps implemented, tested, and validated.

Added:

- `src/techno_search/candidate_comparison.py` — local scheduling aid comparing candidate scores and pathway assignments across 2+ candidates; ranked status does not modify scores or pathways
- `schemas/candidate_comparison.schema.json`
- `tests/fixtures/candidate_comparisons.json` — 4 records (2 ranked, 1 tied, 1 insufficient_data)
- `tests/test_candidate_comparison.py` — 20 tests
- `src/techno_search/pipeline_telemetry.py` — per-stage latency and success provenance records covering all 6 pipeline stages
- `schemas/pipeline_telemetry.schema.json`
- `tests/fixtures/pipeline_telemetry.json` — 6 entries (all 6 stages for radio-clean-candidate)
- `tests/test_pipeline_telemetry.py` — 20 tests
- `src/techno_search/provenance_audit.py` — cross-module consistency verdicts (consistent/inconsistent/partial/not_applicable)
- `schemas/provenance_audit.schema.json`
- `tests/fixtures/provenance_audit.json` — 4 entries (1 consistent, 1 partial, 1 inconsistent, 1 not_applicable)
- `tests/test_provenance_audit.py` — 15 tests
- `candidate_comparison`, `pipeline_telemetry`, `provenance_audit` added to `SCHEMA_FILENAMES` (total schemas: 67)
- `techno-search candidate-comparison-summary`, `techno-search pipeline-telemetry-summary`, `techno-search provenance-audit-summary` CLI commands
- `validate-all` gates: `comparison_count >= 1`, `telemetry_entry_count >= 1`, `provenance_audit_entry_count >= 1`
- `validation-summary` fields: `comparison_record_count`, `telemetry_entry_count`, `provenance_audit_entry_count`, `provenance_audit_consistent_count`
- DECISION-048: Candidate Comparison, Pipeline Telemetry, And Provenance Audit Complete Milestone 15
- Docs: CLI_USAGE.md, DECISIONS.md, ROADMAP.md updated; Milestone 15 fully checked off
- `techno-search candidate-rescore-summary`, `techno-search operator-handoff-summary`, `techno-search candidate-methods-summary` CLI commands
- `validate-all` gates: `rescore_event_count >= 1`, `handoff_template_count >= 1`, `handoff_approved_count >= 1`
- `validation-summary` fields: `candidate_rescore_event_count`, `candidate_rescore_pathway_change_count`, `operator_handoff_template_count`, `operator_handoff_approved_count`
- DECISION-046: Candidate Re-Scoring, Operator Handoff Templates, And Candidate Methods Summary Complete Milestone 13
- Docs: CLI_USAGE.md, DECISIONS.md, ROADMAP.md updated; Milestone 13 fully checked off; Milestone 14 stub added

Scientific guardrail:

- Re-score events are append-only provenance records — pathway changes require human review before any action
- Operator handoff templates are local scheduling artifacts only — approved status does not authorize external submission
- Candidate methods summary is an operational dashboard only — does not modify posteriors or authorize external contact

Validation passed:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/ruff check .
.venv/bin/mypy src
git diff --check
.venv/bin/techno-search validate-all
```

Result:

- 1356 tests passed
- 5 tests skipped
- total coverage: 92%
- Ruff passed
- mypy passed (89 source files)
- diff whitespace check passed
- `validate-all` ok=True

Merge status: committed on `claude/general-session-Bb2dZ`, pushed, merged to `main` via PR #13.

---

## Previous Iteration

User requested fifteen iterative steps covering model serving, scoring audit log, and curated dataset intake (Milestone 13 completion).

Current branch: `claude/general-session-Bb2dZ`.

Overall status: all fifteen steps implemented, tested, and validated.

Added:

- `src/techno_search/model_serving.py` — model serving records tracking active/standby/retired/stub inference backends
- `schemas/model_serving.schema.json`
- `tests/fixtures/model_serving.json` — 4 records (1 active baseline_rule, 1 standby pytorch_stub, 1 onnx_stub stub, 1 retired)
- `tests/test_model_serving.py` — 20 tests
- `src/techno_search/scoring_audit_log.py` — append-only provenance records for candidate scoring events
- `schemas/scoring_audit_log.schema.json`
- `tests/fixtures/scoring_audit_log.json` — 5 entries (initial_score, rescore, baseline_comparison across 3 candidates)
- `tests/test_scoring_audit_log.py` — 20 tests
- `src/techno_search/curated_dataset_intake.py` — planning placeholders for future real dataset ingestion
- `schemas/curated_dataset_intake.schema.json`
- `tests/fixtures/curated_dataset_intake.json` — 4 records (BL GBT radio planning, WISE infrared planning, SIMBAD blocked, synthetic approved)
- `tests/test_curated_dataset_intake.py` — 20 tests
- `model_serving`, `scoring_audit_log`, `curated_dataset_intake` added to `SCHEMA_FILENAMES` (total schemas: 60)
- `techno-search model-serving-summary`, `techno-search scoring-audit-log-summary`, `techno-search curated-dataset-intake-summary` CLI commands
- `validate-all` gates: `serving_record_count >= 1`, `audit_entry_count >= 1`, `intake_record_count >= 1`
- `validation-summary` fields: `model_serving_record_count`, `model_serving_active_count`, `scoring_audit_entry_count`, `curated_intake_record_count`, `curated_intake_approved_count`
- DECISION-045: Model Serving, Scoring Audit Log, And Curated Dataset Intake Are Scheduling Provenance Records
- Docs: CLI_USAGE.md, DECISIONS.md, ROADMAP.md updated

Scientific guardrail:

- Model serving records are scheduling provenance artifacts only — no live model weights are loaded
- Scoring audit entries are append-only reproducibility records — they do not re-route candidates
- Curated dataset intake records are planning placeholders — no real observation data has been ingested

Validation passed:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/ruff check .
.venv/bin/mypy src
git diff --check
.venv/bin/techno-search validate-all
```

Result:

- 1194 tests passed
- 5 tests skipped
- total coverage: 92%
- Ruff passed
- mypy passed (80 source files)
- diff whitespace check passed
- `validate-all` ok=True

Merge status: committed on `claude/general-session-Bb2dZ`, pushed, merging to `main`.

---

## Previous Iteration

User requested fifteen iterative steps covering candidate flags, review deadlines, and pipeline throughput.

Current branch: `claude/general-session-Bb2dZ`.

Overall status: all fifteen steps implemented, tested, and validated.

Added:

- `src/techno_search/candidate_flags.py` — quality flags and operational alerts raised against candidates
- `schemas/candidate_flags.schema.json`
- `tests/fixtures/candidate_flags.json` — 5 flags across radio/infrared/anomaly with open/resolved/dismissed/acknowledged statuses
- `tests/test_candidate_flags.py` — 23 tests
- `src/techno_search/review_deadlines.py` — upcoming review deadlines with urgency levels
- `schemas/review_deadlines.schema.json`
- `tests/fixtures/review_deadlines.json` — 5 deadlines across tracks with pending/overdue/completed states
- `tests/test_review_deadlines.py` — 25 tests
- `src/techno_search/pipeline_throughput.py` — per-stage lifecycle counts and throughput rate
- `tests/test_pipeline_throughput.py` — 13 tests
- `candidate_flags` and `review_deadlines` added to `SCHEMA_FILENAMES` (total schemas: 41)
- `techno-search candidate-flags-summary --fixture-path`, `techno-search review-deadlines-summary --fixture-path`, `techno-search pipeline-throughput-summary` CLI commands
- `validate-all` gates: `candidate_flag_count >= 5`, `review_deadline_count >= 4`, `pipeline_throughput_rate >= 0.0`
- `validation-summary` fields: `candidate_flag_count`, `candidate_flag_open_count`, `review_deadline_count`, `review_deadline_overdue_count`, `pipeline_throughput_rate`
- DECISION-036: Candidate Flags, Review Deadlines, And Pipeline Throughput Are Scheduling Provenance Records
- Docs: CLI_USAGE.md, DECISIONS.md updated

Scientific guardrail:

- Flag severity reflects quality-control classification, not candidate interest level
- Deadline urgency reflects scheduling priority, not candidate quality
- Throughput rate is a local scheduling metric, not a calibrated survey efficiency estimate

Validation passed:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/ruff check .
.venv/bin/mypy src
git diff --check
.venv/bin/techno-search validate-all
```

Result:

- 696 tests passed
- 5 tests skipped
- Ruff passed
- mypy passed
- diff whitespace check passed
- `validate-all` ok=True

Merge status: committed on `claude/general-session-Bb2dZ`, pushed, PR updated.

---

## Previous Iteration

User requested fifteen iterative steps covering candidate score history, operator assignment, and pipeline health summary.

Current branch: `claude/general-session-Bb2dZ`.

Overall status: all fifteen steps implemented, tested, and validated.

Added:

- `src/techno_search/candidate_score_history.py` — tracks score evolution across epochs per candidate
- `schemas/candidate_score_history.schema.json`
- `tests/fixtures/candidate_score_history.json` — 5 entries across radio/infrared/anomaly, showing improving/declining/stable trends
- `tests/test_candidate_score_history.py` — 23 tests
- `src/techno_search/operator_assignment.py` — operator scheduling assignments for candidate review
- `schemas/operator_assignment.schema.json`
- `tests/fixtures/operator_assignments.json` — 5 assignments across tracks with pending/in_progress/completed/escalated/deferred statuses
- `tests/test_operator_assignment.py` — 25 tests
- `src/techno_search/pipeline_health.py` — per-track health dashboard aggregating triage, lifecycle, observation, assignment state
- `tests/test_pipeline_health.py` — 13 tests
- `candidate_score_history` and `operator_assignment` added to `SCHEMA_FILENAMES` (total schemas: 39)
- `techno-search score-history-summary --fixture-path`, `techno-search operator-assignment-summary --fixture-path`, `techno-search pipeline-health-summary` CLI commands
- `validate-all` gates: `score_history_entry_count >= 5`, `op_assignment_count >= 4`, `pipeline_total_blocked >= 0`
- `validation-summary` fields: `score_history_entry_count`, `score_history_unique_candidate_count`, `operator_assignment_count`, `operator_assignment_escalated_count`, `pipeline_health_total_blocked`
- DECISION-035: Candidate Score History, Operator Assignment, And Pipeline Health Are Scheduling Provenance Records
- Docs: CLI_USAGE.md, VALIDATION.md, DECISIONS.md updated

Scientific guardrail:

- Score history entries are provenance records only — they do not re-score or re-route candidates
- Operator assignments are scheduling aids — escalated status does not modify pathway routing
- Pipeline health is an operational dashboard — it identifies stalled candidates but does not rank or prioritize for external submission

Validation passed:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/ruff check .
.venv/bin/mypy src
git diff --check
.venv/bin/techno-search validate-all
```

Result:

- 639 tests passed
- 5 tests skipped
- total coverage: 92%
- Ruff passed
- mypy passed
- diff whitespace check passed
- `validate-all` ok=True

Merge status: committed on `claude/general-session-Bb2dZ`, pushed, PR updated.

---

## Previous Iteration

User requested fifteen iterative steps covering candidate observation notes, epoch planning, and aggregate blocker consolidation.

Current branch: `claude/general-session-Bb2dZ`.

Overall status: all fifteen steps implemented, tested, and validated.

Added:

- `src/techno_search/candidate_observation_notes.py` — `CandidateObservationNote` dataclass, `load_observation_notes()`, `observation_notes_summary()`
- `schemas/candidate_observation_notes.schema.json`
- `tests/fixtures/candidate_observation_notes.json` — 5 notes across radio/infrared/anomaly, 2 operators, mixed outcomes
- `techno-search observation-notes-summary` CLI with `--fixture-path`
- `src/techno_search/epoch_plan.py` — `EpochPlanEntry` dataclass, `load_epoch_plan()`, `epoch_plan_summary()`
- `schemas/epoch_plan.schema.json`
- `tests/fixtures/epoch_plan.json` — 5 entries across radio/infrared/anomaly, mixed statuses and priorities
- `techno-search epoch-plan-summary` CLI with `--fixture-path`
- `src/techno_search/aggregate_blockers.py` — `aggregate_blockers_summary()` consolidating triage, lifecycle, observation, and handoff blocking issues
- `techno-search aggregate-blockers-summary` CLI
- `candidate_observation_notes` and `epoch_plan` in `SCHEMA_FILENAMES` (total schemas: 37)
- `validate-all` gates: `obs_notes_count >= 5`, `epoch_plan_entry_count >= 4`, `aggregate_blocker_count >= 0`
- `validation-summary` fields: `observation_notes_count`, `observation_notes_follow_up_count`, `epoch_plan_entry_count`, `epoch_plan_pending_count`, `aggregate_blocker_count`, `aggregate_blocker_unique_candidate_count`
- DECISION-034: Observation Notes, Epoch Plan, And Aggregate Blockers Are Scheduling Provenance Records
- Tests: `test_candidate_observation_notes.py` (21), `test_epoch_plan.py` (21), `test_aggregate_blockers.py` (15) — 57 new tests, all passing
- Docs: CLI_USAGE.md, VALIDATION.md, ROADMAP.md, PROJECT_STATUS.md, DECISIONS.md updated

Scientific guardrail:

- Observation notes are post-observation operator annotations for scheduling and provenance only — they do not modify candidate posteriors
- Epoch plan entries are local scheduling aids — they do not constitute telescope-time commitments or signal confirmation
- Aggregate blocker summary is an operational dashboard only — it mirrors existing fixture data and authorizes no external action

Validation passed:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src
git diff --check
.venv/bin/techno-search validate-all
```

Result:

- 582 tests passed
- 5 tests skipped
- total coverage: 92%
- Ruff passed
- mypy passed
- diff whitespace check passed
- `validate-all` ok=True

Merge status: committed on `claude/general-session-Bb2dZ`, pushed, PR updated.

---

## Previous Iteration

User requested fifteen iterative steps covering route coverage extension, per-track sensitivity config summary, and candidate triage notes.

Current branch: `claude/general-session-Bb2dZ`.

Overall status: all fifteen steps implemented, tested, and validated.

Added:

- `tests/fixtures/route_coverage_fixtures.json` — 3 synthetic candidates verifying `known_object_annotation`, `github_reproducibility_only`, and `human_review_queue` pathway routing
- Updated `route_coverage_summary()` to load dedicated route coverage fixtures in addition to calibration fixtures; route covered count raised from 2 to 5
- `validate-all` gate raised from `route_covered_count >= 2` to `>= 4`
- `src/techno_search/sensitivity_config.py` — `sensitivity_config_summary()` reading `track_sensitivity` from `configs/scoring_v0.json`
- `schemas/sensitivity_config_summary.schema.json`
- `techno-search sensitivity-config-summary` CLI with `--config-path`
- `src/techno_search/candidate_triage.py` — `CandidateTriageNote` dataclass, `load_triage_notes()`, `triage_summary()`
- `schemas/candidate_triage.schema.json`
- `tests/fixtures/candidate_triage_notes.json` — 5 notes across radio/infrared/anomaly, 2 operators
- `techno-search triage-summary` CLI with `--fixture-path`
- `candidate_triage` and `sensitivity_config_summary` in `SCHEMA_FILENAMES` (total schemas: 31)
- `validate-all` gates: `sensitivity_track_count >= 3`, `triage_note_count >= 5`, `len(triage_tracks_covered) >= 3`
- `validation-summary` fields: `sensitivity_track_count`, `sensitivity_weight_count`, `triage_note_count`, `triage_tracks_covered_count`
- DECISION-032: Candidate Triage And Sensitivity Config Are Validated Scheduling Aids
- Tests: `test_sensitivity_config.py` (14), `test_candidate_triage.py` (16) — 30 new tests, all passing
- Docs: CLI_USAGE.md, VALIDATION.md, ROADMAP.md, PROJECT_STATUS.md, DECISIONS.md updated

Scientific guardrail:

- Candidate triage notes are operator scheduling aids and provenance records only — they do not modify scores, posteriors, or pathway routing
- Sensitivity config summary reports local synthetic v0 weights only — not calibrated survey detection sensitivities
- Route coverage extension identifies fixture gaps for human review — not a claim of real observation coverage

Validation passed:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src
git diff --check
.venv/bin/techno-search validate-all
```

Result:

- 460 tests passed
- 5 tests skipped
- total coverage: 92%
- Ruff passed
- mypy passed
- diff whitespace check passed
- `validate-all` ok=True

Merge status: committed on `claude/general-session-Bb2dZ`, pushed, PR created, merging to `main`.

---

## Previous Iteration

User requested fifteen iterative steps covering scoring config summary, route coverage, lifecycle transition validation, and observation efficiency.

Current branch: `claude/general-session-Bb2dZ`.

Overall status: all fifteen steps implemented, tested, and validated.

Added:

- `src/techno_search/scoring_config.py` — `scoring_config_summary()` reading `configs/scoring_v0.json`
- `schemas/scoring_config_summary.schema.json`
- `techno-search scoring-config-summary` CLI with `--config-path`
- `route_coverage_summary()` in `baseline_eval.py` — checks all Pathway enum values have calibration fixture coverage
- `techno-search route-coverage-summary` CLI
- `lifecycle_transition_summary()` in `candidate_lifecycle.py` — validates stage ordering per candidate
- `techno-search lifecycle-transition-summary` CLI with `--fixture-path`
- `observation_efficiency_summary()` in `observation_schedule.py` — completion/cancellation rates and per-track breakdown
- `techno-search observation-efficiency-summary` CLI with `--fixture-path`
- `scoring_config_summary` in `SCHEMA_FILENAMES` (total schemas: 29)
- `validate-all` gates: `scoring_threshold_count >= 1`, `route_covered_count >= 2`, `lifecycle_invalid_count == 0`, `observation_completion_rate >= 0.0`
- `validation-summary` fields: `scoring_threshold_count`, `route_covered_pathway_count`, `route_uncovered_pathway_count`, `lifecycle_invalid_transition_count`, `observation_completion_rate`, `observation_cancellation_rate`
- DECISION-031: Scoring Config And Route Coverage Are Required Local Validation Gates
- Tests: `test_scoring_config.py` (14), `test_lifecycle_transitions.py` (14) — 28 new tests, all passing
- Docs: CLI_USAGE.md, VALIDATION.md, ROADMAP.md, PROJECT_STATUS.md updated

Scientific guardrail:

- Scoring config summary reports local threshold values only — not calibrated detection thresholds
- Route coverage identifies fixture gaps for human review — it does not authorize claiming coverage of real observations
- Lifecycle transition validation is a scheduling/provenance consistency check only
- Observation efficiency summary is a scheduling aid — not a survey efficiency estimate

Validation passed:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src
git diff --check
.venv/bin/techno-search validate-all
```

Result:

- 430 tests passed
- 5 tests skipped
- total coverage: 92%
- Ruff passed
- mypy passed
- diff whitespace check passed
- `validate-all` ok=True

Merge status: committed on `claude/general-session-Bb2dZ`, pushed, PR created, merging to `main`.

---

## Previous Iteration

User requested fifteen iterative steps covering baseline confusion matrix, score determinism checker, candidate lifecycle schema, observation schedule schema, and false-negative summary.

Current branch: `claude/general-session-Bb2dZ`.

Overall status: all fifteen steps implemented, tested, and validated.

Added:

- Baseline confusion matrix (per-pathway TP/FP/TN/FN, precision, recall, F1) in `evaluate_baseline()`
- `baseline-confusion-matrix-summary` CLI
- `score_determinism_check(candidate_path, runs=N)` in `baseline_eval.py`
- `score-determinism-check` CLI — gate: all example candidates deterministic
- `src/techno_search/candidate_lifecycle.py` — lifecycle stage tracker with 7 allowed stages
- `schemas/candidate_lifecycle.schema.json`
- `tests/fixtures/candidate_lifecycle_entries.json` — 10 entries across 3 tracks
- `candidate-lifecycle-summary` CLI
- `src/techno_search/observation_schedule.py` — observation window scheduler
- `schemas/observation_schedule.schema.json`
- `tests/fixtures/observation_schedule.json` — 5 windows (planned/completed/cancelled)
- `observation-schedule-summary` CLI
- `false_negative_summary()` in `injection_recovery.py`
- `false-negative-summary` CLI
- `validate-all` gates: lifecycle >= 3 entries covering 3 tracks, schedule >= 4 windows, missed rate < 1.0
- `validation-summary` fields: `candidate_lifecycle_entry_count`, `observation_schedule_window_count`, `false_negative_case_count`, `synthetic_missed_injection_rate`
- `candidate_lifecycle` and `observation_schedule` in `schema-paths` (total schemas: 28)
- DECISION-030: Scoring Must Be Deterministic Before Any Learned Model Is Introduced
- Tests: `test_baseline_confusion_matrix.py` (14), `test_candidate_lifecycle.py` (13), `test_observation_schedule.py` (13), `test_false_negative.py` (10) — 50 new tests, all passing
- Docs: CLI_USAGE.md, VALIDATION.md, ROADMAP.md, PROJECT_STATUS.md updated

Scientific guardrail:

- Confusion matrix values are synthetic development diagnostics only
- Score determinism check is a local sanity gate — determinism is required before any learned model
- Candidate lifecycle and observation schedule entries are scheduling/provenance records only
- False-negative summary is a synthetic sensitivity indicator, not a calibrated survey metric

Validation passed:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src
git diff --check
.venv/bin/techno-search validate-all
```

Result:

- 402 tests passed
- 5 tests skipped
- total coverage: 92%
- Ruff passed
- mypy passed
- diff whitespace check passed
- `validate-all` ok=True

Merge status: committed on `claude/general-session-Bb2dZ`, pushed, PR created, merging to `main`.

---

## Previous Iteration (Baseline Eval Extensions)

User requested fifteen iterative steps extending the Milestone 10 baseline eval scaffold with rule fire rates, misclassification logs, performance history, drift checks, injection grids, watchlist priority ordering, weekly review watchlist gates, SQLite track summaries, health CLI, and JSON schema artifacts.

Current branch: `claude/general-session-Bb2dZ`.

Overall status: all fifteen steps implemented, tested, and validated.

Added:

- Per-track accuracy breakdown in `evaluate_baseline()` (`by_track_accuracy` field)
- Rule fire-rate reporting for all 8 named baseline rules (`rule_fire_rates` field)
- Misclassification log with `candidate_id`, `expected_pathway`, `predicted_pathway`, `rule_trace`
- `ALL_BASELINE_RULES` public export from `baseline_model.py`
- `baseline_performance_history_summary()` in `baseline_eval.py`
- `tests/fixtures/baseline_performance_history.json` — single synthetic snapshot
- `schemas/baseline_eval.schema.json` — required fields incl. rule_fire_rates and misclassified
- `schemas/baseline_performance_history.schema.json`
- `baseline_pathway_drift_summary()` — compares scoring model vs baseline on example candidates
- `baseline-performance-history-summary` CLI with `--history-path`
- `baseline-pathway-drift-summary` CLI with `--examples-dir`
- `sqlite-log-track-summary` CLI with `--db-path` for per-track run counts
- `health` CLI combining baseline accuracy, watchlist conflicts, drift status
- Watchlist `prioritized_target_ids` ordered by `priority_override_score` (descending)
- `WeeklyReviewTemplate` watchlist fields: `watchlist_elevated_count`, `watchlist_blocked_count`, `watchlist_prioritized_targets`
- Weekly review "Watchlist Status" Markdown section
- `validate-all` gate: `baseline_drift_zero` must be True
- `validation-summary` fields: `baseline_misclassified_count`, `baseline_drift_count`
- `baseline_eval` and `baseline_performance_history` in `schema-paths` (total schemas: 26)
- DECISION-029: Weekly Review Template Is The Authoritative Operator Handoff
- Tests: `tests/test_baseline_extensions.py` (24 tests, all passing)
- Docs: CLI_USAGE.md, VALIDATION.md, ROADMAP.md, PROJECT_STATUS.md updated

Scientific guardrail:

- Baseline eval outputs are synthetic development diagnostics only — not detections, discoveries, or external validation
- Drift summary never auto-corrects — it reports and blocks; human review is required
- Performance history snapshots are local records only; no claim of improving survey performance
- Health CLI is a scheduling aid only

Validation passed:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src
git diff --check
.venv/bin/techno-search validate-all
```

Result:

- 355 tests passed
- 5 tests skipped
- total coverage: 92%
- Ruff passed
- mypy passed
- diff whitespace check passed
- `validate-all` ok=True, baseline_drift_zero=True

Merge status: committed on `claude/general-session-Bb2dZ`, pushed, PR created, merging to `main`.

---

## Cross-Track Cross-Reference, Reproducibility Verification, And Operational Maintenance

User requested applying all system directives and completing the next fifteen steps.

Status: implemented in this iteration.

Added:

- `src/techno_search/artifact_cleanup.py` — local artifacts cleanup planner/applier with dry-run default, forbidden-root safety checks
- `src/techno_search/cross_track.py` — cross-track candidate cross-reference loader, summary helper, and schema
- `src/techno_search/reproducibility.py` — read-only reproducibility verifier comparing re-scored packets against persisted manifests
- `schemas/cross_track_references.schema.json` — JSON Schema for cross-track reference entries
- `tests/fixtures/cross_track_references.json` — 4 synthetic entries (multi-track, conflicting, single-track, known-object)
- `examples/background_draft_reports/` — committed example draft report artifacts
- `sqlite_log_migration_plan()` and `sqlite_log_weekly_digest()` in `log_store.py`
- CLI commands: `artifacts-cleanup`, `cross-track-summary`, `verify-report-reproducibility`, `sqlite-log-migrate`, `sqlite-log-weekly-digest`
- New `validate-all` gates and `validation-summary` fields for all of the above
- Tests: `test_artifact_cleanup.py`, `test_cross_track.py`, `test_reproducibility.py`, `test_log_store_extensions.py`
- Docs updates: `DECISIONS.md` (DECISION-026, DECISION-027), `CLI_USAGE.md`, `VALIDATION.md`, `PROJECT_STATUS.md`, `ROADMAP.md`, `README.md`

Scientific guardrail:

- Cross-track references are operational metadata only — they never modify posteriors or pathway routing
- Reproducibility verification reports drift but never auto-corrects committed artifacts
- Weekly digest confirms network_access_allowed_count and external_submission_approved_count remain zero
- Artifacts cleanup refuses all committed project roots

Validation passed:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src
git diff --check
.venv/bin/techno-search validate-all
```

Result:

- 283 tests passed
- 5 tests skipped
- total coverage: 92%
- Ruff passed
- mypy passed
- diff whitespace check passed
- `validate-all` ok=True

Merge status: committed on `claude/general-session-Bb2dZ`, pushed, PR created, merged to `main`.

---

## Persisted Background Draft Reports And Decision Append Workflow

User requested applying all system directives, completing the next fifteen
background automation steps, and publishing well-tested code.

Status: implemented in this iteration.

Added:

- persisted background draft follow-up report Markdown writer with manifest output
- draft report directory validation for manifest consistency, conservative sections, disabled network access, disabled external submission, and required disclaimer text
- explicit user-decision append helper and CLI command with a required approval flag for external-submission decisions
- scheduler dry-run CLI command that exercises the local non-networked runner without writing production artifacts
- manifest schema coverage for persisted draft reports
- README, CLI usage, validation guide, roadmap, project status, release checklist, automation blueprint, and decisions updates

Scientific guardrail:

- persisted draft reports are local internal review artifacts only
- reports must preserve negative evidence, limitations, blocking issues, and explicit gates
- external submission stays blocked unless the user records approval directly
- scheduler dry runs keep network access disabled and do not authorize external contact

Validation passed:

```bash
.venv/bin/python -m pytest tests/test_background_search.py tests/test_cli.py tests/test_json_schemas.py tests/test_docs.py
.venv/bin/python -m pytest
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src
git diff --check
.venv/bin/techno-search validate-all
```

Result:

- 237 tests passed
- 5 tests skipped
- total coverage: 92%
- Ruff passed
- mypy passed
- diff whitespace check passed
- `validate-all` passed

Merge status: work is on `codex/background-report-decision-scheduler` for push to GitHub.

---

## Top-Level SQLite Background Logs

User requested applying all system directives, completing the next fifteen
steps, and requiring top-level SQLite logs.

Status: implemented in this iteration.

Added:

- top-level `logs/README.md` policy and `.gitignore` rules for generated SQLite databases
- `src/techno_search/log_store.py` using stdlib `sqlite3`
- SQLite schema for background runs, reviewed outcomes, needs-follow-up outcomes, draft-report slots, user-decision slots, validation events, and metadata
- `techno-search init-logs`
- `techno-search sqlite-log-summary`
- `techno-search validate-sqlite-logs`
- optional `--sqlite-log-path` mirroring for `background-run-once`
- scheduler dry-run SQLite output
- `validate-all` and `validation-summary` coverage for SQLite log invariants
- tests for initialization, append-only run/outcome behavior, duplicate run rejection, CLI commands, docs drift, and scheduler templates
- README, CLI usage, validation guide, pipeline spec, roadmap, project status, release checklist, automation blueprint, and decisions updates

Scientific guardrail:

- SQLite logs are operational workflow/provenance records only
- each background run must have exactly one reviewed or needs-follow-up outcome
- network access remains disabled by default
- external submission approval must remain absent unless explicitly recorded by the user

Focused validation passed:

```bash
.venv/bin/python -m pytest tests/test_log_store.py tests/test_cli.py tests/test_docs.py
.venv/bin/python -m ruff check src/techno_search/log_store.py src/techno_search/background_search.py src/techno_search/cli.py src/techno_search/validation.py tests/test_log_store.py tests/test_cli.py tests/test_docs.py
```

Result:

- 69 focused tests passed
- focused Ruff passed

Full validation still needed before committing or publishing this iteration.

---

## SQLite Log Hardening And Review-Safe Exports

User requested applying all system directives, completing the next fifteen
steps, and keeping top-level SQLite logs.

Status: implemented in this iteration.

Added:

- `techno-search sqlite-log-integrity-summary`
- `techno-search sqlite-log-export`
- `techno-search sqlite-recent-runs`
- `techno-search sqlite-needs-follow-up`
- `techno-search sqlite-migration-summary`
- `techno-search sqlite-log-commit-guard`
- metadata validation for missing or unsupported SQLite schema records
- tests for missing outcomes, conflicting outcomes, missing metadata, migration checks, generated-log commit guards, and review-safe exports
- validation-summary and validate-all coverage for SQLite integrity, migration, export, and generated database commit guardrails
- rotation, retention, backup, and pruning guidance in `logs/README.md`
- README, CLI usage, validation guide, roadmap, project status, release checklist, automation blueprint, and decisions updates

Scientific guardrail:

- SQLite recent-run and export views are review-safe summaries only
- exports preserve blockers, negative evidence, provenance, and uncertainty notes
- generated SQLite databases remain ignored and must not be committed
- no SQLite command authorizes external submission or claims a detection

Focused validation passed:

```bash
.venv/bin/python -m pytest tests/test_log_store.py tests/test_cli.py tests/test_docs.py
.venv/bin/python -m ruff check src/techno_search/log_store.py src/techno_search/cli.py tests/test_log_store.py tests/test_cli.py tests/test_docs.py
.venv/bin/python -m mypy src
```

## SQLite Log Maintenance Commands

User reiterated applying all system directives and keeping top-level SQLite logs.

Status: implemented in this iteration.

Added:

- `techno-search sqlite-log-pragmas`
- `techno-search sqlite-log-backup`
- `techno-search sqlite-log-retention-summary`
- `techno-search sqlite-log-vacuum`
- ignored `logs/backups/` policy for generated SQLite backups
- `validate-all` and `validation-summary` coverage for SQLite PRAGMA, backup, retention, and vacuum maintenance
- README, CLI usage, validation guide, roadmap, project status, release checklist, automation blueprint, and logs README updates

Scientific guardrail:

- backups and retention summaries are local operational records only
- maintenance commands do not authorize external submission or imply discovery
- generated SQLite databases and backups remain ignored and must not be committed

Result:

- 76 focused tests passed
- focused Ruff passed
- mypy passed

Full validation still needed before committing or publishing this iteration.

---

## Background Draft Reports, User Decisions, And Scheduler Templates

User requested applying all system directives, completing the next fifteen
background automation steps, and publishing the work.

Status: implemented in this iteration.

Added:

- conservative draft follow-up report schema, fixture, loader, generated summary helper, and CLI commands
- explicit user decision schema, fixture, loader, summary helper, and CLI command
- validation-summary and validate-all wiring for draft-report and user-decision gates
- cron and launchd scheduler templates that call `background-run-once` with ignored `artifacts/` paths
- tests for schema coverage, CLI output, conservative language, disabled external submission, and scheduler templates
- README, CLI usage, validation guide, roadmap, project status, release checklist, and decisions updates

Scientific guardrail:

- draft reports are internal review summaries only
- user decisions keep external submission approval false in committed fixtures
- scheduler templates do not enable live provider access and do not authorize external contact

Validation passed:

```bash
.venv/bin/python -m pytest tests/test_background_search.py tests/test_cli.py tests/test_json_schemas.py tests/test_docs.py
.venv/bin/python -m pytest
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src
git diff --check
.venv/bin/techno-search validate-all
```

Result:

- 228 tests passed
- 5 tests skipped
- total coverage: 92%
- Ruff passed
- mypy passed
- diff whitespace check passed
- `validate-all` passed

---

## README Style Refresh

User requested extracting the style DNA from the sibling exoplanet project README and applying it to this repository.

Status: implemented.

Added:

- compact public-facing README structure with visual section headers
- core flow, key idea, current status, roadmap, architecture, scoring model, quickstart, schema table, disclaimer, license, and vision sections
- conservative technosignature language and false-positive-first framing
- README structure drift test in `tests/test_docs.py`
- updated `docs/PROJECT_STATUS.md` current-phase wording
- refreshed `docs/PUBLISHING.md` with the moved GitHub repository URL

Validation passed:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/ruff check .
.venv/bin/mypy src
git diff --check
```

Result:

- 175 tests passed
- 5 tests skipped
- total coverage: 92%
- Ruff passed
- mypy passed
- diff whitespace check passed

Merge status: already on `main`; no merge needed.

---

## Background Target Priority And Passive Search Ledger Expansion

User requested prioritizing the background searching system discussed in the README.

Status: implemented in this iteration.

Added:

- fixture-backed background target-priority model in `src/techno_search/background_search.py`
- passive/background search ledger loader and summary helper
- `techno-search target-priority-summary`
- `techno-search background-ledger-summary`
- JSON schemas for target-priority and background-ledger fixtures
- local validation wiring through `validate-all` and `validation-summary`
- tests for target scoring, selected target behavior, ledger coverage, schema coverage, and CLI output
- README/docs updates explaining layperson operation, recalibration, target selection, passive logging, and guardrails

Scientific guardrail:

- target priority is a scheduling aid only
- ledger entries are reproducibility records only
- neither output is evidence of a technosignature or a discovery claim

Merge status: already on `main`; no merge needed.

---

## Background Config And Local Passive Runner Expansion

User requested the next fifteen steps and asked to push when complete.

Status: implemented in this iteration.

Added:

- `configs/background_priority_v0.json` for versioned target-priority weights and passive-runner defaults
- background priority config loader and public exports
- config-backed `target-priority-summary`
- explicit `techno-search background-run-once` command
- local-only ledger append helper with required opt-in and no network access
- tests for config loading, opt-in enforcement, ledger creation, ledger append behavior, and CLI output
- README, CLI usage, validation, roadmap, scoring model, pipeline spec, project status, and decisions updates

Scientific guardrail:

- the passive runner records scheduling-only local fixture events
- `candidate_count` remains `0` until candidate extraction is implemented
- the output pathway is `github_reproducibility_only`
- no live provider access is performed

Merge status: already on `main`; no merge needed.

---

## Benchmark Append And Comparison Workflow

User requested the next fifteen steps and asked to push when complete.

Status: implemented in this iteration.

Added:

- append-only benchmark run-result helper
- repeated-run benchmark comparison helper
- `techno-search benchmark-run-append`
- `techno-search benchmark-run-compare`
- required `config_version` field on benchmark run-result entries
- tests for append preservation, duplicate run rejection, repeated-run deltas, schema coverage, and CLI output
- README, CLI usage, validation, roadmap, project status, and decisions updates

Scientific guardrail:

- benchmark runs record local synthetic execution context only
- append/compare outputs are not survey sensitivity estimates, candidate-quality metrics, detections, or external validation

Merge status: already on `main`; no merge needed.

---

## Validation Readiness Workflow

User requested the next fifteen steps and asked to push when complete.

Status: implemented in this iteration.

Added:

- `schemas/validation_readiness.schema.json`
- `tests/fixtures/validation_readiness.json`
- validation readiness dataclass, loader, and summary helper
- `techno-search validation-readiness-summary`
- validation readiness coverage in `validate-all` and `validation-summary`
- tests for readiness statuses, blockers, CLI output, schema coverage, and docs drift
- README, CLI usage, validation guide, roadmap, project status, and decisions updates

Scientific guardrail:

- readiness status is a curated-review gate only
- readiness summaries do not certify discoveries, detections, external validation, or calibrated survey performance

Merge status: already on `main`; no merge needed.

---

## Background Reviewed Workflow Ledger Expansion

User requested the next fifteen steps and asked to push when complete.

Status: implemented in this iteration.

Added:

- reviewed-workflow fields on background search ledger entries
- fixture coverage for candidate-packet-ready, review-blocked, negative-search, and local-scheduling-only states
- `techno-search background-reviewed-workflow-summary`
- reviewed-workflow counts in `validate-all` and `validation-summary`
- tests for local-only run semantics, negative-result logging, target-selection rationale, schema coverage, and CLI output
- README, CLI usage, validation guide, roadmap, project status, and decisions updates

Scientific guardrail:

- reviewed-workflow status is an operational handoff state only
- target-priority scores remain scheduling aids
- local runner entries remain non-networked and scheduling-only
- negative-result logs and candidate packet IDs are provenance records, not discovery or detection claims

Merge status: already on `main`; no merge needed.

---

## Candidate Extraction Handoff Contract

User requested the next fifteen steps and asked to push when complete.

Status: implemented in this iteration.

Added:

- local-only candidate extraction handoff schema
- `tests/fixtures/candidate_extraction_handoffs.json`
- handoff dataclass, loader, and summary helper
- `techno-search candidate-extraction-handoff-summary`
- handoff counts in `validate-all` and `validation-summary`
- tests for schema coverage, loader behavior, summary counts, CLI output, and no-network guardrails
- README, CLI usage, validation guide, pipeline spec, roadmap, project status, and decisions updates

Scientific guardrail:

- handoff records are operational contracts only
- target priority remains separate from candidate evidence
- ready handoffs only mean local fixture inputs are present
- blocked and no-candidate handoffs preserve blockers and negative-result requirements
- no live provider access is enabled by this workflow

Merge status: already on `main`; no merge needed.

---

## Fifteen-Step Consensus Export, Promotion, And Benchmark Run Expansion

User requested the next fifteen steps:

1. Add conservative consensus-label export example format.
2. Add consensus export fixture JSON.
3. Add `techno-search consensus-export-summary`.
4. Add tests for consensus export coverage and conservative language.
5. Wire consensus export summary into `validate-all`.
6. Wire consensus export counts into `validation-summary`.
7. Update docs/status for consensus export examples.
8. Add validation dataset promotion rule schema.
9. Add promotion rule fixture for synthetic to future non-synthetic datasets.
10. Add `techno-search validation-promotion-summary`.
11. Add tests for promotion rules by readiness, evidence requirements, and blocking conditions.
12. Wire promotion rules into `validate-all` and `validation-summary`.
13. Add benchmark run-result metadata schema for future synthetic calibration grids.
14. Add benchmark run-result fixture and summary CLI.
15. Run full validation, update `CLAUDE.md`, commit, push, and confirm clean sync.

Each step should update this file and merge to `main` if needed.

## Consensus Export/Promotion/Benchmark Step 1 — Consensus Export Format

Status: implemented.

Added:

- `CONSENSUS_EXPORT_SCHEMA_VERSION`
- `CONSENSUS_EXPORT_DISCLAIMER`
- `ConsensusExportItem`
- consensus export fixture loader
- consensus export summary helper

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 2 — Consensus Export Fixture

Status: implemented.

Added:

- `schemas/consensus_export.schema.json`
- `tests/fixtures/consensus_exports.json`
- conservative consensus export examples for no-consensus, likely-false-positive, follow-up-target, known-object annotation, and insufficient-evidence labels

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 3 — Consensus Export Summary CLI

Status: implemented.

Added:

- `techno-search consensus-export-summary`
- optional `--fixture-path`
- `consensus_export` in `schema-paths`
- public package exports for consensus export helpers

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 4 — Consensus Export Tests

Status: implemented.

Added tests for:

- consensus export fixture loading
- conservative disclaimer language
- summary counts by track and consensus label
- CLI output for `consensus-export-summary`
- schema discovery and required fixture fields

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 5 — Validate-All Consensus Export Wiring

Status: implemented.

Added:

- `consensus_export_summary` block in `validate-all`
- validation gate for expected synthetic consensus export coverage

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 6 — Validation Summary Consensus Export Counts

Status: implemented.

Added:

- `consensus_export_count`
- `consensus_export_blocking_issue_total`

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 7 — Consensus Export Docs And Status

Status: implemented.

Updated:

- `README.md`
- `docs/CLI_USAGE.md`
- `docs/VALIDATION.md`
- `docs/PROJECT_STATUS.md`

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 8 — Validation Promotion Rule Schema

Status: implemented.

Added:

- `VALIDATION_PROMOTION_SCHEMA_VERSION`
- `VALIDATION_PROMOTION_DISCLAIMER`
- `ValidationPromotionRule`
- promotion rule loader
- promotion rule summary helper

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 9 — Validation Promotion Fixture

Status: implemented.

Added:

- `schemas/validation_promotion_rules.schema.json`
- `tests/fixtures/validation_promotion_rules.json`
- synthetic-to-curated promotion rules for radio, infrared, and anomaly validation datasets

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 10 — Validation Promotion Summary CLI

Status: implemented.

Added:

- `techno-search validation-promotion-summary`
- optional `--rules-path`
- `validation_promotion_rules` in `schema-paths`
- public package exports for validation promotion helpers

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 11 — Validation Promotion Tests

Status: implemented.

Added tests for:

- promotion rule fixture loading
- readiness transitions
- evidence requirements
- blocking conditions
- external-review requirements
- `techno-search validation-promotion-summary`
- schema discovery and required fixture fields

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 12 — Validation Promotion Local Validation Wiring

Status: implemented.

Added:

- `validation_promotion_summary` block in `validate-all`
- validation gate for promotion rule coverage
- `validation_promotion_rule_count` in `validation-summary`
- `validation_promotion_blocking_condition_count` in `validation-summary`

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 13 — Benchmark Run-Result Metadata Schema

Status: implemented.

Added:

- `BENCHMARK_RUN_RESULT_SCHEMA_VERSION`
- `BENCHMARK_RUN_RESULT_DISCLAIMER`
- `BenchmarkRunResult`
- benchmark run-result loader
- benchmark run-result summary helper
- `schemas/benchmark_run_results.schema.json`

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 14 — Benchmark Run-Result Fixture And Summary CLI

Status: implemented.

Added:

- `tests/fixtures/benchmark_run_results.json`
- `techno-search benchmark-run-summary`
- benchmark run-result schema discovery in `schema-paths`
- benchmark run-result summary wiring in `validate-all`
- benchmark run-result counts in `validation-summary`
- tests for fixture loading, CLI output, schema fields, and local validation wiring
- docs/status/roadmap references for benchmark run-result metadata

Validation passed:

```bash
.venv/bin/python -m pytest tests/test_benchmark_metadata.py tests/test_cli.py tests/test_json_schemas.py tests/test_validation_datasets.py
```

Result:

- 48 tests passed

Merge status: already on `main`; no merge needed.

---

## Consensus Export/Promotion/Benchmark Step 15 — Validation, Commit, And Push

Status: implemented.

Validation passed:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/ruff check .
.venv/bin/mypy src
git diff --check
```

Result:

- 174 tests passed
- 5 tests skipped
- total coverage: 92%
- Ruff passed
- mypy passed
- diff whitespace check passed

Planned commit:

```bash
git commit -m "Add benchmark run result summaries"
```

Merge status: already on `main`; no merge needed.

---

## Fifteen-Step Validation Dataset And Benchmark Metadata Expansion

User asked to continue after the consensus/calibration pass. Next roadmap/status items:

1. Add validation dataset manifest helper schema in code.
2. Add validation dataset JSON schema artifact.
3. Add validation dataset manifest fixture examples.
4. Add validation dataset summary helper.
5. Add `techno-search validation-dataset-summary`.
6. Add tests for validation dataset schema, helper, and CLI.
7. Wire validation dataset summary into `validate-all`.
8. Wire validation dataset counts into `validation-summary`.
9. Update validation dataset docs/status/roadmap.
10. Add benchmark metadata helper schema in code.
11. Add benchmark metadata JSON schema and fixture.
12. Add `techno-search benchmark-metadata-summary`.
13. Add tests for benchmark metadata schema, helper, and CLI.
14. Wire benchmark metadata into validation/docs/status.
15. Run full validation, commit, push, and record everything in `CLAUDE.md`.

Each step should update this file and merge to `main` if needed.

## Validation/Benchmark Step 1 — Validation Dataset Helper Schema

Status: implemented.

Added:

- `VALIDATION_DATASET_SCHEMA_VERSION`
- `VALIDATION_DATASET_DISCLAIMER`
- `ValidationDatasetEntry`
- validation dataset manifest loader
- validation dataset summary helper skeleton

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 2 — Validation Dataset JSON Schema

Status: implemented.

Added:

- `schemas/validation_dataset_manifest.schema.json`
- required manifest fields for dataset ID, track, kind, readiness, source fixture path, case count, false-positive classes, and expected pathways

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 3 — Validation Dataset Fixture

Status: implemented.

Added `tests/fixtures/validation_dataset_manifest.json` with lightweight synthetic scaffold entries for:

- radio false-positive validation cases
- infrared false-positive validation cases
- anomaly false-positive validation cases

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 4 — Validation Dataset Summary Helper

Status: implemented.

The validation dataset helper now summarizes:

- dataset count
- total case count
- false-positive class count
- expected pathway count
- counts by track, dataset kind, and readiness
- dataset IDs and source fixture paths

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 5 — Validation Dataset Summary CLI

Status: implemented.

Added:

- `techno-search validation-dataset-summary`
- optional `--manifest-path`
- `validation_dataset_manifest` in `schema-paths`
- public package exports for validation dataset helpers

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 6 — Validation Dataset Tests

Status: implemented.

Added tests for:

- validation dataset manifest loading
- validation dataset summary counts
- `techno-search validation-dataset-summary`
- schema discovery and required manifest fields

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 7 — Validate-All Validation Dataset Wiring

Status: implemented.

Added:

- `validation_dataset_summary` block in `validate-all`
- validation gates for manifest dataset count and total case coverage

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 8 — Validation Summary Dataset Counts

Status: implemented.

Added:

- `validation_dataset_count`
- `validation_dataset_case_count`

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 9 — Validation Dataset Docs And Status

Status: implemented.

Updated:

- `README.md`
- `docs/CLI_USAGE.md`
- `docs/VALIDATION.md`
- `docs/ROADMAP.md`
- `docs/PROJECT_STATUS.md`

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 10 — Benchmark Metadata Helper Schema

Status: implemented.

Added:

- `BENCHMARK_METADATA_SCHEMA_VERSION`
- `BENCHMARK_METADATA_DISCLAIMER`
- `BenchmarkCommand`
- benchmark metadata loader
- benchmark metadata summary helper

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 11 — Benchmark Metadata Schema And Fixture

Status: implemented.

Added:

- `schemas/benchmark_metadata.schema.json`
- `tests/fixtures/benchmark_metadata.json`
- local benchmark metadata tied to `docs/LOCAL_SYSTEM_PROFILE.md`
- recommended worker and memory limits from the documented local workstation

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 12 — Benchmark Metadata Summary CLI

Status: implemented.

Added:

- `techno-search benchmark-metadata-summary`
- optional `--metadata-path`
- `benchmark_metadata` in `schema-paths`
- public package exports for benchmark metadata helpers

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 13 — Benchmark Metadata Tests

Status: implemented.

Added tests for:

- benchmark metadata fixture loading
- local hardware/profile summary fields
- command kind and status counts
- `techno-search benchmark-metadata-summary`
- schema discovery and required fixture fields

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 14 — Benchmark Metadata Validation And Docs

Status: implemented.

Added:

- `benchmark_metadata_summary` block in `validate-all`
- benchmark metadata counts in `validation-summary`
- benchmark metadata references in `README.md`, `docs/CLI_USAGE.md`, `docs/VALIDATION.md`, and `docs/PROJECT_STATUS.md`

Merge status: already on `main`; no merge needed.

---

## Validation/Benchmark Step 15 — Full Validation, Commit, And Push

Status: implemented.

Validation passed:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/ruff check .
.venv/bin/mypy src
git diff --check
```

Result:

- 165 tests passed
- 5 tests skipped
- total coverage: 92%
- Ruff passed
- mypy passed
- diff whitespace check passed

Planned commit:

```bash
git commit -m "Add validation dataset and benchmark metadata summaries"
```

Merge status: already on `main`; no merge needed.

---

## Fifteen-Step Consensus And Calibration-Track Expansion

User requested fifteen iterative steps:

1. Add consensus-label schema for repeated reviewer decisions.
2. Add consensus label fixture examples.
3. Add `techno-search consensus-summary`.
4. Add tests for consensus summaries by label, track, and reviewer count.
5. Wire consensus summary into `validate-all`.
6. Wire consensus counts into `validation-summary`.
7. Update human-review docs for consensus labels.
8. Mark consensus-label scaffold complete in roadmap/status.
9. Add calibration-by-track summary helper.
10. Add `techno-search calibration-track-summary`.
11. Add tests for calibration-by-track class/pathway coverage.
12. Wire calibration-by-track summary into `validate-all`.
13. Wire calibration-by-track counts into `validation-summary`.
14. Update calibration docs/status/roadmap.
15. Run full validation, commit, push, and record everything in `CLAUDE.md`.

Each step should update this file and merge to `main` if needed.

## Consensus/Calibration Step 1 — Consensus Label Schema

Status: implemented.

Added:

- `CONSENSUS_LABEL_SCHEMA_VERSION`
- `CONSENSUS_LABEL_DISCLAIMER`
- `ConsensusLabel`
- `ConsensusDecision`
- `ConsensusItem`
- `schemas/consensus_labels.schema.json`
- consensus fixture loader and summary skeleton

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 2 — Consensus Label Fixtures

Status: implemented.

Added `tests/fixtures/consensus_labels.json` with repeated synthetic reviewer decisions for:

- no consensus
- likely false positive
- follow-up target
- known-object annotation
- insufficient evidence

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 3 — Consensus Summary CLI

Status: implemented.

Added:

- `techno-search consensus-summary`
- optional `--fixture-path`
- `consensus_labels` in `schema-paths`

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 4 — Consensus Summary Tests

Status: implemented.

Added tests for:

- consensus fixture loading and allowed labels
- consensus summary counts by label and track
- repeated reviewer decision counts
- CLI `consensus-summary`
- `consensus_labels` schema discovery and fixture required fields

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 5 — Validate-All Consensus Wiring

Status: implemented.

Added:

- `consensus_summary` block in `validate-all`
- validation gates for minimum synthetic consensus item and decision coverage

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 6 — Validation Summary Consensus Counts

Status: implemented.

Added:

- `consensus_item_count`
- `consensus_decision_count`
- `consensus_unique_reviewer_count`

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 7 — Consensus Docs

Status: implemented.

Updated:

- `docs/CLI_USAGE.md`
- `docs/VALIDATION.md`
- `README.md`

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 8 — Consensus Roadmap And Status

Status: implemented.

Updated:

- `docs/ROADMAP.md`
- `docs/PROJECT_STATUS.md`

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 9 — Calibration-By-Track Helper

Status: implemented.

Added:

- `CALIBRATION_TRACK_SCHEMA_VERSION`
- `CALIBRATION_TRACK_DISCLAIMER`
- `calibration_track_summary`
- per-track case, class, pathway, candidate-ID, and fixture-name coverage

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 10 — Calibration Track Summary CLI

Status: implemented.

Added:

- `techno-search calibration-track-summary`
- optional `--fixture-path`
- public package exports for calibration-track summary helpers

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 11 — Calibration Track Tests

Status: implemented.

Added tests for:

- per-track calibration case counts
- per-track false-positive class coverage
- per-track expected pathway coverage
- `techno-search calibration-track-summary`
- conservative per-track calibration disclaimer

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 12 — Validate-All Calibration Track Wiring

Status: implemented.

Added:

- `calibration_track_summary` block in `validate-all`
- validation gates for expected track coverage and minimum per-track fixture coverage

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 13 — Validation Summary Calibration Track Counts

Status: implemented.

Added:

- `calibration_track_count`
- `calibration_minimum_track_case_count`

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 14 — Calibration Docs And Status

Status: implemented.

Updated:

- `docs/CLI_USAGE.md`
- `docs/VALIDATION.md`
- `docs/ROADMAP.md`
- `docs/PROJECT_STATUS.md`

Merge status: already on `main`; no merge needed.

---

## Consensus/Calibration Step 15 — Full Validation, Commit, And Push

Status: implemented.

Validation passed:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/ruff check .
.venv/bin/mypy src
git diff --check
```

Result:

- 159 tests passed
- 5 tests skipped
- total coverage: 92%
- Ruff passed
- mypy passed
- diff whitespace check passed

Planned commit:

```bash
git commit -m "Add consensus and calibration track summaries"
```

Pushed commit:

- `bdb2ee3 Add consensus and calibration track summaries`

Remote sync:

```bash
git push origin main
```

Result:

- `main` pushed to `origin/main`
- remote advanced from `7b10728` to `bdb2ee3`

Merge status: already on `main`; no merge needed.

---

## Fifteen-Step False-Positive And Human-Review Expansion

User requested fifteen iterative steps:

1. Add false-positive class analysis fixture schema.
2. Add false-positive class fixtures from calibration cases.
3. Add `techno-search false-positive-summary`.
4. Add tests for false-positive summary by class and track.
5. Wire false-positive summary into `validate-all`.
6. Wire false-positive summary into `validation-summary`.
7. Update validation docs for false-positive class diagnostics.
8. Update roadmap/status to mark false-positive class analysis complete.
9. Run focused validation and commit.
10. Push `main` and confirm sync.
11. Add human-review queue packet schema.
12. Add triage label enum/allowed values.
13. Add reviewer notes structure.
14. Add `techno-search review-queue-summary`.
15. Add tests and docs for the human-review queue scaffold.

Each step should update this file and merge to `main` if needed.

## False-Positive/Human-Review Step 1 — False-Positive Analysis Schema

Status: implemented.

Added:

- `FALSE_POSITIVE_ANALYSIS_SCHEMA_VERSION`
- `FALSE_POSITIVE_ANALYSIS_DISCLAIMER`
- class, track, pathway, candidate-ID, and fixture-name summary fields

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 2 — Calibration-Derived Class Fixtures

Status: implemented.

Reused the existing synthetic calibration false-positive cases as the source fixture set for class analysis. This keeps the diagnostic tied to the scored calibration cases and avoids introducing an unscored duplicate fixture list.

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 3 — False-Positive Summary CLI

Status: implemented.

Added:

- `techno-search false-positive-summary`
- optional `--fixture-path`
- conservative JSON output with synthetic diagnostic disclaimer

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 4 — False-Positive Summary Tests

Status: implemented.

Added tests for:

- class count
- track count
- nested track-and-class counts
- CLI output and disclaimer language

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 5 — Validate-All Wiring

Status: implemented.

Added `false_positive_summary` to `validate-all` with gates for expected synthetic case and class coverage.

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 6 — Validation Summary Wiring

Status: implemented.

Added:

- `false_positive_case_count`
- `false_positive_class_count`

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 7 — Validation Docs

Status: implemented.

Updated:

- `docs/CLI_USAGE.md`
- `docs/VALIDATION.md`

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 8 — Roadmap And Status

Status: implemented.

Updated:

- `docs/ROADMAP.md`
- `docs/PROJECT_STATUS.md`

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 9 — Focused Validation And Commit

Status: implemented.

Validation passed:

```bash
.venv/bin/python -m pytest tests/test_calibration_fixtures.py tests/test_cli.py tests/test_docs.py
.venv/bin/ruff check src/techno_search/calibration.py src/techno_search/cli.py src/techno_search/__init__.py tests/test_calibration_fixtures.py tests/test_cli.py
.venv/bin/mypy src
git diff --check
```

Result:

- 36 focused tests passed
- Ruff passed
- mypy passed
- diff whitespace check passed

Commit planned:

```bash
git commit -m "Add false positive class summaries"
```

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 10 — Push Main

Status: implemented.

Pushed commit:

- `5271a93 Add false positive class summaries`

Remote sync:

```bash
git push origin main
```

Result:

- `main` pushed to `origin/main`
- remote advanced from `4652b32` to `5271a93`

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 11 — Human-Review Queue Schema

Status: implemented.

Added:

- `REVIEW_QUEUE_SCHEMA_VERSION`
- `schemas/review_queue.schema.json`
- `tests/fixtures/review_queue.json`
- schema path wiring through `schema-paths`

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 12 — Triage Label Enum

Status: implemented.

Added `TriageLabel` with allowed values:

- `needs_human_review`
- `likely_false_positive`
- `follow_up_target`
- `known_object_annotation`
- `insufficient_evidence`

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 13 — Reviewer Notes Structure

Status: implemented.

Added:

- `ReviewerNote`
- `ReviewQueueItem`
- reviewer-note coverage in the fixture and summary output

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 14 — Review Queue Summary CLI

Status: implemented.

Added:

- `techno-search review-queue-summary`
- review queue summary block in `validate-all`
- review queue counts in `validation-summary`

Merge status: already on `main`; no merge needed.

---

## False-Positive/Human-Review Step 15 — Tests, Docs, And Final Validation

Status: implemented.

Added tests and docs for:

- human-review queue fixtures
- allowed triage labels
- reviewer notes
- review queue schema paths
- review queue CLI output

Validation passed:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/ruff check .
.venv/bin/mypy src
git diff --check
```

Result:

- 154 tests passed
- 5 tests skipped
- total coverage: 92%
- Ruff passed
- mypy passed
- diff whitespace check passed

Commit planned:

```bash
git commit -m "Add human review queue summary"
```

Pushed commit:

- `bf63dc4 Add human review queue summary`

Remote sync:

```bash
git push origin main
```

Result:

- `main` pushed to `origin/main`
- remote advanced from `5271a93` to `bf63dc4`

Merge status: already on `main`; no merge needed.

---

## Fifteen-Step Reliability And Precision-Recall Expansion

User requested fifteen iterative steps:

1. Add synthetic reliability-curve fixture schema.
2. Add radio reliability curve fixture bins.
3. Add infrared reliability curve fixture bins.
4. Add anomaly reliability curve fixture bins.
5. Add `techno-search reliability-summary`.
6. Add tests for reliability summary by track and score bin.
7. Wire reliability summary into `validate-all`.
8. Wire reliability summary into `validation-summary`.
9. Add conservative docs noting these are synthetic diagnostics, not calibrated survey performance.
10. Commit and push the reliability fixture pass.
11. Add precision-recall synthetic fixture schema.
12. Add precision-recall fixtures for candidate vs false-positive classes.
13. Add `techno-search precision-recall-summary`.
14. Run full validation and commit.
15. Push `main` and confirm clean sync.

Each step should update this file and merge to `main` if needed.

## Reliability/PR Step 1 — Reliability Fixture Schema

Status: implemented.

Added:

- `RELIABILITY_SCHEMA_VERSION`
- `ReliabilityBin`
- loader validation for `synthetic_reliability_curves_v1`
- conservative disclaimer that bins are synthetic development diagnostics

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_calibration_metrics.py
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 2 — Radio Reliability Bins

Status: implemented.

Added radio reliability bins for:

- low score range
- mid score range
- high score range

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_calibration_metrics.py
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 3 — Infrared Reliability Bins

Status: implemented.

Added infrared reliability bins for:

- low score range
- mid score range
- high score range

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_calibration_metrics.py
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 4 — Anomaly Reliability Bins

Status: implemented.

Added anomaly reliability bins for:

- low score range
- mid score range
- high score range

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_calibration_metrics.py
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 5 — Reliability Summary CLI

Status: implemented.

Added:

- `techno-search reliability-summary`
- bin counts by track and score range
- synthetic mean and max absolute calibration error

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_calibration_metrics.py
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 6 — Reliability Summary Tests

Status: implemented.

Added tests proving:

- fixture bins cover radio, infrared, and anomaly tracks
- score bins cover low, mid, and high ranges
- summary reports total samples and calibration-error diagnostics

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_calibration_metrics.py
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 7 — Validate-All Reliability Wiring

Status: implemented.

Added:

- reliability summary block in `validate-all`
- validation gate requiring the expected reliability bin coverage

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 8 — Validation Summary Reliability Wiring

Status: implemented.

Added:

- `reliability_bin_count` in `validation-summary`
- `mean_absolute_calibration_error` in `validation-summary`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 9 — Reliability Docs And Status

Status: implemented.

Updated:

- `docs/CLI_USAGE.md`
- `docs/VALIDATION.md`
- `docs/ROADMAP.md`
- `docs/PROJECT_STATUS.md`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 10 — Reliability Fixture Commit

Status: implemented.

Validation passed:

- `.venv/bin/python -m pytest tests/test_calibration_metrics.py tests/test_cli.py tests/test_docs.py`
- `.venv/bin/ruff check src/techno_search/calibration_metrics.py src/techno_search/cli.py src/techno_search/__init__.py tests/test_calibration_metrics.py tests/test_cli.py`
- `.venv/bin/mypy src`
- `git diff --check`

Commit planned:

```bash
git commit -m "Add reliability summary fixtures"
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 11 — Precision-Recall Fixture Schema

Status: implemented.

Added:

- `PRECISION_RECALL_SCHEMA_VERSION`
- `PrecisionRecallCase`
- loader validation for `synthetic_precision_recall_v1`
- conservative disclaimer that fixtures are not validated classification metrics

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_calibration_metrics.py
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 12 — Precision-Recall Fixtures

Status: implemented.

Added synthetic precision-recall fixtures for:

- candidate truth class
- false-positive truth class
- radio, infrared, and anomaly tracks

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_calibration_metrics.py
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 13 — Precision-Recall Summary CLI

Status: implemented.

Added:

- `techno-search precision-recall-summary`
- precision-recall summary block in `validate-all`
- precision-recall counts and synthetic metrics in `validation-summary`
- docs/status updates for synthetic precision-recall diagnostics

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_calibration_metrics.py tests/test_cli.py tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 14 — Full Validation And Commit

Status: implemented.

Validation passed:

- `.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing`
- `.venv/bin/ruff check .`
- `.venv/bin/mypy src`
- `git diff --check`

Result:

- 149 tests passed
- 5 tests skipped
- total coverage: 92%

Commit planned:

```bash
git commit -m "Add precision recall summary fixtures"
```

Merge status: already on `main`; no merge needed.

---

## Reliability/PR Step 15 — Push Main And Confirm Clean Sync

Status: implemented.

Pushed commits:

- `64ccd81 Add reliability summary fixtures`
- `d3767dd Add precision recall summary fixtures`

Remote sync:

```bash
git push origin main
```

Result:

- `main` pushed to `origin/main`
- remote advanced from `64ccd81` to `d3767dd`

Merge status: already on `main`; no merge needed.

---

## Fifteen-Step Plot Ergonomics And Injection-Recovery Expansion

User requested fifteen iterative steps:

1. Add a `plot-artifact-summary` CLI for generated report directories.
2. Add tests for plot artifact summary counts by track/kind.
3. Improve Markdown reports with explicit links to generated SVG diagnostics.
4. Add tests proving Markdown links are present and conservative.
5. Commit and push the plot review ergonomics pass.
6. Add synthetic injection-recovery summary fixture schema.
7. Add radio injection-recovery summary fixtures.
8. Add infrared synthetic excess recovery fixtures.
9. Add archival anomaly recovery simulation fixtures.
10. Add `techno-search injection-recovery-summary`.
11. Add tests for injection-recovery summary by track and outcome.
12. Wire injection-recovery summary into `validate-all` and `validation-summary`.
13. Update `docs/ROADMAP.md`, `docs/PROJECT_STATUS.md`, and `docs/VALIDATION.md`.
14. Run full validation and commit.
15. Push `main` and confirm clean sync.

Each step should update this file and merge to `main` if needed.

## Plot/Injection Step 1 — Plot Artifact Summary CLI

Status: implemented.

Added:

- `plot_artifact_summary(...)`
- `techno-search plot-artifact-summary`
- manifest-derived counts without parsing SVG content
- missing path reporting for referenced plot artifacts

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_plotting.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 2 — Plot Artifact Summary Tests

Status: implemented.

Added tests proving:

- plot artifact summaries count entries from manifests
- counts are grouped by track and artifact kind
- generated synthetic SVG paths exist for all three current tracks

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_plotting.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 3 — Markdown Plot Artifact Links

Status: implemented.

Added:

- explicit Markdown links to generated SVG diagnostics when reports are written
- "None generated" output when plot artifacts are intentionally skipped
- regenerated example Markdown will include the SVG diagnostic links

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_reporting.py tests/test_examples.py
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 4 — Conservative Markdown Link Tests

Status: implemented.

Added tests proving:

- Markdown reports include generated SVG links
- plot artifact language remains explicitly synthetic and illustrative
- reports without generated plots still validate with an explicit "None generated" entry

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_reporting.py
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 5 — Plot Review Ergonomics Commit

Status: implemented.

Validation passed:

- `.venv/bin/python -m pytest tests/test_plotting.py tests/test_cli.py tests/test_reporting.py tests/test_examples.py tests/test_docs.py`
- `.venv/bin/ruff check src/techno_search/plotting.py src/techno_search/reporting.py src/techno_search/cli.py tests/test_plotting.py tests/test_cli.py tests/test_reporting.py`
- `.venv/bin/mypy src`
- `git diff --check`

Commit planned:

```bash
git commit -m "Add plot artifact summary and report links"
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 6 — Injection-Recovery Fixture Schema

Status: implemented.

Added:

- `INJECTION_RECOVERY_SCHEMA_VERSION`
- `InjectionRecoveryCase`
- loader validation for `synthetic_injection_recovery_v1`
- conservative disclaimer that fixtures are not calibrated sensitivity estimates

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_injection_recovery.py
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 7 — Radio Injection-Recovery Fixtures

Status: implemented.

Added radio cases for:

- recovered synthetic narrowband signal
- missed low-SNR synthetic narrowband signal

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_injection_recovery.py
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 8 — Infrared Injection-Recovery Fixtures

Status: implemented.

Added infrared cases for:

- recovered synthetic infrared excess
- dust-contaminated false alarm

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_injection_recovery.py
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 9 — Archival Anomaly Injection-Recovery Fixtures

Status: implemented.

Added anomaly cases for:

- recovered synthetic archival disappearance
- artifact-driven false alarm

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_injection_recovery.py
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 10 — Injection-Recovery Summary CLI

Status: implemented.

Added:

- `techno-search injection-recovery-summary`
- summary counts by track, outcome, injection type, and expected pathway
- synthetic recovery rate and synthetic false-alarm fraction

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_injection_recovery.py
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 11 — Injection-Recovery Summary Tests

Status: implemented.

Added tests proving:

- the fixture covers radio, infrared, and anomaly tracks
- outcomes include recovered, missed, and false alarm
- CLI output exposes track/outcome counts and synthetic rates

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_injection_recovery.py
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 12 — Injection-Recovery Validation Wiring

Status: implemented.

Added:

- injection-recovery summary block in `validate-all`
- validation gate requiring fixture coverage
- injection-recovery counts and synthetic rates in `validation-summary`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_injection_recovery.py
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 13 — Injection-Recovery Docs And Status

Status: implemented.

Updated:

- `docs/CLI_USAGE.md`
- `docs/VALIDATION.md`
- `docs/ROADMAP.md`
- `docs/PROJECT_STATUS.md`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 14 — Full Validation And Commit

Status: implemented.

Validation passed:

- `.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing`
- `.venv/bin/ruff check .`
- `.venv/bin/mypy src`
- `git diff --check`

Result:

- 143 tests passed
- 5 tests skipped
- total coverage: 92%

Commit planned:

```bash
git commit -m "Add injection recovery summaries"
```

Merge status: already on `main`; no merge needed.

---

## Plot/Injection Step 15 — Push Main And Confirm Clean Sync

Status: implemented.

Pushed commits:

- `e882ed0 Add plot artifact summary and report links`
- `e512f7f Add injection recovery summaries`

Remote sync:

```bash
git push origin main
```

Result:

- `main` pushed to `origin/main`
- remote advanced from `e882ed0` to `e512f7f`

Merge status: already on `main`; no merge needed.

---

## Fifteen-Step Validation And Plot Artifact Expansion

User requested fifteen iterative steps:

1. Update `docs/PROJECT_STATUS.md` so "Next 3 Actions" reflects completed pushed work.
2. Update `docs/ROADMAP.md` to mark provider normalization regression summaries as complete.
3. Add `techno-search validation-summary` as a concise local health dashboard.
4. Add tests for `validation-summary`.
5. Commit and push the status/validation-summary cleanup.
6. Add a lightweight plot artifact interface for reports without requiring heavy plotting dependencies.
7. Add synthetic radio waterfall placeholder plot generation.
8. Add synthetic infrared SED placeholder plot generation.
9. Add synthetic anomaly/crossmatch placeholder plot generation.
10. Wire plot artifact references into candidate report manifests.
11. Add tests proving plots are optional and reports still pass without them.
12. Update report docs and validation docs for plot artifacts.
13. Add conservative "plot is illustrative / synthetic" language where needed.
14. Run full validation and commit.
15. Push `main` and confirm clean sync.

Each step should update this file and merge to `main` if needed.

## Validation/Plot Step 1 — Project Status Next Actions

Status: implemented.

Updated:

- `docs/PROJECT_STATUS.md` completed items for provider normalization regression coverage
- `docs/PROJECT_STATUS.md` next actions to point at dependency-free report plot artifacts

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 2 — Roadmap Provider Normalization Status

Status: implemented.

Updated:

- Milestone 5 with the validation summary command
- Milestone 8 with provider normalization regression fixtures
- Milestone 8 with provider normalization summary in local validation

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 3 — Validation Summary CLI

Status: implemented.

Added:

- `techno-search validation-summary`
- concise local health fields for examples, reports, schemas, calibration, score regressions, catalog cache, and provider normalization
- recommended validation commands in the JSON output

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 4 — Validation Summary Tests

Status: implemented.

Added tests proving:

- the command exits successfully when the local health summary is clean
- candidate, schema, calibration, score-regression, catalog-cache, and provider-normalization counts are present
- the full validation command list includes mypy

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 5 — Status And Validation Summary Commit

Status: implemented.

Validation passed:

- `.venv/bin/python -m pytest tests/test_cli.py tests/test_docs.py`
- `.venv/bin/ruff check src/techno_search/cli.py tests/test_cli.py`
- `.venv/bin/mypy src`
- `git diff --check`

Commit planned:

```bash
git commit -m "Add validation summary command"
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 6 — Lightweight Plot Artifact Interface

Status: implemented.

Added:

- `techno_search.plotting.PlotArtifact`
- dependency-free SVG writing via `write_synthetic_plot_artifacts(...)`
- manifest-safe plot artifact entries with media type, kind, track, synthetic flag, and disclaimer

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_plotting.py tests/test_reporting.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 7 — Radio Waterfall Placeholder

Status: implemented.

Added:

- synthetic radio waterfall-style SVG generation
- SNR and drift-rate proxy annotations
- conservative SVG description/disclaimer text

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_plotting.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 8 — Infrared SED Placeholder

Status: implemented.

Added:

- synthetic infrared SED-style SVG generation
- IR excess and confusion proxy annotations
- dependency-free rendering from candidate feature values

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_plotting.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 9 — Anomaly Crossmatch Placeholder

Status: implemented.

Added:

- synthetic archival crossmatch-style SVG generation
- crossmatch-confidence and artifact proxy annotations
- conservative generated diagnostic text

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_plotting.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 10 — Plot References In Manifests

Status: implemented.

Added:

- report manifest `plot_artifacts` entries
- batch manifest `plot_artifact_paths`
- generated plot paths in `ReportPaths`
- CLI support for default plot generation and `--no-plot-artifacts`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_reporting.py tests/test_cli.py tests/test_examples.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 11 — Optional Plot Tests

Status: implemented.

Added tests proving:

- report writers can skip plot artifacts
- manifests can contain an empty `plot_artifacts` list
- report manifest validation accepts missing optional plot artifact fields
- CLI `--no-plot-artifacts` suppresses SVG generation

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_reporting.py tests/test_validation.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 12 — Plot Artifact Docs

Status: implemented.

Updated:

- `docs/CLI_USAGE.md` for generated SVG artifacts and `--no-plot-artifacts`
- `docs/VALIDATION.md` for optional plot artifact validation behavior
- `schemas/report_manifest.schema.json` and `schemas/batch_manifest.schema.json` for plot artifact metadata

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_json_schemas.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 13 — Conservative Plot Language

Status: implemented.

Added:

- shared plot artifact disclaimer
- SVG title/description disclaimers
- Markdown report plot artifact note
- docs language describing plot artifacts as optional review context

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_reporting.py tests/test_plotting.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 14 — Full Validation And Commit

Status: implemented.

Validation passed:

- `.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing`
- `.venv/bin/ruff check .`
- `.venv/bin/mypy src`
- `git diff --check`

Result:

- 138 tests passed
- 5 tests skipped
- total coverage: 92%

Commit planned:

```bash
git commit -m "Add synthetic plot artifacts to reports"
```

Merge status: already on `main`; no merge needed.

---

## Validation/Plot Step 15 — Push Main And Confirm Clean Sync

Status: implemented.

Pushed commits:

- `620b283 Add validation summary command`
- `dad5ddb Add synthetic plot artifacts to reports`

Remote sync:

```bash
git push origin main
```

Result:

- `main` pushed to `origin/main`
- remote advanced from `620b283` to `dad5ddb`

Merge status: already on `main`; no merge needed.

---

## Fifteen-Step Catalog Cache And Normalization Expansion

User requested fifteen iterative steps:

1. Add catalog cache storage implementation behind `CatalogCachePolicy`.
2. Add tests proving catalog cache storage never writes into committed paths.
3. Add `techno-search catalog-cache-summary`.
4. Add catalog cache summary tests.
5. Update docs/status and commit catalog cache storage work.
6. Add provider cache integration tests for Gaia, IRSA, VizieR, SIMBAD, and Breakthrough Listen.
7. Add provider-specific normalization refinements for Gaia TAP metadata.
8. Add provider-specific normalization refinements for IRSA catalog metadata.
9. Add provider-specific normalization refinements for VizieR catalog metadata.
10. Add provider-specific normalization refinements for SIMBAD object metadata.
11. Add provider-specific normalization refinements for Breakthrough Listen file metadata.
12. Add a provider normalization regression fixture set.
13. Wire provider normalization summaries into `validate-all`.
14. Run full validation and commit.
15. Push `main` to GitHub and confirm clean sync.

Each step should update this file and merge to `main` if needed.

## Catalog Cache/Normalization Step 1 — Catalog Cache Storage

Status: implemented.

Added:

- `CatalogCache` metadata-only storage helper
- policy-backed metadata paths and suffix checks
- required provenance field validation
- metadata size enforcement
- read/write/summary methods that do not implement catalog ingestion

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 2 — Catalog Cache Storage Tests

Status: implemented.

Added tests proving:

- catalog cache writes only under the configured policy root
- required provenance fields are enforced
- oversized metadata is rejected
- cache paths under project `cache/` are rejected by commit-path validation
- local override paths outside the project are allowed by commit-path validation

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 3 — Catalog Cache Summary CLI

Status: implemented.

Added:

- `techno-search catalog-cache-summary`
- optional `--cache-root`
- metadata counts without reading catalog payloads
- no directory creation for empty cache roots

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 4 — Catalog Cache Summary Tests

Status: implemented.

Added tests proving:

- `catalog-cache-summary` reports empty cache roots without creating directories
- populated metadata directories report provider counts and byte totals
- summary output remains metadata-only and does not implement ingestion

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 5 — Catalog Cache Docs And Commit

Status: implemented.

Updated:

- `docs/CLI_USAGE.md`
- `docs/CATALOG_CACHE_POLICY.md`
- `docs/PROJECT_STATUS.md`
- `docs/ROADMAP.md`
- `CLAUDE.md` handoff notes for catalog cache storage

Commit planned:

```bash
git commit -m "Add catalog cache storage"
```

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_cli.py tests/test_docs.py
.venv/bin/ruff check .
.venv/bin/mypy src
git diff --check
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 6 — Provider Cache Integration Tests

Status: implemented.

Added:

- cache integration coverage for Gaia, IRSA, VizieR, SIMBAD, and Breakthrough Listen
- injected transports for networked providers
- local temporary file metadata for Breakthrough Listen
- proof that a second fetch reuses `LiveProviderCache`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 7 — Gaia Normalization Refinements

Status: implemented.

Added Gaia response metadata fields for:

- TAP response format
- query endpoint
- content byte count
- raw provider field names
- normalized row field names

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 8 — IRSA Normalization Refinements

Status: implemented.

Added IRSA response metadata fields for:

- catalog response format
- query endpoint
- content byte count
- normalized row count
- normalized row field names

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 9 — VizieR Normalization Refinements

Status: implemented.

Added VizieR response metadata fields for:

- TSV response format
- query endpoint
- normalized row count
- normalized row field names

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 10 — SIMBAD Normalization Refinements

Status: implemented.

Added SIMBAD response metadata fields for:

- object lookup response format
- query endpoint
- normalized row count
- normalized row field names

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 11 — Breakthrough Listen Normalization Refinements

Status: implemented.

Added Breakthrough Listen response metadata fields for:

- local-file response format
- file name and suffix
- file existence
- content-read flag
- size bytes when available

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 12 — Provider Normalization Regression Fixtures

Status: implemented.

Added:

- `tests/fixtures/provider_normalization_regressions.json`
- regression summary loader
- regression summary test covering all five providers

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 13 — Validate-All Provider Normalization Summary

Status: implemented.

Added:

- provider normalization regression summary in `techno-search validate-all`
- validation gate requiring the provider normalization summary to cover current cases
- CLI assertion for provider normalization coverage

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 14 — Full Validation And Commit

Status: implemented.

Validation passed:

- `.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing`
- `.venv/bin/ruff check .`
- `.venv/bin/mypy src`
- `git diff --check`

Result:

- 131 tests passed
- 5 tests skipped
- total coverage: 92%

Commit planned:

```bash
git commit -m "Add provider normalization regression summary"
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache/Normalization Step 15 — Push Main And Confirm Clean Sync

Status: implemented.

Pushed commits:

- `1ac5959 Add catalog cache storage`
- `e4d687b Add provider normalization regression summary`

Remote sync:

```bash
git push origin main
```

Result:

- `main` pushed to `origin/main`
- remote advanced from `786507b` to `e4d687b`

Merge status: already on `main`; no merge needed.

---

## Fifteen-Step Remaining Provider Expansion

User requested fifteen iterative steps:

1. Add guarded VizieR live client with mocked transport.
2. Add VizieR mocked response fixture.
3. Add VizieR `integration_live` marker test without default network access.
4. Update `CLAUDE.md`, `PROJECT_STATUS`, `ROADMAP`, and provider-interface docs.
5. Run validation and commit VizieR work.
6. Add guarded SIMBAD live client with mocked transport.
7. Add SIMBAD mocked response fixture.
8. Add SIMBAD `integration_live` marker test.
9. Update docs/status and commit SIMBAD work.
10. Add guarded Breakthrough Listen local-file metadata client.
11. Add Breakthrough Listen mocked/local metadata fixture.
12. Add local-file ingestion tests proving no large data is committed.
13. Wire provider-client summaries to distinguish `implemented`, `networked`, and `local_file_only`.
14. Run full validation and commit.
15. Push `main` to GitHub and confirm branch is clean/synced.

Each step should update this file and merge to `main` if needed.

## Remaining Provider Expansion Step 1 — Guarded VizieR Client

Status: implemented.

Added:

- guarded VizieR catalog client using `TECHNO_SEARCH_ENABLE_LIVE_DATA`
- injectable HTTP GET byte fetcher for non-networked tests
- bounded response reads
- VizieR TSV row normalization through the shared delimited-table helper

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Remaining Provider Expansion Step 2 — VizieR Mock Fixture

Status: implemented.

Added:

- `tests/fixtures/live_metadata/vizier_mock_response.metadata.json`
- fixture loader coverage for mocked VizieR response metadata
- live fixture summary expected count update

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Remaining Provider Expansion Step 3 — VizieR Integration Marker

Status: implemented.

Added:

- VizieR client test proving disabled-by-default behavior
- injected transport test for opt-in VizieR metadata fetches
- `integration_live`-marked VizieR test with injected transport and no default network dependency

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Remaining Provider Expansion Step 4 — VizieR Status Docs

Status: implemented.

Updated:

- `docs/PROJECT_STATUS.md`
- `docs/ROADMAP.md`
- `docs/LIVE_PROVIDER_INTERFACES.md`
- `CLAUDE.md` handoff notes for the VizieR step

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_cli.py tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Remaining Provider Expansion Step 5 — VizieR Validation And Commit

Status: implemented.

Validation passed:

- `.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing`
- `.venv/bin/ruff check .`
- `.venv/bin/mypy src`
- `git diff --check`

Result:

- 113 tests passed, 4 skipped
- total coverage: 93%

Commit planned:

```bash
git commit -m "Add guarded VizieR provider client"
```

Merge status: already on `main`; no merge needed.

---

## Remaining Provider Expansion Step 6 — Guarded SIMBAD Client

Status: implemented.

Added:

- guarded SIMBAD object-lookup client using `TECHNO_SEARCH_ENABLE_LIVE_DATA`
- injectable HTTP GET byte fetcher for non-networked tests
- bounded response reads
- SIMBAD tabular metadata normalization through the shared delimited-table helper

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Remaining Provider Expansion Step 7 — SIMBAD Mock Fixture

Status: implemented.

Added:

- `tests/fixtures/live_metadata/simbad_mock_response.metadata.json`
- fixture loader coverage for mocked SIMBAD response metadata
- live fixture summary expected count update

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Remaining Provider Expansion Step 8 — SIMBAD Integration Marker

Status: implemented.

Added:

- SIMBAD client test proving disabled-by-default behavior
- injected transport test for opt-in SIMBAD metadata fetches
- `integration_live`-marked SIMBAD test with injected transport and no default network dependency

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Remaining Provider Expansion Step 9 — SIMBAD Docs, Validation, And Commit

Status: implemented.

Updated:

- `docs/PROJECT_STATUS.md`
- `docs/ROADMAP.md`
- `docs/LIVE_PROVIDER_INTERFACES.md`
- `CLAUDE.md` handoff notes for the SIMBAD step

Validation passed:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/ruff check .
.venv/bin/mypy src
git diff --check
```

Commit planned:

```bash
git commit -m "Add guarded SIMBAD provider client"
```

Merge status: already on `main`; no merge needed.

Result:

- 114 tests passed, 5 skipped
- total coverage: 92%

---

## Remaining Provider Expansion Step 10 — Breakthrough Listen Local Metadata Client

Status: implemented.

Added:

- guarded Breakthrough Listen local-file metadata client
- `TECHNO_SEARCH_ENABLE_LIVE_DATA` opt-in requirement
- file `stat()` metadata without reading observation contents
- local-file-only client metadata fields

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Remaining Provider Expansion Step 11 — Breakthrough Listen Local Fixture

Status: implemented.

Added:

- `tests/fixtures/live_metadata/breakthrough_listen_local_file_mock_response.metadata.json`
- fixture loader coverage for local-file metadata response
- live fixture summary expected count update

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Remaining Provider Expansion Step 12 — Breakthrough Listen Local-File Tests

Status: implemented.

Added tests proving:

- local-file metadata client is disabled by default
- enabled client uses file `stat()` metadata only
- missing files are reported without reading contents
- local-file coverage uses temporary files rather than committed observation data
- `content_read` remains false

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Remaining Provider Expansion Step 13 — Live Client Summary Capability Fields

Status: implemented.

Added:

- `networked` field in `live-client-summary`
- `local_file_only` field in `live-client-summary`
- CLI tests for implemented/networked/local-file-only provider capability maps
- docs noting networked versus local-file-only client summaries

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Remaining Provider Expansion Step 14 — Breakthrough/Summary Validation And Commit

Status: implemented.

Updated:

- `docs/PROJECT_STATUS.md`
- `docs/ROADMAP.md`
- Breakthrough Listen local metadata tests and fixture
- live-client summary capability tests and docs

Validation passed:

- `.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing`
- `.venv/bin/ruff check .`
- `.venv/bin/mypy src`
- `git diff --check`

Result:

- 117 tests passed, 5 skipped
- total coverage: 92%

Commit planned:

```bash
git commit -m "Add Breakthrough Listen local metadata client"
```

Merge status: already on `main`; no merge needed.

---

## Remaining Provider Expansion Step 15 — Push Provider Commits

Status: implemented.

Pushed to GitHub:

- `d17205c Add guarded VizieR provider client`
- `90f7fc1 Add guarded SIMBAD provider client`
- `2dab9bd Add Breakthrough Listen local metadata client`

Push result:

```bash
git push origin main
```

Remote update:

```text
d505b99..2dab9bd  main -> main
```

Merge status: already on `main`; no merge needed.

---

## Fifteen-Step Live Provider Expansion

User requested fifteen iterative steps:

1. Push `main` to GitHub with required token scopes.
2. Add a catalog-cache validator CLI command for pre-commit/release checks.
3. Add tests for that validator CLI command.
4. Wire catalog-cache validation into `validate-all`.
5. Update release docs to include the new validator output.
6. Add a real-provider implementation plan doc for Gaia, IRSA, VizieR, SIMBAD, and Breakthrough Listen.
7. Add a provider-client result normalization interface.
8. Add tests for provider normalization contracts.
9. Implement the Gaia client behind `TECHNO_SEARCH_ENABLE_LIVE_DATA=1`.
10. Add mocked Gaia integration fixtures.
11. Add Gaia live integration test markers without enabling network by default.
12. Update `PROJECT_STATUS`, `ROADMAP`, and `CLAUDE.md`.
13. Run full validation and commit.
14. Repeat the same client pattern for IRSA as the next provider.
15. Push the new commits once GitHub credentials are working.

Each step should update this file and merge to `main` if needed.

## Live Provider Expansion Step 1 — Push Main

Status: implemented.

Result:

- `git push origin main` returned `Everything up-to-date`
- local `main` and `origin/main` were already synchronized

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 2 — Catalog Cache Validator CLI

Status: implemented.

Added:

- `techno-search catalog-cache-validate`
- structured JSON output for catalog cache commit-path validation
- nonzero exit for forbidden catalog cache paths

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 3 — Validator CLI Tests

Status: implemented.

Added tests for:

- accepting committed fixture and docs paths
- rejecting forbidden `cache/` catalog metadata paths
- rejecting forbidden `data/` catalog paths
- returning nonzero status when forbidden paths are supplied

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 4 — Validate-All Catalog Cache Wiring

Status: implemented.

Added:

- Git-tracked path collection for release-scoped catalog cache validation
- `catalog_cache_validation` block in `techno-search validate-all`
- CLI test assertion that `validate-all` reports catalog cache validation state

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 5 — Release Docs Validator Output

Status: implemented.

Updated:

- `docs/CLI_USAGE.md` with `catalog-cache-validate`
- `docs/CLI_USAGE.md` with `validate-all` catalog cache validation output
- `docs/VALIDATION.md` with direct catalog cache path validation
- `docs/RELEASE_CHECKLIST.md` with validator and `validate-all` commands

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 6 — Provider Implementation Plan

Status: implemented.

Added:

- `docs/LIVE_PROVIDER_IMPLEMENTATION_PLAN.md`
- shared real-provider requirements
- provider rollout order for Gaia, IRSA, VizieR, SIMBAD, and Breakthrough Listen
- done criteria preserving opt-in network access, provenance, fixtures, and catalog cache guardrails

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 7 — Provider Normalization Interface

Status: implemented.

Added:

- `ProviderResponseNormalizer` protocol
- `ProvenanceOnlyResponseNormalizer`
- shared `provider_response_metadata(...)`
- default provenance-only normalization path for adapters

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 8 — Provider Normalization Contract Tests

Status: implemented.

Added tests for:

- response shape metadata
- row-count summaries
- provider-status summaries
- provenance-only normalizer request context preservation

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 9 — Guarded Gaia Live Client

Status: implemented.

Added:

- guarded Gaia TAP client using `TECHNO_SEARCH_ENABLE_LIVE_DATA`
- injectable HTTP POST byte fetcher for non-networked tests
- bounded response reads
- Gaia TAP JSON row normalization
- live-client summary now reports Gaia as implemented while preserving opt-in requirement

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 10 — Mocked Gaia Integration Fixture

Status: implemented.

Added:

- `tests/fixtures/live_metadata/gaia_tap_mock_response.metadata.json`
- fixture loader coverage for mocked Gaia TAP response metadata
- live fixture summary expected count update

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 11 — Gaia Integration Marker

Status: implemented.

Added:

- `integration_live`-marked Gaia client test
- opt-in skip guard using `TECHNO_SEARCH_ENABLE_LIVE_DATA`
- injected transport so the marked test still has no default network dependency

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 12 — Status And Roadmap Updates

Status: implemented.

Updated:

- `docs/PROJECT_STATUS.md` completed, in-progress, and next-action entries
- `docs/ROADMAP.md` reporting and live-data milestone entries
- `docs/LIVE_PROVIDER_INTERFACES.md` to identify Gaia as the first guarded implementation
- `docs/CLI_USAGE.md` live-client wording
- `CLAUDE.md` handoff notes for this step

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_cli.py tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 13 — Validation And Commit

Status: implemented.

Validation passed:

- `.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing`
- `.venv/bin/ruff check .`
- `.venv/bin/mypy src`
- `git diff --check`

Result:

- 111 tests passed, 2 skipped
- total coverage: 93%

Commit planned:

```bash
git commit -m "Add guarded Gaia provider client"
```

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 14 — Guarded IRSA Provider Client

Status: implemented.

Added:

- guarded IRSA catalog client using `TECHNO_SEARCH_ENABLE_LIVE_DATA`
- injectable HTTP GET byte fetcher for non-networked tests
- bounded response reads
- small delimited table row normalization
- mocked IRSA response fixture
- opt-in `integration_live` marker coverage with injected transport
- status, roadmap, and provider interface docs updates

Validation passed:

- `.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing`
- `.venv/bin/ruff check .`
- `.venv/bin/mypy src`
- `git diff --check`

Result:

- 112 tests passed, 3 skipped
- total coverage: 93%

Commit planned:

```bash
git commit -m "Add guarded IRSA provider client"
```

Merge status: already on `main`; no merge needed.

---

## Live Provider Expansion Step 15 — Push Provider Commits

Status: implemented.

Pushed to GitHub:

- `6056039 Add guarded Gaia provider client`
- `fd5d48c Add guarded IRSA provider client`

Push result:

```bash
git push origin main
```

Remote update:

```text
27693f9..fd5d48c  main -> main
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache Guardrail Step 7 — Validator Tests

Status: implemented.

Added tests for:

- rejecting catalog cache paths under `cache/`
- rejecting catalog data paths under `data/`
- rejecting generated catalog artifacts under `artifacts/`
- allowing small committed docs and fixture paths outside forbidden roots

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache Guardrail Step 8 — Release Checklist Gate

Status: implemented.

Updated:

- `docs/RELEASE_CHECKLIST.md` artifact checks
- release validation command list with `techno-search catalog-cache-policy`
- release gate requiring catalog cache policy and commit-path validator before real provider clients

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache Guardrail Step 9 — Status And Roadmap Updates

Status: implemented.

Updated:

- `docs/PROJECT_STATUS.md` completed and in-progress entries
- `docs/PROJECT_STATUS.md` next actions for policy-gated catalog cache storage
- `docs/ROADMAP.md` reporting and live-data milestones
- `CLAUDE.md` handoff notes for this step

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_cli.py tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache Guardrail Step 10 — Validation And Commit

Status: implemented.

Validation passed:

- `.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing`
- `.venv/bin/ruff check .`
- `.venv/bin/mypy src`
- `git diff --check`

Result:

- 106 tests passed, 1 skipped
- total coverage: 94%

Commit planned:

```bash
git commit -m "Add catalog cache guardrails"
```

Merge status: already on `main`; no merge needed.

---

## Step 1 — Report File Writers

Status: implemented.

Added:

- `write_candidate_reports(scored, output_dir, filename_prefix=None)`
- `ReportPaths`
- safe filename generation from candidate IDs or explicit prefixes
- tests proving Markdown and JSON files are written with conservative content

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_reporting.py
```

---

## Step 2 — Synthetic Radio Prototype

Status: implemented.

Added:

- `src/techno_search/radio/`
- `RadioHit` and `RfiBand`
- synthetic hit-table parsing
- known RFI band overlap scoring
- ON/OFF presence feature extraction
- recurrence, frequency persistence, metadata, and data-quality features
- tests proving a clean synthetic radio candidate scores above an RFI-like candidate

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_radio_prototype.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache Guardrail Step 6 — Commit Path Validator

Status: implemented.

Added:

- `CATALOG_CACHE_FORBIDDEN_COMMITTED_ROOTS`
- `validate_catalog_cache_commit_paths(...)`
- helper for project-relative path checks
- rejection of paths under `data/`, `cache/`, and `artifacts/`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache Guardrail Step 5 — Policy Docs Warning

Status: implemented.

Updated:

- CLI docs for `catalog-cache-policy`
- `docs/CATALOG_CACHE_POLICY.md` to state the policy command is informational only
- data policy note for future catalog cache metadata versus live-provider metadata cache

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache Guardrail Step 4 — Catalog Cache Policy CLI

Status: implemented.

Added:

- `catalog_cache_policy_summary(...)`
- `techno-search catalog-cache-policy`
- optional `--cache-root`
- CLI test proving the command prints policy metadata without creating directories

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache Guardrail Step 3 — Policy Tests

Status: implemented.

Added tests for:

- default catalog cache root under `cache/catalog_metadata`
- allowed metadata suffixes
- maximum metadata file size default
- no directory creation
- local `TECHNO_SEARCH_CATALOG_CACHE_DIR` override

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Catalog Cache Guardrail Step 2 — Catalog Cache Policy

Status: implemented.

Added:

- `CATALOG_CACHE_DIR_ENV_VAR`
- `DEFAULT_CATALOG_CACHE_DIR`
- `configured_catalog_cache_dir(...)`
- `CatalogCachePolicy`
- JSON-serializable policy representation that does not create directories or implement ingestion

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Ten-Step Catalog Cache Guardrail Expansion

User requested ten iterative steps:

1. Add catalog cache metadata schema docs, separate from local live-provider metadata cache files.
2. Add `CatalogCachePolicy` dataclass for cache root, max metadata file size, allowed suffixes, and provenance requirements.
3. Add tests for catalog cache policy defaults and local override behavior.
4. Add `techno-search catalog-cache-policy` to print policy without creating cache files.
5. Add docs warning that catalog cache policy is not catalog ingestion yet.
6. Add validation helper that rejects committed catalog cache paths under `data/`, `cache/`, and `artifacts/`.
7. Add tests for the catalog cache path validator.
8. Add release checklist item for catalog cache policy/validator before real provider clients.
9. Update `PROJECT_STATUS`, `ROADMAP`, and `CLAUDE.md`.
10. Run full validation, commit, and report branch state.

## Catalog Cache Guardrail Step 1 — Metadata Schema Docs

Status: implemented.

Added:

- `docs/CATALOG_CACHE_POLICY.md`
- catalog cache metadata field list
- storage boundary between live-provider metadata cache and future catalog cache metadata
- explicit no-ingestion and no-interpretation guardrails

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

## Ten-Step Config/CI Expansion

User requested ten iterative steps:

1. Push/publish decision.
2. Add README links to examples.
3. Add CLI quickstart test.
4. Add batch manifest regeneration test.
5. Add report manifest schema checks.
6. Add calibration fixture loader.
7. Add calibration summary CLI.
8. Add scoring config use in pathway.
9. Add track config use in prototypes.
10. Add first CI workflow.

Each step should update this file and merge to `main` if needed.

---

## Config/CI Step 1 — Publish Decision

Status: implemented as documentation.

Updated:

- `docs/PUBLISHING.md`
- recent local commit list
- owner-controlled publication recommendation
- reminder that direct automated push remains out of scope

Merge status: already on `main`; no merge needed.

---

## Config/CI Step 2 — README Example Links

Status: implemented.

Updated README quickstart with links to:

- single radio Markdown packet
- single radio manifest
- batch manifest
- batch radio packet
- batch infrared packet
- batch anomaly packet

Merge status: already on `main`; no merge needed.

---

## Config/CI Step 3 — README Quickstart Test

Status: implemented.

Added:

- README quickstart command assertions
- README linked example artifact existence checks

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Config/CI Step 4 — Batch Manifest Regeneration Test

Status: implemented.

Added:

- `score_batch(...)` regeneration test using `examples/candidates`
- expected candidate set assertions
- regenerated Markdown/JSON/manifest file checks

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Config/CI Step 5 — Manifest Schema Checks

Status: implemented.

Added:

- expected per-candidate manifest field set
- expected batch manifest field set
- expected batch report entry field set
- tests for single example manifests and batch manifests

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_examples.py
```

Merge status: already on `main`; no merge needed.

---

## Config/CI Step 6 — Calibration Fixture Loader

Status: implemented.

Added:

- `src/techno_search/calibration.py`
- `CalibrationFixture`
- `CalibrationSummary`
- `load_calibration_fixtures(...)`
- `summarize_calibration_fixtures(...)`
- tests using the loader instead of ad hoc JSON parsing

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_calibration_fixtures.py
```

Merge status: already on `main`; no merge needed.

---

## Config/CI Step 7 — Calibration Summary CLI

Status: implemented.

Added:

- `techno-search calibration-summary`
- optional `--fixture-path`
- JSON output using `CalibrationSummary.as_dict()`
- CLI test for fixture counts
- CLI usage docs

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Five-Step Quickstart/Batch/Calibration Expansion

User requested five iterative steps:

1. Add README quickstart.
2. Add batch example artifacts.
3. Add aggregate manifest tests.
4. Add CLI docs tests.
5. Add calibration expansion fixtures.

Each step should update this file and merge to `main` if needed.

---

## Quickstart Step 1 — README Quickstart

Status: implemented.

Added:

- local environment install command
- single-candidate CLI scoring command
- report-writing command
- batch scoring command
- conservative review-packet warning

Merge status: already on `main`; no merge needed.

---

## Quickstart Step 2 — Batch Example Artifacts

Status: implemented.

Generated with:

```bash
.venv/bin/techno-search score-batch examples/candidates examples/batch_reports
```

Added:

- per-candidate Markdown/JSON/manifest artifacts in `examples/batch_reports/`
- aggregate `examples/batch_reports/batch_manifest.json`

Merge status: already on `main`; no merge needed.

---

## Quickstart Step 3 — Aggregate Manifest Tests

Status: implemented.

Added:

- tests for `examples/batch_reports/batch_manifest.json`
- candidate coverage assertions
- per-candidate path existence assertions
- pathway and track assertions
- conservative disclaimer checks for batch Markdown reports

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_examples.py
```

Merge status: already on `main`; no merge needed.

---

## Quickstart Step 4 — CLI Docs Tests

Status: implemented.

Added:

- `tests/test_docs.py`
- `docs/CLI_USAGE.md` path/command checks
- `docs/PUBLISHING.md` validation-command checks
- existence checks for referenced example files

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Quickstart Step 5 — Calibration Expansion Fixtures

Status: implemented.

Added false-positive fixtures for:

- radio band-edge artifact
- radio instrumental artifact
- infrared AGB-like colors
- infrared bad photometry
- archival moving object
- archival catalog mismatch

Updated:

- `tests/fixtures/calibration_false_positives.json`
- `docs/CALIBRATION_FIXTURES.md`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_calibration_fixtures.py
```

Merge status: already on `main`; no merge needed.

---

## Five-Step Docs/Batch CLI Expansion

User requested five iterative steps:

1. Push or publish safely.
2. Add CLI usage docs.
3. Add calibration documentation.
4. Add batch scoring CLI.
5. Add installed-console-script test.

Each step should update this file and merge to `main` if needed.

---

## Docs/Batch Step 1 — Safe Publish Options

Status: implemented locally.

Added:

- `docs/PUBLISHING.md`
- current local commit state
- note that automated `git push origin main` was blocked by environment policy
- safe owner-controlled publication options
- pre-publish validation checklist

Merge status: already on `main`; no merge needed.

---

## Docs/Batch Step 2 — CLI Usage Docs

Status: implemented.

Added:

- `docs/CLI_USAGE.md`
- install and help instructions
- single-candidate scoring examples
- report writing examples
- normalized input JSON shape
- output and manifest expectations
- conservative CLI guardrails

Merge status: already on `main`; no merge needed.

---

## Docs/Batch Step 3 — Calibration Documentation

Status: implemented.

Added:

- `docs/CALIBRATION_FIXTURES.md`
- fixture table by false-positive class
- expected pathway documentation
- requirements for adding future fixtures
- future fixture expansion list
- calibration guardrails

Merge status: already on `main`; no merge needed.

---

## Docs/Batch Step 4 — Batch Scoring CLI

Status: implemented.

Added:

- `techno-search score-batch INPUT_DIR OUTPUT_DIR`
- per-candidate Markdown, JSON, and manifest output
- aggregate `batch_manifest.json`
- optional batch filename prefix
- batch CLI docs
- tests for batch scoring two synthetic candidate packets

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Docs/Batch Step 5 — Installed Console-Script Smoke Test

Status: implemented.

Added:

- `tests/test_console_script.py`
- direct `.venv/bin/techno-search score ...` subprocess smoke test
- JSON parse assertion for installed console script output

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_console_script.py
```

Merge status: already on `main`; no merge needed.

---

## Five-Step CLI/Examples/Calibration Expansion

User requested five iterative steps:

1. Push the foundation commit.
2. Add CLI entry points.
3. Add example review packets.
4. Add calibration fixture sets.
5. Add persistence/report manifest.

Each step should update this file and merge to `main` if needed.

---

## CLI Expansion Step 1 — Push Foundation Commit

Status: blocked by environment policy.

Attempted:

```bash
git push origin main
```

Result:

- The local branch was clean and ahead of `origin/main` by one commit.
- The push was rejected by the escalation reviewer because pushing `main` mutates an external remote.
- No workaround was attempted.

Current local commit remains:

```text
5c1c6ae Build synthetic scoring foundation
```

Merge status: already on `main`; no merge needed.

---

## CLI Expansion Step 2 — CLI Entry Points

Status: implemented.

Added:

- `src/techno_search/cli.py`
- `techno-search` console script entry point
- `techno-search score candidate.json`
- optional `--output-dir` and `--prefix` report writing
- CLI tests for stdout JSON and Markdown/JSON report file output

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## CLI Expansion Step 3 — Example Review Packets

Status: implemented.

Added:

- `examples/candidates/radio_clean_candidate.json`
- `examples/candidates/infrared_clean_candidate.json`
- `examples/candidates/anomaly_clean_candidate.json`
- generated Markdown and JSON packets under `examples/reports/`
- tests proving example packets exist and include conservative disclaimers

Generation command shape:

```bash
.venv/bin/python -m techno_search.cli score examples/candidates/radio_clean_candidate.json --output-dir examples/reports --prefix example-radio-clean
```

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_examples.py
```

Merge status: already on `main`; no merge needed.

---

## CLI Expansion Step 4 — Calibration Fixture Sets

Status: implemented.

Added:

- `tests/fixtures/calibration_false_positives.json`
- RFI fixture
- AGN/blend fixture
- dust/YSO-style fixture
- archival image-artifact fixture
- proper-motion fixture
- survey-depth mismatch fixture
- tests proving all calibration false-positive fixtures route to `do_not_submit_false_positive`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_calibration_fixtures.py
```

Merge status: already on `main`; no merge needed.

---

## CLI Expansion Step 5 — Report Manifest

Status: implemented; validation passed.

Added:

- manifest generation when reports are written
- `report_manifest(...)`
- `report_manifest_json(...)`
- `ReportPaths.manifest_path`
- manifest fields for candidate ID, track, pathway, output paths, config version, git commit when available, and UTC generation timestamp
- tests for persisted manifests and CLI-created manifests

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_reporting.py tests/test_cli.py tests/test_examples.py
```

Merge status: already on `main`; no merge needed.

Overall status for this five-step batch:

- Step 1 push was blocked by environment policy.
- Steps 2-5 were implemented locally on `main`.
- Full validation passed with 38 tests.
- A local commit should be created after this note.

---

## Five-Step Expansion

User requested five iterative steps:

1. Add radio waterfall placeholder/report interface.
2. Add synthetic radio injection tests.
3. Start infrared prototype.
4. Start archival anomaly prototype.
5. Commit the current foundation.

Each step should update this file and merge to `main` if needed.

---

## Expansion Step 1 — Radio Diagnostic Placeholder/Report Interface

Status: implemented.

Added:

- `RadioDiagnosticPaths`
- optional diagnostic fields in radio candidate feature packets
- Markdown report `Diagnostics` section
- tests for diagnostic placeholder propagation

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_radio_prototype.py tests/test_reporting.py
```

Merge status: already on `main`; no merge needed.

---

## Expansion Step 2 — Synthetic Radio Injection Tests

Status: implemented.

Added:

- `SyntheticRadioInjection`
- injection hit-row generation
- `injection_recovery_score(...)`
- radio candidate feature propagation for `injection_recovery_score`
- tests proving recovered injections improve candidate-interest posterior relative to missed injections

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_radio_injection.py tests/test_radio_prototype.py
```

Merge status: already on `main`; no merge needed.

---

## Expansion Step 3 — Infrared Prototype

Status: implemented.

Added:

- `src/techno_search/infrared/`
- `InfraredSource`
- synthetic Gaia/WISE-like row normalization
- derived IR-excess, SED residual, and stellar-solution features
- AGN, dust, confusion, photometric-quality, and artifact feature propagation
- tests proving a clean synthetic infrared-excess candidate scores above an AGN/confused source

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_infrared_prototype.py
```

Merge status: already on `main`; no merge needed.

---

## Expansion Step 4 — Archival Anomaly Prototype

Status: implemented.

Added:

- `src/techno_search/anomalies/`
- `ArchivalAnomaly`
- synthetic historical-modern source comparison normalization
- magnitude-change and modern non-detection features
- cross-match, proper-motion, survey-depth, artifact, moving-object, variability, and catalog-mismatch features
- tests proving a clean synthetic archival anomaly scores above an artifact false positive

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_anomaly_prototype.py
```

Merge status: already on `main`; no merge needed.

---

## Expansion Step 5 — Foundation Commit

Status: implemented; validation passed; commit is part of this step.

Scope to commit:

- documentation foundation updates
- local system profile
- Python package scaffold
- conservative v0 scoring and pathway core
- report packet generation and file writers
- synthetic radio prototype, diagnostic placeholders, and injection helpers
- synthetic infrared prototype
- synthetic archival anomaly prototype
- track-specific configs and tests

Validation before commit:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src
git diff --check
```

Merge status: already on `main`; no merge needed.

---

## Step 3 — Track-Specific Configs

Status: implemented.

Added:

- `configs/radio_search_v0.json`
- `configs/infrared_search_v0.json`
- `configs/anomaly_search_v0.json`
- `TrackConfig`
- `load_track_config(track)`
- tests for all three track configs

Config policy:

- Use JSON for v0 so no parser dependency is needed.
- Keep thresholds, feature defaults, assumptions, and raw metadata auditable.
- Do not let config defaults bypass false-positive evidence or provenance rules.

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_config.py
```

Merge status: already on `main`; no merge needed.

---

## Config/CI Step 8 — Scoring Config Pathway Wiring

Status: implemented.

Added:

- `score_candidate(..., thresholds=None)` support for explicit pathway thresholds
- default scoring pathway thresholds loaded from `configs/scoring_v0.json`
- regression test proving supplied thresholds change pathway routing

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_scoring.py
```

Merge status: already on `main`; no merge needed.

---

## Config/CI Step 9 — Track Config Prototype Wiring

Status: implemented.

Added:

- optional `track_config` inputs for radio, infrared, and archival anomaly prototype builders
- configured feature-default use for missing synthetic feature values
- configured provenance-completeness fallback for packets without provenance
- tests proving each prototype consumes supplied `TrackConfig` defaults

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_radio_prototype.py tests/test_infrared_prototype.py tests/test_anomaly_prototype.py
```

Merge status: already on `main`; no merge needed.

---

## Config/CI Step 10 — First CI Workflow

Status: deferred.

Reason:

- GitHub rejected the push because the current Personal Access Token does not have `workflow` scope.
- Do not include `.github/workflows/ci.yml` in pushed history until the project owner pushes with a token that has `workflow` scope.
- The intended workflow should run Python 3.11, install `.[dev]`, run non-live tests with coverage, run Ruff, and run mypy.

Validation for this step should include:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src
git diff --check
```

Merge status: already on `main`; no merge needed.

---

## Ten-Step Validation/Regression Expansion

User requested ten iterative steps:

1. Confirm GitHub push succeeds after the amended commit.
2. Keep CI workflow deferred until a token with `workflow` scope is available.
3. Add candidate JSON validation CLI.
4. Add generated report validation CLI.
5. Add JSON schema files for candidate packets and manifests.
6. Expand calibration false-positive edge cases.
7. Add score regression snapshots.
8. Add config-version provenance into scored packets and batch manifests.
9. Add golden example stable-field tests.
10. Add opt-in live-data integration scaffold.

Each step should update this file and merge to `main` if needed.

---

## Validation/Regression Step 1 — GitHub Push Confirmation

Status: confirmed.

Observation:

- Local `main` is even with `origin/main`, so the amended workflow-free history appears pushed.
- No merge was needed because work is already on `main`.

Merge status: already on `main`; no merge needed.

---

## Validation/Regression Step 2 — CI Workflow Deferred

Status: documented as deferred.

Reason:

- GitHub rejects workflow-file pushes unless the active token has `workflow` scope.
- Keep CI as a future separate commit once the project owner has a suitable token.
- Local validation remains the required gate: pytest with coverage, Ruff, mypy, and `git diff --check`.

Merge status: already on `main`; no merge needed.

---

## Validation/Regression Step 3 — Candidate Validation CLI

Status: implemented.

Added:

- `src/techno_search/validation.py`
- `ValidationResult`
- candidate mapping/file validation
- conservative-language checks for unsupported phrases
- `techno-search validate-candidate`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Regression Step 4 — Report Validation CLI

Status: implemented.

Added:

- generated report packet validation
- per-candidate report manifest validation
- required disclaimer and evidence-section checks
- `techno-search validate-reports`
- CLI tests for generated report directories

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Regression Step 5 — JSON Schema Artifacts

Status: implemented.

Added:

- `schemas/candidate_packet.schema.json`
- `schemas/report_manifest.schema.json`
- `schemas/batch_manifest.schema.json`
- schema parseability and example-field coverage tests

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_json_schemas.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Regression Step 6 — Expanded Calibration Edge Cases

Status: implemented.

Added false-positive fixtures for:

- radio satellite-like recurrence
- infrared extragalactic contamination
- archival anomaly variable-star behavior

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_calibration_fixtures.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Regression Step 7 — Score Regression Snapshots

Status: implemented.

Added:

- `tests/fixtures/score_regressions.json`
- stable score/pathway snapshots for the three example candidates
- regression test comparing example scores and posteriors to snapshots

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_score_regressions.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Regression Step 8 — Config-Version Provenance

Status: implemented.

Added:

- top-level `config_version` in candidate JSON packets
- config-version fallback of `scoring_v0` for sparse provenance
- `config_version` in batch manifests and batch report entries
- updated schema and example artifact checks

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_reporting.py tests/test_cli.py tests/test_examples.py tests/test_json_schemas.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Regression Step 9 — Golden Example Stable Fields

Status: implemented.

Added:

- temporary regeneration of example batch reports in tests
- stable-field comparison against committed example packets
- timestamp/path-independent golden coverage for scores, pathways, evidence, disclaimer, and config version

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_examples.py
```

Merge status: already on `main`; no merge needed.

---

## Validation/Regression Step 10 — Opt-In Live-Data Scaffold

Status: implemented.

Added:

- `src/techno_search/live_data.py`
- `TECHNO_SEARCH_ENABLE_LIVE_DATA` opt-in guard
- base `LiveDataClient` scaffold with no default network access
- default disabled test and skipped `integration_live` scaffold test

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Ten-Step Documentation/Release Expansion

User requested ten iterative tasks:

1. Push commit `9ef0b8a` to GitHub.
2. Add README and CLI docs for `validate-candidate` and `validate-reports`.
3. Add schema links to README and `docs/PIPELINE_SPEC.md`.
4. Add `docs/LIVE_DATA_INTEGRATIONS.md`.
5. Add malformed validation tests.
6. Add `techno-search schema-paths`.
7. Add `techno-search score-regression-summary`.
8. Add conservative release checklist doc.
9. Update project status and roadmap.
10. Add a GitHub-safe CI template outside `.github/workflows`.

Each step should update this file and merge to `main` if needed.

---

## Documentation/Release Step 1 — Push Attempt

Status: blocked by environment policy.

Result:

- Attempted `git push origin main`.
- The environment rejected the push because updating the external GitHub `main` branch is disallowed by tenant policy.
- No workaround was attempted.

Merge status: already on `main`; no merge needed.

---

## Documentation/Release Step 2 — Validation Command Docs

Status: implemented.

Updated:

- README quickstart with `validate-candidate`
- README quickstart with `validate-reports`
- `docs/CLI_USAGE.md` validation command sections

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Documentation/Release Step 3 — Schema Links

Status: implemented.

Updated:

- README links to candidate packet, report manifest, and batch manifest schemas
- `docs/PIPELINE_SPEC.md` schema references for shared candidate and manifest outputs

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_json_schemas.py
```

Merge status: already on `main`; no merge needed.

---

## Documentation/Release Step 4 — Live Data Integration Policy

Status: implemented.

Added:

- `docs/LIVE_DATA_INTEGRATIONS.md`
- opt-in guard documentation for `TECHNO_SEARCH_ENABLE_LIVE_DATA`
- `integration_live` test policy
- provenance and cache/credential guardrails

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Documentation/Release Step 5 — Malformed Validation Tests

Status: implemented.

Added:

- bad candidate track validation test
- non-mapping feature validation test
- missing report manifest validation test
- empty report directory validation test

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_validation.py
```

Merge status: already on `main`; no merge needed.

---

## Documentation/Release Step 6 — Schema Paths CLI

Status: implemented.

Added:

- `techno-search schema-paths`
- deterministic schema path JSON output
- CLI test for schema path keys and candidate packet schema path
- CLI usage documentation

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Documentation/Release Step 7 — Score Regression Summary CLI

Status: implemented.

Added:

- `techno-search score-regression-summary`
- optional `--snapshot-path`
- snapshot counts by track and recommended pathway
- CLI test for current regression fixture coverage
- CLI usage documentation

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Documentation/Release Step 8 — Conservative Release Checklist

Status: implemented.

Added:

- `docs/RELEASE_CHECKLIST.md`
- required local validation commands
- artifact and schema release checks
- scientific-language release guardrails
- live-data and GitHub workflow-token caveats

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Documentation/Release Step 9 — Status And Roadmap Updates

Status: implemented.

Updated:

- `docs/PROJECT_STATUS.md` completed items and next actions
- `docs/ROADMAP.md` reporting, calibration, and live-data milestones

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Documentation/Release Step 10 — GitHub-Safe CI Template

Status: implemented.

Added:

- `docs/templates/ci.yml`
- note that it should only be copied into `.github/workflows/` with a token that has `workflow` scope
- release checklist link to the template

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Ten-Step Validation Tooling Expansion

User requested ten iterative items:

1. Push local commits to GitHub.
2. Add `docs/VALIDATION.md`.
3. Add `techno-search validate-all`.
4. Add `techno-search regenerate-examples`.
5. Add deterministic regenerate-example tests.
6. Add docs for example regeneration.
7. Add schema versioning policy.
8. Add explicit `schema_version` fields.
9. Add tests enforcing `schema_version`.
10. Update project status, roadmap, and this file.

Each step should update this file and merge to `main` if needed.

---

## Validation Tooling Step 1 — Push Attempt

Status: blocked by environment policy.

Result:

- Attempted `git push origin main`.
- The environment rejected the push because updating the external GitHub `main` branch is disallowed by tenant policy.
- No workaround was attempted.

Merge status: already on `main`; no merge needed.

---

## Validation Tooling Step 2 — Validation Guide

Status: implemented.

Added:

- `docs/VALIDATION.md`
- local validation gate commands
- candidate/report validation command docs
- schema, score regression, and example regeneration notes

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Validation Tooling Step 3 — Validate-All CLI

Status: implemented.

Added:

- `techno-search validate-all`
- candidate validation summary
- report validation summary
- schema path existence checks
- calibration and score regression summaries
- CLI test coverage

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Validation Tooling Step 4 — Regenerate Examples CLI

Status: implemented.

Added:

- `techno-search regenerate-examples`
- regeneration of `examples/reports`
- regeneration of `examples/batch_reports`
- relative output paths for committed artifacts

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_examples.py
```

Merge status: already on `main`; no merge needed.

---

## Validation Tooling Step 5 — Deterministic Regeneration Tests

Status: implemented.

Added:

- CLI test that regenerates examples in an isolated temporary directory
- existing golden example stable-field test continues to compare regenerated report fields against committed artifacts

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_examples.py
```

Merge status: already on `main`; no merge needed.

---

## Validation Tooling Step 6 — Example Regeneration Docs

Status: implemented.

Updated:

- `docs/CLI_USAGE.md`
- `docs/VALIDATION.md`
- README validation links

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Validation Tooling Step 7 — Schema Versioning Policy

Status: implemented.

Added:

- `docs/SCHEMA_VERSIONING.md`
- schema compatibility policy
- current `techno_search_packet_v1` documentation

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_json_schemas.py
```

Merge status: already on `main`; no merge needed.

---

## Validation Tooling Step 8 — Schema Version Fields

Status: implemented.

Added:

- `schema_version` in candidate packets
- `schema_version` in per-candidate report manifests
- `schema_version` in batch manifests
- regenerated committed example artifacts

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_reporting.py tests/test_examples.py tests/test_json_schemas.py
```

Merge status: already on `main`; no merge needed.

---

## Validation Tooling Step 9 — Schema Version Tests

Status: implemented.

Added:

- example artifact assertions for `schema_version`
- schema required-field assertions for `schema_version`
- reporting assertions for `schema_version`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_reporting.py tests/test_examples.py tests/test_json_schemas.py
```

Merge status: already on `main`; no merge needed.

---

## Validation Tooling Step 10 — Status And Roadmap Updates

Status: implemented.

Updated:

- `docs/PROJECT_STATUS.md`
- `docs/ROADMAP.md`
- `docs/RELEASE_CHECKLIST.md`
- this file

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Ten-Step Live Provider/Provenance Expansion

User requested ten iterative tasks:

1. Push local commits to GitHub.
2. Add provider-specific live-data adapter interfaces for Gaia, IRSA, VizieR, SIMBAD, and Breakthrough Listen behind the opt-in guard.
3. Add mocked tests proving provider adapters do not perform network access by default.
4. Add `docs/LIVE_PROVIDER_INTERFACES.md`.
5. Add provenance helper module.
6. Wire provenance helper output into report manifests and live-data request scaffolds.
7. Add `techno-search provenance-summary`.
8. Add tests for provenance summary across `examples/reports` and `examples/batch_reports`.
9. Update schemas with provenance summary expectations.
10. Update project status, roadmap, and this file.

Each step should update this file and merge to `main` if needed.

---

## Live Provider/Provenance Step 1 — Push Attempt

Status: blocked by environment policy.

Result:

- Attempted `git push origin main`.
- The environment rejected the push because updating the external GitHub `main` branch is disallowed by tenant policy.
- No workaround was attempted.

Merge status: already on `main`; no merge needed.

---

## Live Provider/Provenance Step 2 — Provider Adapter Interfaces

Status: implemented.

Added:

- `LiveProviderAdapter`
- Gaia adapter scaffold
- IRSA adapter scaffold
- VizieR adapter scaffold
- SIMBAD adapter scaffold
- Breakthrough Listen adapter scaffold
- shared constants module for schema and scoring config versions

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider/Provenance Step 3 — Provider Adapter Default-Off Tests

Status: implemented.

Added:

- provider adapter request-building test
- provider-name coverage for Gaia, IRSA, VizieR, SIMBAD, and Breakthrough Listen
- assertions that adapter fetches raise `LiveDataDisabledError` by default

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider/Provenance Step 4 — Live Provider Interface Docs

Status: implemented.

Added:

- `docs/LIVE_PROVIDER_INTERFACES.md`
- adapter responsibilities
- provenance fields
- cache policy
- conservative scientific guardrails

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider/Provenance Step 5 — Provenance Helper Module

Status: implemented.

Added:

- `src/techno_search/provenance.py`
- `ProvenanceRecord`
- `build_provenance_record(...)`
- `candidate_provenance_record(...)`
- provenance unit tests

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_provenance.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider/Provenance Step 6 — Provenance Wiring

Status: implemented.

Added:

- `provenance_summary` in report manifests
- shared git commit helper usage
- live-data request provenance record generation
- tests for report and live-data provenance summaries

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_reporting.py tests/test_live_data.py tests/test_provenance.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider/Provenance Step 7 — Provenance Summary CLI

Status: implemented.

Added:

- `techno-search provenance-summary`
- manifest counts
- counts by track, schema version, config version, and source dataset
- CLI usage docs

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider/Provenance Step 8 — Provenance Summary Tests

Status: implemented.

Added:

- provenance summary test for `examples/reports`
- provenance summary test for `examples/batch_reports`
- example manifest assertions for `provenance_summary`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_examples.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider/Provenance Step 9 — Provenance Summary Schema

Status: implemented.

Added:

- required `provenance_summary` in report manifest schema
- validation required-field update
- schema tests for `provenance_summary`
- pipeline spec note for provenance summaries

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_json_schemas.py tests/test_examples.py
```

Merge status: already on `main`; no merge needed.

---

## Live Provider/Provenance Step 10 — Status And Roadmap Updates

Status: implemented.

Updated:

- `docs/PROJECT_STATUS.md`
- `docs/ROADMAP.md`
- `docs/RELEASE_CHECKLIST.md`
- this file

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Ten-Step Mock Provider/Cache Expansion

User requested ten iterative tasks:

1. Push local commits to GitHub.
2. Add mocked provider implementations with injected fetch functions.
3. Add tests proving injected fetch functions are only called with live opt-in.
4. Add provider response normalization into provenance-only metadata records.
5. Add `techno-search live-provider-summary`.
6. Add docs for mocked provider implementations and safe test patterns.
7. Add cache-key generation helper.
8. Add deterministic cache-key tests.
9. Update schemas/docs with provider/cache provenance fields.
10. Update project status, roadmap, and this file.

Each step should update this file and merge to `main` if needed.

---

## Mock Provider/Cache Step 1 — Push Attempt

Status: blocked by environment policy.

Result:

- Attempted `git push origin main`.
- The environment rejected the push because updating the external GitHub `main` branch is disallowed by tenant policy.
- No workaround was attempted.

Merge status: already on `main`; no merge needed.

---

## Mock Provider/Cache Step 2 — Injected Provider Fetchers

Status: implemented.

Added:

- optional injected provider fetch functions
- guarded provider fetch execution
- provider-specific constructors that accept injected fetchers

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Mock Provider/Cache Step 3 — Live Opt-In Fetch Tests

Status: implemented.

Added:

- test proving injected fetchers are not called while live data is disabled
- test proving injected fetchers run only after `TECHNO_SEARCH_ENABLE_LIVE_DATA=1`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Mock Provider/Cache Step 4 — Provenance-Only Response Normalization

Status: implemented.

Added:

- `normalize_provider_response(...)`
- response metadata fields only
- no candidate interpretation in live provider response normalization

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Mock Provider/Cache Step 5 — Live Provider Summary CLI

Status: implemented.

Added:

- `techno-search live-provider-summary`
- provider names
- service URLs
- live-enabled status
- CLI test coverage

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Mock Provider/Cache Step 6 — Mock Provider Docs

Status: implemented.

Updated:

- `docs/LIVE_PROVIDER_INTERFACES.md`
- safe injected-fetch test pattern
- provenance-only response normalization guidance
- CLI usage docs for live provider summary

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Mock Provider/Cache Step 7 — Cache-Key Helper

Status: implemented.

Added:

- deterministic `build_cache_key(...)`
- request-level `cache_key()`
- cache key in live-data request provenance

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_provenance.py tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Mock Provider/Cache Step 8 — Cache-Key Tests

Status: implemented.

Added:

- deterministic cache-key test for sorted query parameters
- cache-key assertion in live provider fetch metadata test

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_provenance.py tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Mock Provider/Cache Step 9 — Provider/Cache Provenance Schema Docs

Status: implemented.

Updated:

- report manifest schema provenance summary fields
- schema tests for service URL and cache key fields
- pipeline spec provenance summary text
- live provider interface docs
- release checklist

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_json_schemas.py tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Mock Provider/Cache Step 10 — Status And Roadmap Updates

Status: implemented.

Updated:

- `docs/PROJECT_STATUS.md` completed and next-action entries
- `docs/ROADMAP.md` reporting and live-data milestone status
- `CLAUDE.md` with final step handoff notes

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_provenance.py tests/test_cli.py tests/test_json_schemas.py tests/test_examples.py tests/test_reporting.py
```

Merge status: already on `main`; no merge needed.

---

## Ten-Step Live Cache/Query Shape Expansion

User requested ten iterative steps:

1. Add local cache policy constants and ignored cache directory conventions.
2. Implement a `LiveProviderCache` helper that stores metadata by deterministic cache key.
3. Add tests proving cache writes stay outside committed example/report paths.
4. Wire cache directory config into live-provider request handling.
5. Add `techno-search live-cache-summary`.
6. Add docs for cache location, cleanup, and reproducibility limits.
7. Add Gaia mock query-shape builder with no network access by default.
8. Add IRSA mock query-shape builder with no network access by default.
9. Add VizieR/SIMBAD mock query-shape builders with conservative provenance fields.
10. Update `PROJECT_STATUS`, `ROADMAP`, and `CLAUDE.md`, then commit the batch.

## Live Cache/Query Shape Step 1 — Cache Policy Constants

Status: implemented.

Added:

- `LIVE_CACHE_DIR_ENV_VAR`
- `DEFAULT_LIVE_CACHE_DIR`
- `configured_live_cache_dir(...)`

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Cache/Query Shape Step 2 — Live Provider Cache Helper

Status: implemented.

Added:

- `LiveProviderCache.from_config(...)`
- deterministic metadata paths from request cache keys
- JSON metadata read/write helpers
- cache summary helper that counts metadata files by provider

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Cache/Query Shape Step 3 — Cache Path Tests

Status: implemented.

Added tests for:

- configured cache directory environment override
- default project-local `cache/live_providers` convention
- metadata writes under a cache root
- cache writes staying outside committed example report paths

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Cache/Query Shape Step 4 — Cache-Aware Provider Fetch

Status: implemented.

Added:

- optional `cache=` argument to provider `fetch_metadata(...)`
- cached normalized metadata reuse
- cache write after injected live fetches
- test coverage for one fetch call followed by cached reuse

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Cache/Query Shape Step 5 — Live Cache Summary CLI

Status: implemented.

Added:

- `techno-search live-cache-summary`
- optional `--cache-dir`
- cache existence, metadata count, and provider-count output
- CLI test coverage

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Live Cache/Query Shape Step 6 — Cache Documentation

Status: implemented.

Updated:

- live-provider cache location and environment override docs
- live-cache summary CLI docs
- data policy note that live-provider caches are ignored local artifacts
- cleanup and reproducibility limits

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Live Cache/Query Shape Step 7 — Gaia Query Shape Builder

Status: implemented.

Added:

- Gaia cone-search request builder
- ADQL-like query descriptor with catalog, coordinates, and radius metadata
- test proving request construction does not require live access

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Cache/Query Shape Step 8 — IRSA Query Shape Builder

Status: implemented.

Added:

- IRSA catalog cone-search request builder
- catalog, coordinates, radius, and purpose metadata
- test proving request construction stays non-networked by default

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Cache/Query Shape Step 9 — VizieR And SIMBAD Query Shape Builders

Status: implemented.

Added:

- VizieR catalog cone-search request builder
- SIMBAD object lookup request builder
- provenance-only interpretation markers in request parameters
- tests proving both remain guarded by default

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Cache/Query Shape Step 10 — Status And Roadmap Updates

Status: implemented.

Updated:

- `docs/PROJECT_STATUS.md` completed, in-progress, and next-action entries
- `docs/ROADMAP.md` reporting and live-data milestone status
- `docs/LIVE_PROVIDER_INTERFACES.md` query-shape builder guidance
- `CLAUDE.md` with final step handoff notes

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_cli.py tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Ten-Step Live Fixture/Client Skeleton Expansion

User requested ten iterative steps:

1. Add cached live-metadata fixture format under `tests/fixtures/live_metadata/`.
2. Add tests that load cached Gaia metadata fixtures without network access.
3. Add tests that load cached IRSA metadata fixtures without network access.
4. Add tests that load cached VizieR/SIMBAD metadata fixtures without network access.
5. Add `techno-search live-fixture-summary`.
6. Add docs for live metadata fixture rules and non-committed cache boundaries.
7. Add a provider-client protocol/interface so real clients can plug in cleanly later.
8. Add a disabled Gaia real-client skeleton behind `TECHNO_SEARCH_ENABLE_LIVE_DATA=1`.
9. Add a disabled IRSA real-client skeleton behind `TECHNO_SEARCH_ENABLE_LIVE_DATA=1`.
10. Update `PROJECT_STATUS`, `ROADMAP`, and `CLAUDE.md`, then commit the batch.

## Live Fixture/Client Step 1 — Cached Metadata Fixture Format

Status: implemented.

Added:

- `tests/fixtures/live_metadata/gaia_cone_search.metadata.json`
- `tests/fixtures/live_metadata/irsa_catalog_cone.metadata.json`
- `tests/fixtures/live_metadata/vizier_catalog_cone.metadata.json`
- `tests/fixtures/live_metadata/simbad_object_lookup.metadata.json`
- `live_metadata_fixture_v1` fixture schema marker

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Fixture/Client Step 2 — Gaia Fixture Loader Test

Status: implemented.

Added:

- `default_live_metadata_fixture_dir(...)`
- `load_live_metadata_fixture(...)`
- `iter_live_metadata_fixtures(...)`
- fixture shape validation
- Gaia fixture test that runs with live data disabled

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Fixture/Client Step 3 — IRSA Fixture Loader Test

Status: implemented.

Added:

- IRSA cached metadata fixture loader test
- assertions for provider name, catalog provenance, cache key, and response metadata
- live-data-disabled guard coverage

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Fixture/Client Step 4 — VizieR And SIMBAD Fixture Tests

Status: implemented.

Added:

- VizieR cached metadata fixture loader test
- SIMBAD cached metadata fixture loader test
- provenance-only interpretation assertions
- no candidate interpretation assertion for cached provider fixtures

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Fixture/Client Step 5 — Live Fixture Summary CLI

Status: implemented.

Added:

- `live_metadata_fixture_summary(...)`
- `techno-search live-fixture-summary`
- optional `--fixture-dir`
- CLI test for committed fixture coverage counts

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Fixture/Client Step 6 — Fixture Documentation

Status: implemented.

Updated:

- CLI docs for `live-fixture-summary`
- live-data integration fixture policy
- live-provider interface fixture allow/deny lists
- data policy note for tiny live metadata fixtures versus local cache contents

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Live Fixture/Client Step 7 — Provider Client Protocol

Status: implemented.

Added:

- `LiveProviderClient` protocol
- `fetcher_from_client(...)`
- `LiveProviderAdapter.from_client(...)`
- protocol adapter test with injected stub client

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Fixture/Client Step 8 — Disabled Gaia Client Skeleton

Status: implemented.

Added:

- `GaiaLiveClient`
- explicit live opt-in guard
- `NotImplementedError` after opt-in because no real network client exists yet
- tests for disabled and unimplemented Gaia skeleton behavior

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Fixture/Client Step 9 — Disabled IRSA Client Skeleton

Status: implemented.

Added:

- `IrsaLiveClient`
- explicit live opt-in guard
- `NotImplementedError` after opt-in because no real network client exists yet
- tests for disabled and unimplemented IRSA skeleton behavior

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Fixture/Client Step 10 — Status And Roadmap Updates

Status: implemented.

Updated:

- `docs/PROJECT_STATUS.md` completed, in-progress, and next-action entries
- `docs/ROADMAP.md` reporting and live-data milestone status
- `docs/LIVE_PROVIDER_INTERFACES.md` provider-client protocol and skeleton guidance
- `CLAUDE.md` with final step handoff notes

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_cli.py tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Ten-Step Live Client Completion Expansion

User requested ten iterative steps:

1. Add cached fixture-driven normalization tests for Gaia and IRSA client skeleton paths.
2. Add cached fixture-driven normalization tests for VizieR and SIMBAD paths.
3. Add `VizierLiveClient` disabled skeleton behind `TECHNO_SEARCH_ENABLE_LIVE_DATA=1`.
4. Add `SimbadLiveClient` disabled skeleton behind `TECHNO_SEARCH_ENABLE_LIVE_DATA=1`.
5. Add `BreakthroughListenLiveClient` disabled skeleton and a tiny metadata fixture.
6. Add Breakthrough Listen request-shape builder for local file metadata, no file ingestion yet.
7. Add `techno-search live-client-summary` for configured skeleton/client status.
8. Add docs for the live-client lifecycle.
9. Update `PROJECT_STATUS`, `ROADMAP`, and `CLAUDE.md`.
10. Run full validation, commit, and report branch state.

## Live Client Completion Step 1 — Gaia/IRSA Fixture Normalization Tests

Status: implemented.

Added:

- fixture-backed client stub for adapter normalization tests
- Gaia fixture-client normalization test
- IRSA fixture-client normalization test
- live opt-in scoped only to the tests

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Client Completion Step 2 — VizieR/SIMBAD Fixture Normalization Tests

Status: implemented.

Added:

- VizieR fixture-client normalization test
- SIMBAD fixture-client normalization test
- provenance-only query parameter assertions on normalized request metadata

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Client Completion Step 3 — Disabled VizieR Client Skeleton

Status: implemented.

Added:

- `VizierLiveClient`
- explicit live opt-in guard
- `NotImplementedError` after opt-in because no real network client exists yet
- tests for disabled and unimplemented VizieR skeleton behavior

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Client Completion Step 4 — Disabled SIMBAD Client Skeleton

Status: implemented.

Added:

- `SimbadLiveClient`
- explicit live opt-in guard
- `NotImplementedError` after opt-in because no real network client exists yet
- tests for disabled and unimplemented SIMBAD skeleton behavior

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Client Completion Step 5 — Breakthrough Listen Fixture And Skeleton

Status: implemented.

Added:

- `tests/fixtures/live_metadata/breakthrough_listen_file_metadata.metadata.json`
- `BreakthroughListenLiveClient`
- fixture loader test for Breakthrough Listen metadata
- tests for disabled and unimplemented Breakthrough Listen skeleton behavior
- updated fixture-summary expected count

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Live Client Completion Step 6 — Breakthrough Listen File Request Shape

Status: implemented.

Added:

- `BreakthroughListenAdapter.build_local_file_metadata_request(...)`
- provenance-only local file metadata descriptor
- test proving request construction does not read or require the file

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Client Completion Step 7 — Live Client Summary CLI

Status: implemented.

Added:

- `live_client_summary(...)`
- `techno-search live-client-summary`
- client status fields for provider, service URL, implementation state, and live opt-in
- CLI test proving all configured clients are disabled skeletons

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_live_data.py
```

Merge status: already on `main`; no merge needed.

---

## Live Client Completion Step 8 — Live Client Lifecycle Docs

Status: implemented.

Updated:

- CLI docs for `live-client-summary`
- provider interface docs with all disabled skeletons
- live-client lifecycle: query shape, fixture, skeleton, normalization tests, real client
- live-data integration docs for the guarded lifecycle

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_docs.py tests/test_cli.py
```

Merge status: already on `main`; no merge needed.

---

## Live Client Completion Step 9 — Status And Roadmap Updates

Status: implemented.

Updated:

- `docs/PROJECT_STATUS.md` completed, in-progress, and next-action entries
- `docs/ROADMAP.md` reporting and live-data milestone status
- `CLAUDE.md` with step 9 handoff notes

Validation for this step should include:

```bash
.venv/bin/python -m pytest tests/test_live_data.py tests/test_cli.py tests/test_docs.py
```

Merge status: already on `main`; no merge needed.

---

## Live Client Completion Step 10 — Validation And Commit

Status: implemented.

Validation passed:

- full pytest with coverage
- full Ruff check
- `git diff --check`

Commit planned:

```bash
git commit -m "Add live client skeleton completion"
```

Merge status: already on `main`; no merge needed.

---

## Milestone 10 Scaffolding, Weekly Review, Target Watchlist, And SQLite Migration

User requested applying all system directives and completing the next fifteen steps.

Status: implemented in this iteration.

Added:

- `src/techno_search/weekly_review.py` — weekly review template assembler combining SQLite digest + cross-track summary; confirms network access and external submission are zero
- `schemas/weekly_review_template.schema.json` — JSON Schema for the weekly review template output
- `tests/test_weekly_review.py` — 12 tests for weekly review template structure, gates, markdown sections, and CLI
- `schemas/target_watchlist.schema.json` — JSON Schema for target watchlist scheduling aid entries
- `tests/fixtures/target_watchlist.json` — 4 synthetic entries (elevated, deprioritized, blocked, completed)
- `src/techno_search/target_watchlist.py` — watchlist loader, summary helper, and conflict detection
- `tests/test_target_watchlist.py` — tests for watchlist counts, conflict detection, disclaimer, and CLI output
- `src/techno_search/baseline_model.py` — interpretable rule-based baseline classifier mirroring scoring pathway logic
- `src/techno_search/baseline_eval.py` — baseline evaluation harness against calibration fixtures and example candidates
- `tests/test_baseline_model.py` — 14 tests covering all pathway routes, rule trace, disclaimer, and accuracy gate
- `tests/test_sqlite_migration.py` — 12 tests for SQLite log v1→v2 migration (additive column, idempotent, guard, CLI)
- SQLite log migration: `TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION = "top_level_sqlite_logs_v2"`, `apply_sqlite_log_migration()`, `SUPPORTED_SQLITE_LOG_MIGRATIONS` with v1→v2 and noop entries
- CLI commands: `baseline-eval-summary`, `target-watchlist-summary`, `weekly-review-template`, `sqlite-log-migrate --apply`
- `validate-all` gates: baseline pathway accuracy >= 0.80, baseline total cases >= 3, watchlist entry count >= 4, conflict count == 0
- `validation-summary` fields: `baseline_pathway_accuracy`, `baseline_false_positive_recall`, `baseline_total_cases`, `target_watchlist_entry_count`, `target_watchlist_elevated_count`, `target_watchlist_conflict_count`
- `docs/DECISIONS.md` DECISION-028: Interpretable Baseline Must Precede Any Learned Model
- `docs/CLI_USAGE.md`, `docs/VALIDATION.md`, `docs/ROADMAP.md`, `docs/PROJECT_STATUS.md` updated
- Schema count now 24 (added `target_watchlist`, `weekly_review_template`)

Scientific guardrail:

- Baseline outputs carry an explicit disclaimer that they are not detections, discoveries, confirmations, or external validation
- Target watchlist entries are scheduling metadata only — they never modify candidate posteriors or pathway routing
- Weekly review template is a local operator review artifact confirming network access and submission remain disabled
- SQLite migration is guarded and additive only — unknown schema versions return an error, no destructive migration is allowed

Validation passed:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src
git diff --check
.venv/bin/techno-search validate-all
```

Result:

- 331 tests passed
- 5 tests skipped
- total coverage: 93%
- Ruff passed
- mypy passed
- diff whitespace check passed
- `validate-all` ok=True

Merge status: committed on `claude/general-session-Bb2dZ`, pushed, PR created, merged to `main`.
