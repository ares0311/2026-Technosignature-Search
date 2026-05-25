# ROADMAP

## Project
Technosignature Search

## Strategy

Build a multi-modal technosignature candidate search platform.

Do not start with live large-scale data. Start with the shared scoring and pathway core using synthetic data, then build track-specific ingestion and search modules.

---

# Milestone 1 — Multi-Modal Scoring Core

## Goal

Create shared candidate scoring logic across radio, infrared, and archival anomaly tracks.

## Tasks

- [x] Define typed candidate schemas
- [x] Define shared posterior-style score outputs
- [x] Define track-specific evidence fields
- [x] Implement scoring model v0
- [x] Implement pathway classifier
- [x] Add synthetic unit tests
- [x] Add scientific sanity tests

## Output

```text
candidate features → scoring engine → pathway recommendation
```

## Done When

- Clean synthetic radio candidate scores better than obvious RFI
- Clean synthetic infrared excess scores better than AGN/blended source
- Clean synthetic archival anomaly scores better than known artifact
- All tests pass

---

# Milestone 2 — Radio SETI Prototype

## Goal

Build the first radio candidate workflow.

## Tasks

- [x] Add radio candidate schema
- [x] Add support for parsing candidate-hit tables
- [x] Add RFI-band overlap checks
- [x] Add ON/OFF cadence checks
- [x] Add initial radio search config
- [x] Add waterfall plot placeholder/report interface
- [x] Add synthetic radio injection tests

## Output

```text
radio hit table → RFI vetting → score → report
```

---

# Milestone 3 — Infrared Waste-Heat Prototype

## Goal

Build the first catalog-based infrared anomaly workflow.

## Tasks

- [x] Add infrared candidate schema
- [x] Add Gaia/WISE/2MASS feature schema
- [x] Add SED/IR-excess feature logic
- [x] Add source-confusion flags
- [x] Add galaxy/AGN/dust/YSO rejection flags
- [x] Add initial infrared search config
- [x] Add synthetic infrared tests

## Output

```text
catalog features → IR excess checks → score → report
```

---

# Milestone 4 — Archival / Catalog Anomaly Prototype

## Goal

Build the first vanishing/appearing source and catalog anomaly workflow.

## Tasks

- [x] Add anomaly candidate schema
- [x] Add cross-match confidence features
- [x] Add proper-motion sanity checks
- [x] Add survey-depth mismatch checks
- [x] Add artifact flags
- [x] Add initial archival anomaly search config
- [x] Add synthetic anomaly tests

## Output

```text
cross-match features → artifact checks → score → report
```

---

# Milestone 5 — Reporting System

## Goal

Generate reproducible candidate reports.

## Tasks

- [x] Markdown report generation
- [x] JSON candidate packet
- [x] Plots where available
- [x] Positive evidence list
- [x] Negative evidence list
- [x] Blocking issues list
- [x] Provenance block
- [x] Persistence manifest
- [x] Candidate/report validation commands
- [x] JSON schema artifacts
- [x] Golden example regression checks
- [x] Example regeneration CLI
- [x] Schema versioning policy
- [x] Provenance summaries in report manifests
- [x] Provider service URL and cache-key provenance fields
- [x] Live-provider cache summary command
- [x] Live-metadata fixture summary command
- [x] Live-client summary command
- [x] Catalog-cache policy command
- [x] Catalog-cache validator command
- [x] Catalog-cache summary command
- [x] Validation summary command
- [x] Dependency-free synthetic SVG plot artifacts

## Done When

Each candidate can generate a review packet without claiming confirmation.

---

# Milestone 6 — Injection-Recovery

## Goal

Measure sensitivity and reliability.

## Tasks

- [x] Radio synthetic signal injection
- [x] Infrared synthetic excess injection
- [x] Archival anomaly simulation
- [x] Synthetic injection-recovery summary fixtures
- [x] Synthetic reliability curve fixtures
- [x] Recovery curves
- [x] Synthetic false-alarm estimates

---

# Milestone 7 — Human Review Workflow

## Goal

Support citizen-science review.

## Tasks

- [x] Candidate triage labels
- [x] Review queue format
- [x] Exportable review packets
- [x] Reviewer notes
- [x] Consensus labels

---

# Milestone 8 — Live Data Integrations

## Goal

Add real data ingestion behind tested abstractions.

## Tasks

- [x] Breakthrough Listen style file ingestion
- [x] Gaia/IRSA/VizieR query wrappers
- [x] Catalog caching
- [x] Provenance tracking scaffold
- [x] Live integration tests marked separately
- [x] Opt-in live-data scaffold
- [x] Provider adapter interfaces behind opt-in guard
- [x] Provider adapters behind mocks
- [x] Deterministic provider request cache keys
- [x] Live provider summary CLI
- [x] Live provider metadata cache helper
- [x] Live provider cache summary CLI
- [x] Non-networked Gaia/IRSA/VizieR/SIMBAD query-shape builders
- [x] Cached live metadata fixtures
- [x] Provider client protocol
- [x] Disabled Gaia and IRSA live-client skeletons
- [x] Fixture-driven live-client normalization tests
- [x] Disabled VizieR, SIMBAD, and Breakthrough Listen live-client skeletons
- [x] Breakthrough Listen local file metadata request shape
- [x] Catalog cache metadata policy
- [x] Catalog cache commit-path validator
- [x] Catalog cache metadata storage helper
- [x] Provider response normalization contract
- [x] Guarded Gaia live client with mocked transport tests
- [x] Guarded IRSA live client with mocked transport tests
- [x] Guarded VizieR live client with mocked transport tests
- [x] Guarded SIMBAD live client with mocked transport tests
- [x] Breakthrough Listen local-file metadata client
- [x] Live client capability summary fields
- [x] Remaining real provider client implementations
- [x] Catalog cache storage implementation
- [x] Provider normalization regression fixtures
- [x] Provider normalization summary in local validation
- [x] Fixture-backed background target-priority summary
- [x] Passive/background search ledger summary
- [x] Versioned background target-priority config
- [x] Explicit local-only passive runner ledger append command
- [x] Reviewed background workflow ledger semantics and summary command
- [x] Candidate-extraction handoff contract and summary command
- [x] Reviewed and needs-follow-up outcome logs for background runs
- [x] Review-history adjusted target selection for external scheduler use
- [x] Deterministic local follow-up test results for needs-follow-up records
- [x] Report-readiness gates with top-three conservative recommendations
- [x] Conservative draft follow-up report summaries
- [x] Explicit user decision records before external submission
- [x] External scheduler templates for cron and launchd
- [x] Persisted draft report Markdown writer and validation
- [x] User decision append helper with explicit approval guard
- [x] Scheduler dry-run smoke path for temporary artifact directories
- [x] Top-level SQLite operational logs for bounded background runs
- [x] SQLite log initialization, summary, validation, and CLI wiring
- [x] SQLite integrity, migration, recent-run, needs-follow-up, export, and commit-guard commands
- [x] SQLite PRAGMA diagnostics, ignored backups, retention summaries, and vacuum maintenance commands
- [x] SQLite log non-destructive migration plan command
- [x] SQLite log review-safe weekly digest command
- [x] Persisted draft-report example artifacts under `examples/background_draft_reports`
- [x] Local artifacts cleanup CLI with dry-run default and committed-path safety
- [x] Cross-track candidate cross-reference fixture and summary command
- [x] Persisted-report reproducibility verification command

---

# Milestone 9 — Calibration

## Goal

Make scores empirically meaningful.

## Tasks

- [x] Build validation dataset manifests
- [x] Curated validation readiness records
- [x] Synthetic false-positive fixture set
- [x] Score regression snapshots
- [x] False-positive class summary tooling
- [x] Local validation summary command
- [x] Provenance summary command
- [x] Synthetic injection-recovery summary command
- [x] Reliability curves
- [x] Precision-recall analysis
- [x] False-positive class analysis
- [x] Calibration by track
- [x] Local benchmark metadata
- [x] Synthetic benchmark run-result metadata
- [x] Append-only benchmark run-result workflow
- [x] Repeated-run benchmark comparison workflow

---

# Milestone 10 — Advanced AI Research Track

## Goal

Evaluate modern AI methods only after interpretable baselines, provenance, false-positive handling, and calibration datasets exist.

## Milestone 10 Scaffold (In Progress)

- [x] Interpretable rule-based baseline classifier (`baseline_model.py`) mirroring scoring pathway logic
- [x] Baseline evaluation harness against calibration false-positive and clean example candidate fixtures
- [x] `baseline-eval-summary` CLI command with pathway accuracy, false-positive recall, candidate precision
- [x] `validate-all` gate: pathway accuracy >= 0.80
- [x] Target watchlist scheduling aid with elevated/deprioritized/blocked/completed kinds
- [x] `target-watchlist-summary` CLI command with conflict detection
- [x] Weekly review template assembling SQLite digest + cross-track summary
- [x] `weekly-review-template` CLI command
- [x] SQLite log migration (v1 → v2 adding `target_notes` column)
- [x] DECISION-028: Interpretable Baseline Must Precede Any Learned Model
- [x] Per-track accuracy breakdown and rule fire-rate reporting in baseline eval
- [x] Misclassification log with candidate_id, expected/predicted pathway, and rule trace
- [x] Baseline performance history fixture and `baseline-performance-history-summary` CLI
- [x] Synthetic injection grid tests for radio SNR×drift and infrared excess routing
- [x] `baseline-pathway-drift-summary` CLI with zero-drift gate in `validate-all`
- [x] Watchlist priority ordering by `priority_override_score`
- [x] Weekly review template watchlist gate (elevated, blocked, prioritized targets)
- [x] `sqlite-log-track-summary` CLI for per-track run counts from local SQLite database
- [x] `health` CLI for concise operator status dashboard
- [x] Baseline eval and performance history JSON schema artifacts
- [x] DECISION-029: Weekly Review Template Is The Authoritative Operator Handoff
- [x] Baseline confusion matrix (per-pathway precision/recall/F1) in `evaluate_baseline()`
- [x] `baseline-confusion-matrix-summary` CLI
- [x] `score-determinism-check` CLI (gate: all example candidates deterministic)
- [x] Candidate lifecycle schema, fixture, loader, and `candidate-lifecycle-summary` CLI
- [x] Observation schedule schema, fixture, loader, and `observation-schedule-summary` CLI
- [x] False-negative summary from injection-recovery fixture and `false-negative-summary` CLI
- [x] DECISION-030: Scoring Must Be Deterministic Before Any Learned Model Is Introduced
- [x] Scoring config summary (`scoring-config-summary`) with threshold count and v0 parameter report
- [x] Route coverage summary (`route-coverage-summary`) checking Pathway enum fixture coverage
- [x] Lifecycle transition validator (`lifecycle-transition-summary`) checking stage ordering
- [x] Observation efficiency summary (`observation-efficiency-summary`) with completion/cancellation rates
- [x] DECISION-031: Scoring Config And Route Coverage Are Required Local Validation Gates
- [x] Route coverage extended: 5/6 Pathway values now covered by calibration fixtures
- [x] Per-track sensitivity config summary (`sensitivity-config-summary`) with weight audit
- [x] Candidate triage notes schema, fixture, loader, and `triage-summary` CLI
- [x] DECISION-032: Candidate Triage And Sensitivity Config Are Validated Scheduling Aids

## Guardrails

- Learned models must not replace provenance, negative evidence, blocking issues, or pathway logic.
- Black-box scores must be calibrated against synthetic injections, known contaminants, known artifacts, and human-reviewed labels.
- AI outputs should be treated as decision-support signals, not discovery claims.
- Model versions, training data, features, prompts where applicable, and evaluation metrics must be recorded.

---

# Milestone 11 — ML Feature Engineering

## Goal

Build a stable, versioned feature extraction layer that transforms scored candidates into ML-ready numeric representations before any learned model is introduced.

## Tasks

- [x] Flat feature vector extraction from scored candidates (`candidate_feature_vector.py`)
- [x] Feature vector schema and JSON schema artifact
- [x] Synthetic feature vector fixtures covering radio, infrared, and anomaly tracks
- [x] `feature-vector-summary` CLI command
- [x] `validate-all` gate: feature vector count >= 5, covering all three tracks
- [x] Feature normalization and scaling scaffold (min-max per track, stored with vector)
- [x] Track-specific feature set definitions derived from existing scoring config weights
- [x] Feature importance mapping from baseline rule fire rates to feature names
- [x] Feature drift detection: flag vectors where normalization bounds shift across extractor versions
- [x] DECISION-042: Feature Vector Layer Must Be Stable Before Any Learned Model Is Trained

---

# Milestone 12 — ML Model Registry And Development

## Goal

Introduce pluggable learned models with mandatory version tracking, provenance, and comparison against the interpretable baseline — so no learned model is used unless it demonstrably improves on the baseline.

## Tasks

- [x] ML model registry schema and JSON schema artifact (`ml_model_registry.py`)
- [x] Synthetic model registry fixtures covering experimental, validated, and deprecated entries
- [x] `model-registry-summary` CLI command
- [x] ML pipeline diagnostics module comparing baseline vs registered learned model metrics (`ml_pipeline_diagnostics.py`)
- [x] `ml-diagnostics-summary` CLI command with above-baseline gate
- [x] `validate-all` gate: no registered model below baseline pathway accuracy
- [x] CNN scaffold for radio waterfall morphology (architecture definition, no weights yet)
- [x] Transformer scaffold for sequential multi-epoch radio features (architecture definition, no weights yet)
- [x] Hybrid model interface combining baseline rule scores with learned feature embeddings
- [x] Self-supervised representation learning scaffold for unlabeled candidate clusters
- [x] Foundation-model embedding adapter for retrieval and human-review triage support
- [x] Training data scaffold assembled from calibration fixtures and injection-recovery cases
- [x] Model evaluation harness comparing learned model accuracy, precision, and recall to baseline
- [x] Model performance history appended to the existing benchmark run-result workflow
- [x] DECISION-043: Feature Normalization, Feature Importance, And ML Training Data Are Required ML Infrastructure
- [x] DECISION-044: ML Model Architecture Scaffolds, Evaluation Harness, And Performance History Are Required Before Any Model Deployment

---

# Milestone 13 — Candidate Methods Production Readiness

## Goal

Harden the candidate scoring, routing, and reporting pipeline for a first curated non-synthetic validation dataset, introduce model-serving scaffolds, and complete the operator handoff documentation required before any external submission is considered.

## Tasks

- [x] Model serving scaffold: versioned inference interface wrapping a registered model or baseline
- [x] Model inference provenance: record which model version scored each candidate packet
- [x] Candidate re-scoring workflow: re-score candidates when a new validated model is registered
- [x] Scoring audit log: append-only record of each score event per candidate per model version
- [x] Curated validation dataset intake checklist schema
- [x] First curated non-synthetic dataset intake fixture (placeholder, conservative)
- [x] `validate-all` gate: at least one curated dataset entry present
- [x] Updated operator handoff template including model version and inference provenance fields
- [x] Candidate methods summary CLI: aggregate view of scoring, routing, and model provenance
- [x] DECISION-045: Model Serving, Scoring Audit Log, And Curated Dataset Intake Are Required Candidate Methods Production Prerequisites
- [x] DECISION-046: Candidate Re-Scoring, Operator Handoff Templates, And Candidate Methods Summary Complete Milestone 13

---

# Project-Level Decision Tree

```text
IF known object or known artifact:
    → known_object_annotation

ELIF strong candidate evidence AND low false-positive evidence:
    → candidate_review_packet

ELIF interesting but ambiguous:
    → human_review_queue

ELIF likely false positive:
    → do_not_submit_false_positive

ELSE:
    → github_reproducibility_only
```

---

# Development Principle

Build the candidate evaluation engine first. Add large data ingestion only after the scoring, testing, and reporting interfaces are stable.

---

# Milestone 14 — Pipeline Integration & End-to-End Validation

## Goal

Connect the candidate scoring, model serving, audit logging, and operator handoff pipeline into a validated end-to-end flow. Introduce pipeline configuration management, integration smoke tests, and external submission readiness checks.

## Tasks

- [x] Unified pipeline configuration module tying scoring config, model serving, and track configs
- [x] Pipeline configuration schema and JSON schema artifact
- [x] `pipeline-config-summary` CLI command
- [x] End-to-end pipeline smoke test: candidate → scoring → serving → audit → handoff
- [x] Submission readiness checker: gate ensuring all required provenance fields are present before any external handoff is considered
- [x] `submission-readiness-summary` CLI command
- [x] Pipeline integration tests covering multi-step candidate flow
- [x] DECISION-047: Pipeline Config, Submission Readiness, And Pipeline Integration Complete Milestone 14

## Done When

- A single candidate can flow through scoring, model serving, audit logging, and operator handoff with full provenance recorded
- Submission readiness check blocks any pathway missing required provenance
- All integration tests pass without network access

---

# Milestone 15 — Candidate Comparison, Pipeline Telemetry, And Provenance Audit

## Goal

Close the pipeline loop with three complementary operational modules: multi-candidate comparison for scheduling queue prioritisation, per-stage telemetry for operational provenance, and end-to-end provenance audit for cross-module consistency validation.

## Tasks

- [x] Candidate comparison module: local scheduling aid ranking candidates by score
- [x] `candidate_comparison.schema.json` and fixture
- [x] `candidate-comparison-summary` CLI command
- [x] Pipeline telemetry module: per-stage latency and success provenance records
- [x] `pipeline_telemetry.schema.json` and fixture
- [x] `pipeline-telemetry-summary` CLI command
- [x] Provenance audit module: cross-module consistency verdicts per candidate
- [x] `provenance_audit.schema.json` and fixture
- [x] `provenance-audit-summary` CLI command
- [x] `validate-all` gates: comparison_count >= 1, telemetry_entry_count >= 1, provenance_audit_entry_count >= 1
- [x] `validation-summary` fields: comparison_record_count, telemetry_entry_count, provenance_audit_entry_count, provenance_audit_consistent_count
- [x] DECISION-048: Candidate Comparison, Pipeline Telemetry, And Provenance Audit Complete Milestone 15

## Done When

- Multi-candidate comparisons are recorded as scheduling aids without modifying scores
- All pipeline stages have telemetry coverage in fixtures
- Provenance audit verdicts cover consistent, inconsistent, partial, and not_applicable cases
- All integration tests pass without network access

---

# Milestone 16 — Candidate Alert Log, Pipeline Replay Log, And Scoring Threshold Audit

**Status**: complete

## Tasks

- [x] `src/techno_search/candidate_alert_log.py` — operational alert records for threshold crossings, pathway changes, and escalations
- [x] `schemas/candidate_alert_log.schema.json`
- [x] `tests/fixtures/candidate_alert_log.json` — 5 entries (2 resolved, 3 open; info×2, warning×2, critical×1)
- [x] `tests/test_candidate_alert_log.py` — 21 tests
- [x] `src/techno_search/pipeline_replay_log.py` — append-only reproducibility replay records
- [x] `schemas/pipeline_replay_log.schema.json`
- [x] `tests/fixtures/pipeline_replay_log.json` — 4 entries (2 score_matched, 1 score_diverged, 1 config_mismatch)
- [x] `tests/test_pipeline_replay_log.py` — 20 tests
- [x] `src/techno_search/scoring_threshold_audit.py` — threshold consistency provenance checks
- [x] `schemas/scoring_threshold_audit.schema.json`
- [x] `tests/fixtures/scoring_threshold_audit.json` — 5 entries (3 pass, 1 warning, 1 not_checked)
- [x] `tests/test_scoring_threshold_audit.py` — 21 tests
- [x] CLI: `candidate-alert-summary`, `pipeline-replay-summary`, `scoring-threshold-audit-summary`
- [x] `validate-all` gates: alert_entry_count >= 1, replay_entry_count >= 1, threshold_pass_count >= 1
- [x] `validation-summary` fields: candidate_alert_entry_count, candidate_alert_open_count, pipeline_replay_entry_count, pipeline_replay_matched_count, scoring_threshold_pass_count, scoring_threshold_fail_count
- [x] DECISION-049: Candidate Alert Log, Pipeline Replay Log, And Scoring Threshold Audit Complete Milestone 16

## Done When

- Alert log covers all severity levels with resolved and open entries
- Replay log covers matched, diverged, and mismatch outcomes
- Threshold audit covers pass, warning, and not_checked verdicts across all three tracks
- All integration tests pass without network access

---

# Milestone 17 — Alert Resolution Log, Config Version History, And Operator Escalation Log

**Status**: complete

## Tasks

- [x] `src/techno_search/alert_resolution_log.py` — provenance records for formally closing open alerts
- [x] `schemas/alert_resolution_log.schema.json`
- [x] `tests/fixtures/alert_resolution_log.json` — 5 entries (4 resolved, 1 open)
- [x] `tests/test_alert_resolution_log.py` — 22 tests
- [x] `src/techno_search/config_version_history.py` — append-only config change log
- [x] `schemas/config_version_history.schema.json`
- [x] `tests/fixtures/config_version_history.json` — 4 entries (created×2, promoted×1, deprecated×1)
- [x] `tests/test_config_version_history.py` — 22 tests
- [x] `src/techno_search/operator_escalation_log.py` — inter-operator escalation records
- [x] `schemas/operator_escalation_log.schema.json`
- [x] `tests/fixtures/operator_escalation_log.json` — 4 entries (critical open, urgent acknowledged, routine resolved, critical resolved)
- [x] `tests/test_operator_escalation_log.py` — 24 tests
- [x] CLI: `alert-resolution-summary`, `config-version-history-summary`, `operator-escalation-summary`
- [x] `validate-all` gates: alert_resolution_entry_count >= 1, config_history_entry_count >= 1, operator_escalation_entry_count >= 1
- [x] `validation-summary` fields: alert_resolution_entry_count, alert_resolution_open_count, config_history_entry_count, operator_escalation_entry_count, operator_escalation_open_count
- [x] DECISION-064: Alert Resolution Log, Config Version History, And Operator Escalation Log Complete Milestone 17

## Done When

- Alert resolution log covers all resolution statuses and kinds
- Config version history covers created, promoted, and deprecated change kinds
- Operator escalation log covers open, acknowledged, and resolved states with all severity levels
- All integration tests pass without network access

---

# Milestone 18 — Candidate Deduplication Log, Intake Queue Log, And Workflow State Log

**Status**: complete

## Tasks

- [x] `src/techno_search/candidate_deduplication_log.py` — provenance records for pairwise candidate deduplication comparisons
- [x] `schemas/candidate_deduplication_log.schema.json`
- [x] `tests/fixtures/candidate_deduplication_log.json` — 5 entries (2 confirmed_distinct, 1 confirmed_duplicate, 1 inconclusive, 1 pending)
- [x] `tests/test_candidate_deduplication_log.py` — 22 tests
- [x] `src/techno_search/intake_queue_log.py` — local planning placeholders for data source intake queue tracking
- [x] `schemas/intake_queue_log.schema.json`
- [x] `tests/fixtures/intake_queue_log.json` — 5 entries (2 blocked, 1 queued, 1 intake_ready, 1 cancelled)
- [x] `tests/test_intake_queue_log.py` — 22 tests
- [x] `src/techno_search/workflow_state_log.py` — local scheduling coordination records for review assignment state transitions
- [x] `schemas/workflow_state_log.schema.json`
- [x] `tests/fixtures/workflow_state_log.json` — 5 entries (2 initial_assign, 2 state_change, 1 close)
- [x] `tests/test_workflow_state_log.py` — 22 tests
- [x] CLI: `candidate-deduplication-summary`, `intake-queue-summary`, `workflow-state-summary`
- [x] `validate-all` gates: dedup_entry_count >= 1, intake_entry_count >= 1, workflow_entry_count >= 1
- [x] `validation-summary` fields: candidate_deduplication_entry_count, candidate_deduplication_pending_count, intake_queue_entry_count, intake_queue_blocked_count, workflow_state_entry_count
- [x] DECISION-065: Candidate Deduplication Log, Intake Queue Log, And Workflow State Log Complete Milestone 18

## Done When

- Deduplication log covers all match kinds and statuses including pending with null match_score
- Intake queue log covers all intake statuses and source kinds with blocking_reason for blocked entries
- Workflow state log covers initial_assign (null from_state), state changes, and closure transitions
- All integration tests pass without network access

---

# Milestone 19 — Data Gap Log, Candidate Match Log, And Pipeline Error Log

## Goal

Add three operational provenance modules: scheduling gap records, cross-catalog matching outcomes, and pipeline error tracking.

## Tasks

- [x] `src/techno_search/data_gap_log.py` — DataGapEntry, load_data_gap_entries, data_gap_summary; statuses: identified, under_investigation, resolved, accepted
- [x] `schemas/data_gap_log.schema.json`
- [x] `tests/fixtures/data_gap_log.json` — 5 entries (2 identified, 1 under_investigation, 1 resolved, 1 accepted)
- [x] `tests/test_data_gap_log.py` — 22 tests
- [x] `src/techno_search/candidate_match_log.py` — CandidateMatchEntry, load_match_entries, candidate_match_summary; sources: simbad, gaia, vizier, irsa, internal_catalog
- [x] `schemas/candidate_match_log.schema.json`
- [x] `tests/fixtures/candidate_match_log.json` — 5 entries (2 matched, 1 no_match, 1 ambiguous, 1 pending)
- [x] `tests/test_candidate_match_log.py` — 22 tests
- [x] `src/techno_search/pipeline_error_log.py` — PipelineErrorEntry, load_error_entries, pipeline_error_summary; kinds: scoring_failure, data_missing, config_mismatch, timeout, validation_error
- [x] `schemas/pipeline_error_log.schema.json`
- [x] `tests/fixtures/pipeline_error_log.json` — 5 entries (1 critical/unresolved, 2 error/mixed, 2 warning/resolved)
- [x] `tests/test_pipeline_error_log.py` — 22 tests
- [x] `data_gap_log`, `candidate_match_log`, `pipeline_error_log` added to `SCHEMA_FILENAMES` (total schemas: 91)
- [x] CLI: `data-gap-summary`, `candidate-match-summary`, `pipeline-error-summary`
- [x] `validate-all` gates: data_gap_entry_count >= 1, candidate_match_entry_count >= 1, pipeline_error_entry_count >= 1
- [x] `validation-summary` fields: data_gap_entry_count, data_gap_unresolved_count, candidate_match_entry_count, candidate_match_matched_count, pipeline_error_entry_count, pipeline_error_unresolved_count
- [x] DECISION-066: Data Gap Log, Candidate Match Log, And Pipeline Error Log Complete Milestone 19

## Done When

- Data gap log covers all missing reasons and statuses with resolved_utc for resolved/accepted entries
- Candidate match log covers all match sources and statuses with angular_separation_arcsec for matched entries
- Pipeline error log covers all error kinds and severities with resolved bool and resolved_utc for resolved entries
- All integration tests pass without network access

---

# Milestone 20 — Observation Request Log, Candidate Export Log, And Quality Gate Log

## Goal

Add three operational provenance modules: follow-up observation scheduling requests, candidate data export events, and pipeline quality gate checks.

## Tasks

- [x] `src/techno_search/observation_request_log.py` — ObservationRequestEntry, load_observation_request_entries, observation_request_summary; kinds: target_followup, reobservation, calibration_check, verification, archival_search
- [x] `schemas/observation_request_log.schema.json`
- [x] `tests/fixtures/observation_request_log.json` — 5 entries (1 submitted, 1 acknowledged, 1 completed, 1 rejected, 1 scheduled)
- [x] `tests/test_observation_request_log.py` — 22 tests
- [x] `src/techno_search/candidate_export_log.py` — CandidateExportEntry, load_export_entries, candidate_export_summary; formats: json, csv, markdown, fits_stub, parquet_stub
- [x] `schemas/candidate_export_log.schema.json`
- [x] `tests/fixtures/candidate_export_log.json` — 5 entries (2 exported, 1 delivered, 1 prepared, 1 failed)
- [x] `tests/test_candidate_export_log.py` — 22 tests
- [x] `src/techno_search/quality_gate_log.py` — QualityGateEntry, load_quality_gate_entries, quality_gate_summary; kinds: score_threshold, provenance_completeness, rfi_screen, catalog_check, review_coverage
- [x] `schemas/quality_gate_log.schema.json`
- [x] `tests/fixtures/quality_gate_log.json` — 5 entries (2 pass, 1 fail, 1 warn, 1 not_applicable)
- [x] `tests/test_quality_gate_log.py` — 26 tests
- [x] `observation_request_log`, `candidate_export_log`, `quality_gate_log` added to `SCHEMA_FILENAMES` (total schemas: 94)
- [x] CLI: `observation-request-summary`, `candidate-export-summary`, `quality-gate-summary`
- [x] `validate-all` gates: obs_request_entry_count >= 1, candidate_export_entry_count >= 1, quality_gate_entry_count >= 1, quality_gate_pass_count >= 1
- [x] `validation-summary` fields: observation_request_entry_count, observation_request_pending_count, candidate_export_entry_count, candidate_export_delivered_count, quality_gate_entry_count, quality_gate_pass_count
- [x] DECISION-067: Observation Request Log, Candidate Export Log, And Quality Gate Log Complete Milestone 20

## Done When

- Observation request log covers all request kinds and statuses with target_utc for scheduled/completed entries
- Candidate export log covers all export formats and statuses with destination for delivered entries
- Quality gate log covers all gate kinds and results with score_at_check for applicable entries
- All integration tests pass without network access

---

# Milestone 21 — Instrument Log, Archival Query Log, And Candidate Linkage Log

## Goal

Add three operational provenance modules: instrument/telescope status events, archival/catalog query provenance, and candidate-to-candidate linkage records.

## Tasks

- [x] `src/techno_search/instrument_log.py` — InstrumentLogEntry, load_instrument_log_entries, instrument_log_summary; instrument kinds: radio_telescope, optical_telescope, archive_node, data_pipeline
- [x] `schemas/instrument_log.schema.json`
- [x] `tests/fixtures/instrument_log.json` — 5 entries (1 online, 1 offline, 1 degraded, 1 maintenance, 1 calibrating)
- [x] `tests/test_instrument_log.py` — 22 tests
- [x] `src/techno_search/archival_query_log.py` — ArchivalQueryEntry, load_archival_query_entries, archival_query_summary; query kinds: cone_search, identifier_lookup, time_series, spectral_query, image_retrieval
- [x] `schemas/archival_query_log.schema.json`
- [x] `tests/fixtures/archival_query_log.json` — 5 entries (2 completed, 1 submitted, 1 failed, 1 cached)
- [x] `tests/test_archival_query_log.py` — 22 tests
- [x] `src/techno_search/candidate_linkage_log.py` — CandidateLinkageEntry, load_linkage_entries, candidate_linkage_summary; linkage kinds: same_source, temporal_followup, spatial_neighbor, frequency_related, cross_track
- [x] `schemas/candidate_linkage_log.schema.json`
- [x] `tests/fixtures/candidate_linkage_log.json` — 5 entries (2 confirmed, 1 proposed, 1 rejected, 1 under_review)
- [x] `tests/test_candidate_linkage_log.py` — 22 tests
- [x] `instrument_log`, `archival_query_log`, `candidate_linkage_log` added to `SCHEMA_FILENAMES` (total schemas: 97)
- [x] CLI: `instrument-log-summary`, `archival-query-summary`, `candidate-linkage-summary`
- [x] `validate-all` gates: instrument_log_entry_count >= 1, archival_query_entry_count >= 1, candidate_linkage_entry_count >= 1
- [x] `validation-summary` fields: instrument_log_entry_count, archival_query_entry_count, candidate_linkage_entry_count, candidate_linkage_confirmed_count
- [x] DECISION-068: Instrument Log, Archival Query Log, And Candidate Linkage Log Complete Milestone 21

## Done When

- Instrument log covers all instrument and event kinds
- Archival query log covers all query kinds and statuses
- Candidate linkage log covers all linkage kinds and statuses with separation_arcsec for spatial entries
- All integration tests pass without network access

---

# Milestone 22 — Signal Classification Log, RFI Mitigation Log, And Candidate Annotation Log

## Goal

Add three operational provenance modules: signal characterization classification provenance, RFI flagging and mitigation provenance, and operator/automated annotation provenance.

## Tasks

- [x] `src/techno_search/signal_classification_log.py` — SignalClassificationEntry, load_signal_classification_entries, signal_classification_summary; classification kinds: narrowband, broadband, pulsed, intermittent, unknown
- [x] `schemas/signal_classification_log.schema.json`
- [x] `tests/fixtures/signal_classification_log.json` — 5 entries (2 classified, 1 unclassified, 1 ambiguous, 1 reclassified)
- [x] `tests/test_signal_classification_log.py` — 22 tests
- [x] `src/techno_search/rfi_mitigation_log.py` — RfiMitigationEntry, load_rfi_mitigation_entries, rfi_mitigation_summary; mitigation kinds: known_rfi_source, statistical_outlier, satellite_track, terrestrial_interference, other
- [x] `schemas/rfi_mitigation_log.schema.json`
- [x] `tests/fixtures/rfi_mitigation_log.json` — 5 entries (2 flagged, 1 excised, 1 masked, 1 passed)
- [x] `tests/test_rfi_mitigation_log.py` — 22 tests
- [x] `src/techno_search/candidate_annotation_log.py` — CandidateAnnotationLogEntry, load_candidate_annotation_log_entries, candidate_annotation_log_summary; annotation kinds: manual_tag, automated_flag, cross_reference, operator_note, classification_hint
- [x] `schemas/candidate_annotation_log.schema.json`
- [x] `tests/fixtures/candidate_annotation_log.json` — 5 entries (3 active, 1 superseded, 1 withdrawn)
- [x] `tests/test_candidate_annotation_log.py` — 22 tests
- [x] `signal_classification_log`, `rfi_mitigation_log`, `candidate_annotation_log` added to `SCHEMA_FILENAMES` (total schemas: 100)
- [x] CLI: `signal-classification-summary`, `rfi-mitigation-summary`, `candidate-annotation-log-summary`
- [x] `validate-all` gates: signal_classification_entry_count >= 1, rfi_mitigation_entry_count >= 1, candidate_annotation_entry_count >= 1
- [x] `validation-summary` fields: signal_classification_entry_count, signal_classification_classified_count, rfi_mitigation_entry_count, rfi_mitigation_flagged_count, candidate_annotation_entry_count, candidate_annotation_active_count
- [x] DECISION-069: Signal Classification Log, RFI Mitigation Log, And Candidate Annotation Log Complete Milestone 22

## Done When

- Signal classification log covers all classification kinds and statuses
- RFI mitigation log covers all mitigation kinds and actions with frequency_mhz for applicable entries
- Candidate annotation log covers all annotation kinds and statuses with supersedes_entry_id for superseded entries
- All integration tests pass without network access

---

# Project Operations Readiness

## Goal

Keep validation, route coverage, and CI scaffolding aligned with the scientific
guardrails before any non-synthetic validation data or external workflow is
introduced.

## Tasks

- [x] Non-networked GitHub Actions template kept under `docs/templates/ci.yml`
- [x] CI promotion caveat documented until publishing has GitHub `workflow` scope
- [x] Route coverage fixtures cover all 6/6 `Pathway` enum values
- [x] `validate-all` requires zero uncovered route-coverage pathways
- [x] Operations-readiness summary aggregates QC, alerts, review deadlines,
      route coverage, pipeline capacity, submission provenance, and SQLite log
      safety fields
- [x] Review-safe operations-readiness Markdown digest added for local operator
      handoff
- [x] CI template reports operations readiness without enabling live data
- [x] Operations action-plan summary translates readiness blockers into
      prioritized local operator tasks
- [x] CI template reports operations action-plan visibility without clearing
      blockers or authorizing external workflow
- [x] Operations action-resolution summary records local operator status for
      action-plan items
- [x] Operations action-resolution coverage verifies every current action-plan
      ID has a local provenance record
- [x] SQLite bootstrap summary restores top-level SQLite visibility for a
      supplied local ignored database path
- [x] Operations blocker-detail summary traces current action-plan blockers to
      fixture-backed local source records without clearing blockers
- [x] Operations blocker-review summary records local review status for
      blocker-detail evidence bundles without clearing blockers
- [x] Operations blocker-followup summary derives next local operator actions
      from blocker-review records without clearing blockers
- [x] Operations blocker-followup progress summary tracks progress notes
      against follow-up action IDs without clearing blockers
- [x] Operations blocker progress-review summary covers unresolved progress
      records without reopening verified-local workflow items
- [x] Operations blocker progress next-actions summary orders unresolved
      progress-review tasks without clearing blockers
- [x] Operations blocker progress-execution summary records local execution
      notes against next-action IDs without clearing blockers
- [x] Operations blocker progress-execution review summary reviews execution
      notes without clearing blockers
- [x] Operations blocker progress-execution follow-up summary plans reviewed
      execution follow-up without clearing blockers
- [x] CI template reports action-resolution visibility without clearing
      blockers or authorizing live data or external submission

## Guardrails

- CI must not enable live provider access by default.
- `external_followup_candidate` route coverage is synthetic enum coverage only.
- Real observation intake remains blocked until data policy, provenance,
  licensing, labeling, and external-review requirements are satisfied.
- `blocked_for_real_data` is an operations recommendation only. It is not a
  scientific classification and does not modify candidate scores or pathways.
- Operations action plans are task lists only; they do not clear blockers
  automatically and do not authorize live data access.
- Operations action-resolution records are workflow provenance only; they do not
  clear blockers or authorize external submission.
- Action-resolution coverage is an audit check only; full coverage does not
  mean the underlying blockers are cleared.
- SQLite bootstrap visibility is local to the supplied database path and does
  not clear non-SQLite operations blockers.
- Blocker-detail summaries are traceability aids only; fixture-backed source
  records help operator review but do not clear blockers or authorize external
  workflow.
- Blocker-review records are local provenance only; full evidence coverage
  does not clear readiness blockers, mutate scores, or authorize external
  workflow.
- Blocker-followup recommendations are local planning aids only. They preserve
  residual blockers and disabled authorization gates.
- Blocker-followup progress records are workflow notes only. They do not clear
  blockers or authorize live data or external submission.
- Blocker progress-review records are second-pass local notes only. They cover
  unresolved progress, preserve verified-local exclusions, and do not authorize
  live data or external submission.
- Blocker progress next-action records are local task ordering only. They do
  not clear blockers, reopen verified-local items, or authorize live data or
  external submission.
- Blocker progress-execution records are local workflow notes only. They do
  not clear blockers, reopen verified-local items, or authorize live data or
  external submission.
- Blocker progress-execution review records are local workflow review notes
  only. They do not clear blockers, reopen verified-local items, or authorize
  live data or external submission.
- Blocker progress-execution follow-up records are local workflow planning
  notes only. They do not clear blockers, reopen verified-local items, or
  authorize live data or external submission.

# Milestone 23 — Frequency Channel Log, Pipeline Checkpoint Log, And Candidate Status Log

- [x] `frequency_channel_log` — operational processing provenance records for frequency channel configuration; channel kinds: primary, backup, rfi_free, reserved, calibration; statuses: active, flagged, reserved, disabled
- [x] `pipeline_checkpoint_log` — operational reproducibility records for pipeline execution checkpoints; checkpoint kinds: stage_start, stage_complete, recovery_point, validation_gate, end_of_run; statuses: saved, restored, expired, invalidated
- [x] `candidate_status_log` — operational provenance records for candidate status transitions; transition kinds: initial, promotion, demotion, hold, archive; statuses: new, active, under_review, on_hold, archived
- [x] `frequency_channel_log`, `pipeline_checkpoint_log`, `candidate_status_log` added to `SCHEMA_FILENAMES` (total schemas: 103)
- [x] `techno-search frequency-channel-summary`, `techno-search pipeline-checkpoint-summary`, `techno-search candidate-status-summary` CLI commands
- [x] `validate-all` gates: `frequency_channel_entry_count >= 1`, `pipeline_checkpoint_entry_count >= 1`, `candidate_status_entry_count >= 1`
- [x] `validation-summary` fields: `frequency_channel_entry_count`, `frequency_channel_active_count`, `pipeline_checkpoint_entry_count`, `pipeline_checkpoint_saved_count`, `candidate_status_entry_count`, `candidate_status_active_count`
- [x] DECISION-070: Frequency Channel Log, Pipeline Checkpoint Log, And Candidate Status Log Complete Milestone 23

## Guardrails

- Frequency channel entries are operational processing provenance records — channel configuration does not modify candidate scores or pathway routing and does not authorize external submission or constitute a detection claim
- Pipeline checkpoint entries are operational reproducibility records — a restored checkpoint does not modify candidate scores or pathway routing and does not authorize external submission or constitute a detection claim
- Candidate status entries are operational provenance records — a status transition does not modify candidate scores or pathway routing, does not authorize external submission, and does not constitute a detection claim

# Milestone 24 — Beam Configuration Log, Calibration Event Log, And Pipeline Run Log

- [x] `beam_configuration_log` — operational processing provenance records for radio telescope beam configuration; beam kinds: primary_beam, sidelobe, calibrator_beam, off_source, synthetic_beam; statuses: configured, applied, superseded, failed
- [x] `calibration_event_log` — operational processing provenance records for pipeline calibration events; event kinds: flux_calibration, bandpass_calibration, phase_calibration, polarization_calibration, pointing_calibration; statuses: applied, failed, skipped, deferred
- [x] `pipeline_run_log` — operational reproducibility records for top-level pipeline execution runs; run kinds: full_pipeline, partial_rerun, calibration_only, test_run, recovery_run; statuses: started, completed, failed, aborted, paused
- [x] `beam_configuration_log`, `calibration_event_log`, `pipeline_run_log` added to `SCHEMA_FILENAMES` (total schemas: 106)
- [x] `techno-search beam-configuration-summary`, `techno-search calibration-event-summary`, `techno-search pipeline-run-summary` CLI commands
- [x] `validate-all` gates: `beam_configuration_entry_count >= 1`, `calibration_event_entry_count >= 1`, `pipeline_run_entry_count >= 1`
- [x] `validation-summary` fields: `beam_configuration_entry_count`, `beam_configuration_applied_count`, `calibration_event_entry_count`, `calibration_event_applied_count`, `pipeline_run_entry_count`, `pipeline_run_completed_count`
- [x] DECISION-071: Beam Configuration Log, Calibration Event Log, And Pipeline Run Log Complete Milestone 24

## Guardrails

- Beam configuration entries are operational processing provenance records — beam configuration does not modify candidate scores or pathway routing and does not authorize external submission or constitute a detection claim
- Calibration event entries are operational processing provenance records — a calibration event does not modify candidate scores or pathway routing and does not authorize external submission or constitute a detection claim
- Pipeline run entries are operational reproducibility records — a pipeline run record does not modify candidate scores or pathway routing and does not authorize external submission or constitute a detection claim

---

# Milestone 25 — Source Catalog Log, Noise Measurement Log, And Spectral Feature Log

- [x] `src/techno_search/source_catalog_log.py` — operational provenance records for source catalog cross-matching events; catalog kinds: radio_source, infrared, stellar, known_object, known_rfi; statuses: queried, matched, no_match, error
- [x] `schemas/source_catalog_log.schema.json`
- [x] `tests/fixtures/source_catalog_log.json` — 5 entries (2 matched, 1 queried, 1 no_match, 1 error)
- [x] `tests/test_source_catalog_log.py` — 22 tests
- [x] `src/techno_search/noise_measurement_log.py` — operational processing provenance records for pipeline noise and sensitivity measurements; measurement kinds: system_temperature, noise_floor, rms_baseline, sensitivity_estimate, interference_level; statuses: recorded, flagged, superseded, failed
- [x] `schemas/noise_measurement_log.schema.json`
- [x] `tests/fixtures/noise_measurement_log.json` — 5 entries (2 recorded, 1 flagged, 1 superseded, 1 failed)
- [x] `tests/test_noise_measurement_log.py` — 22 tests
- [x] `src/techno_search/spectral_feature_log.py` — operational provenance records for spectral feature extraction events; feature kinds: emission_line, absorption_line, continuum_fit, spectral_index, line_complex; statuses: detected, tentative, not_detected, artifact
- [x] `schemas/spectral_feature_log.schema.json`
- [x] `tests/fixtures/spectral_feature_log.json` — 5 entries (2 detected, 1 tentative, 1 not_detected, 1 artifact)
- [x] `tests/test_spectral_feature_log.py` — 22 tests
- [x] `source_catalog_log`, `noise_measurement_log`, `spectral_feature_log` added to `SCHEMA_FILENAMES` (total schemas: 109)
- [x] `techno-search source-catalog-summary`, `techno-search noise-measurement-summary`, `techno-search spectral-feature-summary` CLI commands
- [x] `validate-all` gates: `source_catalog_entry_count >= 1`, `noise_measurement_entry_count >= 1`, `spectral_feature_entry_count >= 1`
- [x] `validation-summary` fields: `source_catalog_entry_count`, `source_catalog_matched_count`, `noise_measurement_entry_count`, `noise_measurement_recorded_count`, `spectral_feature_entry_count`, `spectral_feature_detected_count`
- [x] DECISION-072: Source Catalog Log, Noise Measurement Log, And Spectral Feature Log Complete Milestone 25

---

# Milestone 26 — Polarization Log, Telescope Status Log, And Observation Parameter Log

- [x] `src/techno_search/polarization_log.py` — operational processing provenance records for polarization measurements; polarization kinds: stokes_i, stokes_q, stokes_u, stokes_v, circular_polarization; statuses: measured, calibrated, flagged, failed
- [x] `schemas/polarization_log.schema.json`
- [x] `tests/fixtures/polarization_log.json` — 5 entries (2 measured, 1 calibrated, 1 flagged, 1 failed)
- [x] `tests/test_polarization_log.py` — 22 tests
- [x] `src/techno_search/telescope_status_log.py` — operational scheduling provenance records for telescope operational status; status kinds: operational, maintenance, degraded, offline, commissioning; statuses: recorded, updated, superseded, error
- [x] `schemas/telescope_status_log.schema.json`
- [x] `tests/fixtures/telescope_status_log.json` — 5 entries (2 recorded, 1 updated, 1 superseded, 1 error)
- [x] `tests/test_telescope_status_log.py` — 22 tests
- [x] `src/techno_search/observation_parameter_log.py` — operational processing provenance records for observation configuration parameters; parameter kinds: integration_time, bandwidth, center_frequency, resolution, sensitivity_target; statuses: applied, overridden, flagged, failed
- [x] `schemas/observation_parameter_log.schema.json`
- [x] `tests/fixtures/observation_parameter_log.json` — 5 entries (2 applied, 1 overridden, 1 flagged, 1 failed)
- [x] `tests/test_observation_parameter_log.py` — 22 tests
- [x] `polarization_log`, `telescope_status_log`, `observation_parameter_log` added to `SCHEMA_FILENAMES` (total schemas: 112)
- [x] `techno-search polarization-summary`, `techno-search telescope-status-summary`, `techno-search observation-parameter-summary` CLI commands
- [x] `validate-all` gates: `polarization_entry_count >= 1`, `telescope_status_entry_count >= 1`, `obs_parameter_entry_count >= 1`
- [x] `validation-summary` fields: `polarization_entry_count`, `polarization_measured_count`, `telescope_status_entry_count`, `telescope_status_recorded_count`, `obs_parameter_entry_count`, `obs_parameter_applied_count`
- [x] DECISION-073: Polarization Log, Telescope Status Log, And Observation Parameter Log Complete Milestone 26

---

# Milestone 28 — Target Selection Log, Doppler Correction Log, And Data Archival Log

- [x] `src/techno_search/target_selection_log.py` — operational scheduling provenance records for target selection events; selection_kinds: priority_queue, manual_selection, automated_filter, watchlist_trigger, follow_up_request; statuses: selected, deferred, rejected, pending
- [x] `schemas/target_selection_log.schema.json`
- [x] `tests/fixtures/target_selection_log.json` — 5 entries (2 selected, 1 deferred, 1 rejected, 1 pending)
- [x] `tests/test_target_selection_log.py` — 22 tests
- [x] `src/techno_search/doppler_correction_log.py` — operational processing provenance records for Doppler correction; correction_kinds: barycentric, topocentric, heliocentric, observatory_frame, rest_frame; statuses: applied, failed, not_applicable, flagged
- [x] `schemas/doppler_correction_log.schema.json`
- [x] `tests/fixtures/doppler_correction_log.json` — 5 entries (2 applied, 1 failed, 1 not_applicable, 1 flagged)
- [x] `tests/test_doppler_correction_log.py` — 22 tests
- [x] `src/techno_search/data_archival_log.py` — operational provenance records for observation data archival events; archival_kinds: raw_data, processed_data, candidate_packet, pipeline_artifact, calibration_data; statuses: archived, pending, failed, deleted
- [x] `schemas/data_archival_log.schema.json`
- [x] `tests/fixtures/data_archival_log.json` — 5 entries (2 archived, 1 pending, 1 failed, 1 deleted)
- [x] `tests/test_data_archival_log.py` — 22 tests
- [x] `target_selection_log`, `doppler_correction_log`, `data_archival_log` added to `SCHEMA_FILENAMES` (total schemas: 116)
- [x] `techno-search target-selection-summary`, `techno-search doppler-correction-summary`, `techno-search data-archival-summary` CLI commands
- [x] `validate-all` gates: `target_selection_entry_count >= 1`, `doppler_correction_entry_count >= 1`, `data_archival_entry_count >= 1`
- [x] `validation-summary` fields: `target_selection_entry_count`, `target_selection_selected_count`, `doppler_correction_entry_count`, `doppler_correction_applied_count`, `data_archival_entry_count`, `data_archival_archived_count`
- [x] DECISION-075: Target Selection Log, Doppler Correction Log, And Data Archival Log Complete Milestone 28

---

# Milestone 29 — Production Ingestion Hardening

- [x] `run-pipeline` CLI command validates one local CSV input before scoring and report writing
- [x] Pipeline run JSON records the structural validation result, reader type, row count, report paths, and conservative disclaimer
- [x] `schemas/data_quality.schema.json` added for `validate-input` output (total schemas: 117)
- [x] Archival/catalog anomaly CSV reader added for synthetic-compatible anomaly feature tables
- [x] Synthetic anomaly CSV fixture added under `tests/fixtures/anomaly/`
- [x] Focused tests added for anomaly CSV reading, structural input validation, and `run-pipeline`
- [x] DECISION-076: Pipeline Input Validation Gates Local CSV Scoring
