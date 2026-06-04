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

---

# Milestone 30 — RFI Database Guardrails

- [x] `src/techno_search/rfi_database.py` — local site-specific RFI database records with provenance validation
- [x] `schemas/rfi_database.schema.json`
- [x] `tests/fixtures/rfi_database.json` — 5 synthetic entries covering reviewed, provisional, and deprecated records
- [x] `tests/test_rfi_database.py` — guardrail tests for ranges, provenance, matching, and conservative disclaimers
- [x] `techno-search rfi-database-summary` CLI command
- [x] Radio candidates now record RFI database schema version, record count, reviewed count, validation status, and overlap IDs
- [x] `rfi_database` added to `SCHEMA_FILENAMES` (total schemas: 118)
- [x] `validate-all` gates: `rfi_database_record_count >= 1`, `rfi_database_reviewed_count >= 1`, and `rfi_database_validation_ok`
- [x] `validation-summary` fields: `rfi_database_record_count`, `rfi_database_reviewed_count`, `rfi_database_validation_ok`, `rfi_database_synthetic_count`
- [x] DECISION-077: RFI Database Guardrails Precede Any Radio Threshold Recalibration

---

# Milestone 31 — RFI Database Admission Gates

- [x] `src/techno_search/rfi_database_admission.py` — local readiness records for proposed RFI database sources
- [x] `schemas/rfi_database_admission.schema.json`
- [x] `tests/fixtures/rfi_database_admission.json` — 4 records covering synthetic-only and blocked real-source admission states
- [x] `tests/test_rfi_database_admission.py` — guardrail tests for review requirements, blocker counts, and real-data authorization
- [x] `techno-search rfi-database-admission-summary` CLI command
- [x] `rfi_database_admission` added to `SCHEMA_FILENAMES` (total schemas: 119)
- [x] `validate-all` gates: admission records exist, validation is clean, and real-data authorization count remains zero
- [x] `validation-summary` fields: `rfi_database_admission_record_count`, `rfi_database_admission_blocked_count`, `rfi_database_admission_real_data_authorized_count`, `rfi_database_admission_validation_ok`
- [x] DECISION-078: RFI Database Admission Records Gate Real RFI Source Lists

---

# Milestone 32 — Curated Dataset Admission Gates

- [x] `src/techno_search/curated_dataset_admission.py` — local readiness records for proposed curated validation datasets
- [x] `schemas/curated_dataset_admission.schema.json`
- [x] `tests/fixtures/curated_dataset_admission.json` — 4 records covering synthetic-only and blocked real-dataset admission states
- [x] `tests/test_curated_dataset_admission.py` — guardrail tests for review requirements, blocker counts, and real-data authorization
- [x] `techno-search curated-dataset-admission-summary` CLI command
- [x] `curated_dataset_admission` added to `SCHEMA_FILENAMES` (total schemas: 120)
- [x] `validate-all` gates: admission records exist, validation is clean, and real-data authorization count remains zero
- [x] `validation-summary` fields: `curated_dataset_admission_record_count`, `curated_dataset_admission_blocked_count`, `curated_dataset_admission_real_data_authorized_count`, `curated_dataset_admission_validation_ok`
- [x] DECISION-079: Curated Dataset Admission Records Gate Real Labeled Dataset Supplements

---

# Milestone 33 — Production Readiness Status Consistency Gates

- [x] `src/techno_search/project_status_consistency.py` — local documentation and validation drift checks for project readiness status
- [x] `schemas/project_status_consistency.schema.json`
- [x] `tests/fixtures/project_status_consistency.json` — expected latest milestone, decision, schema count, and zero-real-data authorization gate metadata
- [x] `tests/test_project_status_consistency.py` — guardrail tests for stale milestone metadata, schema-count drift, and zero-real-data authorization visibility
- [x] `techno-search project-status-consistency-summary` CLI command
- [x] `project_status_consistency` added to `SCHEMA_FILENAMES` (total schemas: 121)
- [x] `validate-all` gate: project status consistency check must pass
- [x] `validation-summary` fields: `project_status_consistency_ok`, `project_status_latest_milestone`, `project_status_latest_decision`, `project_status_schema_count`
- [x] DECISION-080: Production Readiness Status Must Stay Aligned With Validation Gates

---

# Milestone 34 — Operations Alert Review Consistency Gates

- [x] `src/techno_search/operations_alert_review_consistency.py` — local alert/QC operator-review visibility checks for candidate alerts, alert resolutions, QC health, operations readiness, and disabled authorization counts
- [x] `schemas/operations_alert_review_consistency.schema.json`
- [x] `tests/fixtures/operations_alert_review_consistency.json` — expected open-alert count, critical-open-alert count, alert-resolution open count, QC health, readiness recommendation, and zero live/external authorization gates
- [x] `tests/test_operations_alert_review_consistency.py` — guardrail tests for count drift, missing critical-alert resolution coverage, and authorization drift
- [x] `techno-search operations-alert-review-consistency-summary` CLI command
- [x] `operations_alert_review_consistency` added to `SCHEMA_FILENAMES` (total schemas: 122)
- [x] `validate-all` gate: operations alert review consistency check must pass
- [x] `validation-summary` fields: `operations_alert_review_consistency_ok`, `operations_alert_review_open_alert_count`, `operations_alert_review_critical_open_alert_count`, `operations_alert_review_uncovered_open_alert_count`
- [x] DECISION-081: Operations Alert Review Visibility Must Stay Aligned With QC Gates

---

# Milestone 35 — Operations Action Resolution Staleness Gates

- [x] `src/techno_search/operations_action_resolution_consistency.py` — local action-resolution staleness checks for current action-plan IDs, stale resolution records, residual blockers, coverage, and disabled authorization counts
- [x] `schemas/operations_action_resolution_consistency.schema.json`
- [x] `tests/fixtures/operations_action_resolution_consistency.json` — expected current action count, resolution record count, stale resolution IDs, residual blocker total, coverage requirement, and zero live/external authorization gates
- [x] `tests/test_operations_action_resolution_consistency.py` — guardrail tests for stale-ID drift, missing current action coverage, and authorization drift
- [x] `techno-search operations-action-resolution-consistency-summary` CLI command
- [x] `operations_action_resolution_consistency` added to `SCHEMA_FILENAMES` (total schemas: 123)
- [x] `validate-all` gate: operations action-resolution consistency check must pass
- [x] `validation-summary` fields: `operations_action_resolution_consistency_ok`, `operations_action_resolution_consistency_stale_count`, `operations_action_resolution_consistency_stale_action_ids`, `operations_action_resolution_consistency_missing_action_count`
- [x] DECISION-082: Operations Action Resolution Staleness Must Stay Aligned With Action Plans

---

# Milestone 36 — Operations Blocker Progress Consistency Gates

- [x] `src/techno_search/operations_blocker_progress_consistency.py` — local blocker-progress chain checks for blocker-detail, review, follow-up, progress, next-action, execution, execution-review, execution-follow-up, residual blockers, verified-local exclusions, categories, mismatch totals, priority ordering, and disabled authorization counts
- [x] `schemas/operations_blocker_progress_consistency.schema.json`
- [x] `tests/fixtures/operations_blocker_progress_consistency.json` — expected chain counts, residual blocker total, verified-local progress action IDs, categories covered, coverage requirement, priority ordering requirement, zero mismatch requirement, and zero live/external authorization gates
- [x] `tests/test_operations_blocker_progress_consistency.py` — guardrail tests for count drift, residual drift, category drift, coverage drift, mismatch drift, and authorization drift
- [x] `techno-search operations-blocker-progress-consistency-summary` CLI command
- [x] `operations_blocker_progress_consistency` added to `SCHEMA_FILENAMES` (total schemas: 124)
- [x] `validate-all` gate: operations blocker-progress consistency check must pass
- [x] `validation-summary` fields: `operations_blocker_progress_consistency_ok`, `operations_blocker_progress_consistency_issue_count`, `operations_blocker_progress_consistency_residual_blocker_total`, `operations_blocker_progress_consistency_mismatch_total`, `operations_blocker_progress_consistency_live_data_authorized_total`, `operations_blocker_progress_consistency_external_submission_authorized_total`
- [x] DECISION-083: Operations Blocker Progress Chains Must Stay Aligned

---

# Milestone 37 — Top-Level SQLite Log Consistency Gates

- [x] `src/techno_search/top_level_sqlite_log_consistency.py` — local top-level SQLite log consistency checks for database visibility, validation, integrity, migration state, weekly digest state, retention state, PRAGMA diagnostics, commit-guard state, run/outcome alignment, and disabled network/external authorization counts
- [x] `schemas/top_level_sqlite_log_consistency.schema.json`
- [x] `tests/fixtures/top_level_sqlite_log_consistency.json` — expected SQLite health, migration, authorization, run/outcome, and commit-guard requirements
- [x] `tests/test_top_level_sqlite_log_consistency.py` — guardrail tests for missing database visibility, run/outcome drift, authorization drift, migration drift, and commit-guard drift
- [x] `techno-search sqlite-log-consistency-summary` CLI command
- [x] `top_level_sqlite_log_consistency` added to `SCHEMA_FILENAMES` (total schemas: 125)
- [x] `validate-all` gate: top-level SQLite log consistency check must pass
- [x] `validation-summary` fields: `top_level_sqlite_log_consistency_ok`, `top_level_sqlite_log_consistency_issue_count`
- [x] DECISION-084: Top-Level SQLite Logs Must Keep Health And Authorization Gates Aligned

---

# Milestone 38 — Production Blocker Visibility Consistency Gates

- [x] `src/techno_search/production_blocker_consistency.py` — local production-readiness blocker visibility checks for Tier 1 blocker phrases, RFI admission blockers, curated-dataset admission blockers, operations-readiness blocker state, and disabled authorization counts
- [x] `schemas/production_blocker_consistency.schema.json`
- [x] `tests/fixtures/production_blocker_consistency.json` — expected Tier 1 blocker phrases, minimum blocker visibility, admission blocker requirements, operations-readiness blocker requirement, and zero authorization gates
- [x] `tests/test_production_blocker_consistency.py` — guardrail tests for missing blocker drift, authorization drift, admission blocker drift, and operations-readiness drift
- [x] `techno-search production-blocker-consistency-summary` CLI command
- [x] `production_blocker_consistency` added to `SCHEMA_FILENAMES` (total schemas: 126)
- [x] `validate-all` gate: production blocker consistency check must pass
- [x] `validation-summary` fields: `production_blocker_consistency_ok`, `production_blocker_consistency_issue_count`, `production_blocker_tier1_blocker_count`, `production_blocker_real_data_authorized_total`, `production_blocker_external_submission_authorized_total`
- [x] DECISION-085: Production Blockers Must Remain Visible Until Explicitly Resolved

# Milestone 39 — Consistency Gate Repair And Three New Operational Logs

- [x] `tests/fixtures/operations_action_resolution_consistency.json` — corrected expected values to match actual action plan (8 actions, 2 stale resolutions)
- [x] `tests/fixtures/operations_blocker_progress_consistency.json` — corrected expected `detail_count` to match actual detail records (8)
- [x] `tests/conftest.py` — `ensure_sqlite_log_initialized` session fixture ensures SQLite log is ready before consistency tests
- [x] `src/techno_search/data_transfer_log.py` — operational provenance records for data transfer events; transfer_kinds: archive_transfer, inter_site_transfer, local_copy, cloud_upload, network_delivery; statuses: pending, completed, failed, verified
- [x] `schemas/data_transfer_log.schema.json`
- [x] `tests/fixtures/data_transfer_log.json` — 5 entries (2 completed, 1 pending, 1 failed, 1 verified)
- [x] `tests/test_data_transfer_log.py` — 23 tests
- [x] `src/techno_search/scheduling_conflict_log.py` — operational provenance records for scheduling conflict events; conflict_kinds: time_slot_overlap, resource_contention, priority_conflict, maintenance_window, weather_hold; statuses: detected, resolved, escalated, deferred
- [x] `schemas/scheduling_conflict_log.schema.json`
- [x] `tests/fixtures/scheduling_conflict_log.json` — 5 entries (2 detected, 1 resolved, 1 escalated, 1 deferred)
- [x] `tests/test_scheduling_conflict_log.py` — 22 tests
- [x] `src/techno_search/system_health_log.py` — operational provenance records for system health monitoring events; health_kinds: cpu_usage, memory_usage, disk_space, network_latency, process_uptime; statuses: healthy, warning, critical, unknown
- [x] `schemas/system_health_log.schema.json`
- [x] `tests/fixtures/system_health_log.json` — 5 entries (2 healthy, 1 warning, 1 critical, 1 unknown)
- [x] `tests/test_system_health_log.py` — 22 tests
- [x] `data_transfer_log`, `scheduling_conflict_log`, `system_health_log` added to `SCHEMA_FILENAMES` (total schemas: 133)
- [x] `techno-search data-transfer-summary`, `techno-search scheduling-conflict-summary`, `techno-search system-health-summary` CLI commands
- [x] `validate-all` gates: `data_transfer_entry_count >= 1`, `scheduling_conflict_entry_count >= 1`, `system_health_entry_count >= 1`
- [x] `validation-summary` fields: `data_transfer_entry_count`, `data_transfer_completed_count`, `scheduling_conflict_entry_count`, `scheduling_conflict_detected_count`, `system_health_entry_count`, `system_health_healthy_count`
- [x] DECISION-086: Data Transfer Log, Scheduling Conflict Log, And System Health Log Complete Milestone 39

# Milestone 40 — Instrument Configuration Log, Scan Log, And Time Synchronization Log

- [x] `src/techno_search/instrument_configuration_log.py` — operational provenance records for instrument hardware configuration changes; configuration_kinds: frontend_swap, backend_change, receiver_install, filter_change, attenuator_set; statuses: applied, pending, reverted, failed
- [x] `schemas/instrument_configuration_log.schema.json`
- [x] `tests/fixtures/instrument_configuration_log.json` — 5 entries (2 applied, 1 pending, 1 reverted, 1 failed)
- [x] `tests/test_instrument_configuration_log.py` — 22 tests
- [x] `src/techno_search/scan_log.py` — operational provenance records for individual telescope scan events; scan_kinds: on_source, off_source, calibrator, reference_position, slew; statuses: completed, aborted, flagged, pending
- [x] `schemas/scan_log.schema.json`
- [x] `tests/fixtures/scan_log.json` — 5 entries (2 completed, 1 aborted, 1 flagged, 1 pending)
- [x] `tests/test_scan_log.py` — 22 tests
- [x] `src/techno_search/time_synchronization_log.py` — operational provenance records for time and clock synchronization events; sync_kinds: ntp_sync, gps_sync, manual_correction, drift_check, epoch_reset; statuses: synchronized, drifted, failed, not_required
- [x] `schemas/time_synchronization_log.schema.json`
- [x] `tests/fixtures/time_synchronization_log.json` — 5 entries (2 synchronized, 1 drifted, 1 failed, 1 not_required)
- [x] `tests/test_time_synchronization_log.py` — 22 tests
- [x] `instrument_configuration_log`, `scan_log`, `time_synchronization_log` added to `SCHEMA_FILENAMES` (total schemas: 136)
- [x] `techno-search instrument-configuration-summary`, `techno-search scan-log-summary`, `techno-search time-synchronization-summary` CLI commands
- [x] `validate-all` gates: `instrument_configuration_entry_count >= 1`, `scan_entry_count >= 1`, `time_sync_entry_count >= 1`
- [x] `validation-summary` fields: `instrument_configuration_entry_count`, `instrument_configuration_applied_count`, `scan_entry_count`, `scan_completed_count`, `time_synchronization_entry_count`, `time_synchronization_synchronized_count`
- [x] DECISION-087: Instrument Configuration Log, Scan Log, And Time Synchronization Log Complete Milestone 40

# Milestone 41 — Antenna Pointing Log, Weather Log, And Power Log

- [x] `src/techno_search/antenna_pointing_log.py` — operational provenance records for antenna pointing and slew events; pointing_kinds: target_slew, park_position, stow_position, tracking_start, tracking_end; statuses: completed, failed, timeout, cancelled
- [x] `schemas/antenna_pointing_log.schema.json`
- [x] `tests/fixtures/antenna_pointing_log.json` — 5 entries (2 completed, 1 failed, 1 timeout, 1 cancelled)
- [x] `tests/test_antenna_pointing_log.py` — 22 tests
- [x] `src/techno_search/weather_log.py` — operational provenance records for site weather monitoring events; weather_kinds: wind_speed, temperature, humidity, precipitation, seeing; statuses: nominal, advisory, warning, observation_hold
- [x] `schemas/weather_log.schema.json`
- [x] `tests/fixtures/weather_log.json` — 5 entries (2 nominal, 1 advisory, 1 warning, 1 observation_hold)
- [x] `tests/test_weather_log.py` — 22 tests
- [x] `src/techno_search/power_log.py` — operational provenance records for facility power system events; power_kinds: ups_event, mains_failure, generator_start, load_shed, power_restoration; statuses: normal, degraded, critical, restored
- [x] `schemas/power_log.schema.json`
- [x] `tests/fixtures/power_log.json` — 5 entries (2 normal, 1 degraded, 1 critical, 1 restored)
- [x] `tests/test_power_log.py` — 22 tests
- [x] `antenna_pointing_log`, `weather_log`, `power_log` added to `SCHEMA_FILENAMES` (total schemas: 139)
- [x] `techno-search antenna-pointing-summary`, `techno-search weather-summary`, `techno-search power-summary` CLI commands
- [x] `validate-all` gates: `antenna_pointing_entry_count >= 1`, `weather_entry_count >= 1`, `power_entry_count >= 1`
- [x] `validation-summary` fields: `antenna_pointing_entry_count`, `antenna_pointing_completed_count`, `weather_entry_count`, `weather_nominal_count`, `power_entry_count`, `power_normal_count`
- [x] DECISION-088: Antenna Pointing Log, Weather Log, And Power Log Complete Milestone 41

# Milestone 42 — Cooling System Log, Network Connectivity Log, And Software Update Log

- [x] `src/techno_search/cooling_system_log.py` — operational provenance records for cryogenic and cooling system events; cooling_kinds: cooldown_start, cooldown_complete, warmup_event, temperature_alarm, helium_refill; statuses: operating, warning, fault, maintenance
- [x] `schemas/cooling_system_log.schema.json`
- [x] `tests/fixtures/cooling_system_log.json` — 5 entries (2 operating, 1 warning, 1 fault, 1 maintenance)
- [x] `tests/test_cooling_system_log.py` — 22 tests
- [x] `src/techno_search/network_connectivity_log.py` — operational provenance records for network infrastructure events; network_kinds: link_up, link_down, latency_spike, packet_loss, vpn_event; statuses: connected, degraded, disconnected, restored
- [x] `schemas/network_connectivity_log.schema.json`
- [x] `tests/fixtures/network_connectivity_log.json` — 5 entries (2 connected, 1 degraded, 1 disconnected, 1 restored)
- [x] `tests/test_network_connectivity_log.py` — 22 tests
- [x] `src/techno_search/software_update_log.py` — operational provenance records for software and firmware update events; update_kinds: pipeline_update, firmware_update, os_patch, driver_update, config_deploy; statuses: deployed, failed, rolled_back, pending
- [x] `schemas/software_update_log.schema.json`
- [x] `tests/fixtures/software_update_log.json` — 5 entries (2 deployed, 1 failed, 1 rolled_back, 1 pending)
- [x] `tests/test_software_update_log.py` — 22 tests
- [x] `cooling_system_log`, `network_connectivity_log`, `software_update_log` added to `SCHEMA_FILENAMES` (total schemas: 142)
- [x] `techno-search cooling-system-summary`, `techno-search network-connectivity-summary`, `techno-search software-update-summary` CLI commands
- [x] `validate-all` gates: `cooling_entry_count >= 1`, `network_entry_count >= 1`, `sw_update_entry_count >= 1`
- [x] `validation-summary` fields: `cooling_system_entry_count`, `cooling_system_operating_count`, `network_connectivity_entry_count`, `network_connectivity_connected_count`, `software_update_entry_count`, `software_update_deployed_count`
- [x] DECISION-089: Cooling System Log, Network Connectivity Log, And Software Update Log Complete Milestone 42

# Milestone 43 — Hardware Fault Log, Maintenance Log, And Environmental Log

- [x] `src/techno_search/hardware_fault_log.py` — operational provenance records for hardware fault events; fault_kinds: cpu_fault, memory_fault, disk_fault, network_fault, psu_fault; statuses: detected, diagnosed, repaired, deferred
- [x] `schemas/hardware_fault_log.schema.json`
- [x] `tests/fixtures/hardware_fault_log.json` — 5 entries (2 detected, 1 diagnosed, 1 repaired, 1 deferred)
- [x] `tests/test_hardware_fault_log.py` — 22 tests
- [x] `src/techno_search/maintenance_log.py` — operational provenance records for maintenance activities; maintenance_kinds: scheduled_maintenance, emergency_repair, calibration_service, firmware_service, inspection; statuses: planned, in_progress, completed, deferred
- [x] `schemas/maintenance_log.schema.json`
- [x] `tests/fixtures/maintenance_log.json` — 5 entries (2 completed, 1 in_progress, 1 planned, 1 deferred)
- [x] `tests/test_maintenance_log.py` — 22 tests
- [x] `src/techno_search/environmental_log.py` — operational provenance records for environmental monitoring readings; environment_kinds: temperature_reading, humidity_reading, pressure_reading, vibration_reading, electromagnetic_interference; statuses: nominal, advisory, warning, critical
- [x] `schemas/environmental_log.schema.json`
- [x] `tests/fixtures/environmental_log.json` — 5 entries (2 nominal, 1 advisory, 1 warning, 1 critical)
- [x] `tests/test_environmental_log.py` — 22 tests
- [x] `hardware_fault_log`, `maintenance_log`, `environmental_log` added to `SCHEMA_FILENAMES` (total schemas: 145)
- [x] `techno-search hardware-fault-summary`, `techno-search maintenance-summary`, `techno-search environmental-summary` CLI commands
- [x] `validate-all` gates: `hw_fault_entry_count >= 1`, `maintenance_entry_count >= 1`, `env_entry_count >= 1`
- [x] `validation-summary` fields: `hardware_fault_entry_count`, `hardware_fault_detected_count`, `maintenance_entry_count`, `maintenance_completed_count`, `environmental_entry_count`, `environmental_nominal_count`
- [x] DECISION-090: Hardware Fault Log, Maintenance Log, And Environmental Log Complete Milestone 43

# Milestone 44 — Access Log, Security Event Log, And Audit Trail Log

- [x] `src/techno_search/access_log.py` — operational provenance records for facility and system access events; access_kinds: facility_entry, facility_exit, remote_access, system_login, system_logout; statuses: denied, expired, granted, revoked
- [x] `schemas/access_log.schema.json`
- [x] `tests/fixtures/access_log.json` — 5 entries (2 granted, 1 denied, 1 expired, 1 revoked)
- [x] `tests/test_access_log.py` — 22 tests
- [x] `src/techno_search/security_event_log.py` — operational provenance records for security events; event_kinds: credential_change, intrusion_attempt, physical_breach, policy_violation, unauthorized_access; statuses: detected, escalated, investigated, resolved
- [x] `schemas/security_event_log.schema.json`
- [x] `tests/fixtures/security_event_log.json` — 5 entries (2 detected, 1 investigated, 1 resolved, 1 escalated)
- [x] `tests/test_security_event_log.py` — 22 tests
- [x] `src/techno_search/audit_trail_log.py` — operational provenance records for audit trail events; audit_kinds: compliance_check, config_change, data_access, system_event, user_action; statuses: archived, flagged, recorded, reviewed
- [x] `schemas/audit_trail_log.schema.json`
- [x] `tests/fixtures/audit_trail_log.json` — 5 entries (2 recorded, 1 flagged, 1 reviewed, 1 archived)
- [x] `tests/test_audit_trail_log.py` — 22 tests
- [x] `access_log`, `security_event_log`, `audit_trail_log` added to `SCHEMA_FILENAMES` (total schemas: 148)
- [x] `techno-search access-log-summary`, `techno-search security-event-summary`, `techno-search audit-trail-log-summary` CLI commands
- [x] `validate-all` gates: `access_entry_count >= 1`, `sec_event_entry_count >= 1`, `audit_trail_log_entry_count >= 1`
- [x] `validation-summary` fields: `access_log_entry_count`, `access_log_granted_count`, `security_event_entry_count`, `security_event_detected_count`, `audit_trail_log_entry_count`, `audit_trail_log_recorded_count`
- [x] DECISION-091: Access Log, Security Event Log, And Audit Trail Log Complete Milestone 44

# Milestone 45 — Incident Response Log, Change Management Log, And Compliance Report Log

- [x] `src/techno_search/incident_response_log.py` — operational provenance records for facility incident response events; incident_kinds: containment, detection, eradication, lessons_learned, recovery; statuses: closed, contained, open, resolved
- [x] `schemas/incident_response_log.schema.json`
- [x] `tests/fixtures/incident_response_log.json` — 5 entries (2 open, 1 contained, 1 resolved, 1 closed)
- [x] `tests/test_incident_response_log.py` — 22 tests
- [x] `src/techno_search/change_management_log.py` — operational provenance records for structured change management events; change_kinds: approval_request, emergency_change, planned_change, rejection, rollback; statuses: approved, implemented, requested, rolled_back
- [x] `schemas/change_management_log.schema.json`
- [x] `tests/fixtures/change_management_log.json` — 5 entries (2 implemented, 1 requested, 1 approved, 1 rolled_back)
- [x] `tests/test_change_management_log.py` — 22 tests
- [x] `src/techno_search/compliance_report_log.py` — operational provenance records for compliance reporting events; report_kinds: certification_check, external_audit, internal_audit, policy_review, regulatory_report; statuses: failed, passed, pending, waived
- [x] `schemas/compliance_report_log.schema.json`
- [x] `tests/fixtures/compliance_report_log.json` — 5 entries (2 passed, 1 failed, 1 pending, 1 waived)
- [x] `tests/test_compliance_report_log.py` — 22 tests
- [x] `incident_response_log`, `change_management_log`, `compliance_report_log` added to `SCHEMA_FILENAMES` (total schemas: 151)
- [x] `techno-search incident-response-summary`, `techno-search change-management-summary`, `techno-search compliance-report-summary` CLI commands
- [x] `validate-all` gates: `incident_response_entry_count >= 1`, `change_mgmt_entry_count >= 1`, `compliance_report_entry_count >= 1`
- [x] `validation-summary` fields: `incident_response_entry_count`, `incident_response_resolved_count`, `change_management_entry_count`, `change_management_implemented_count`, `compliance_report_entry_count`, `compliance_report_passed_count`
- [x] DECISION-092: Incident Response Log, Change Management Log, And Compliance Report Log Complete Milestone 45

# Milestone 46 — Risk Assessment Log, Backup Recovery Log, And Capacity Planning Log

- [x] `src/techno_search/risk_assessment_log.py` — operational provenance records for facility risk assessment events; risk_kinds: compliance_risk, cyber_risk, environmental_risk, operational_risk, physical_risk; statuses: accepted, assessed, identified, mitigated
- [x] `schemas/risk_assessment_log.schema.json`
- [x] `tests/fixtures/risk_assessment_log.json` — 5 entries (2 mitigated, 1 identified, 1 assessed, 1 accepted)
- [x] `tests/test_risk_assessment_log.py` — 22 tests
- [x] `src/techno_search/backup_recovery_log.py` — operational provenance records for backup and recovery events; backup_kinds: differential_backup, full_backup, incremental_backup, recovery_test, snapshot; statuses: completed, failed, in_progress, skipped
- [x] `schemas/backup_recovery_log.schema.json`
- [x] `tests/fixtures/backup_recovery_log.json` — 5 entries (3 completed, 1 failed, 1 skipped)
- [x] `tests/test_backup_recovery_log.py` — 22 tests
- [x] `src/techno_search/capacity_planning_log.py` — operational provenance records for capacity planning events; capacity_kinds: compute_capacity, equipment_capacity, network_capacity, personnel_capacity, storage_capacity; statuses: adequate, critical, planned_expansion, warning
- [x] `schemas/capacity_planning_log.schema.json`
- [x] `tests/fixtures/capacity_planning_log.json` — 5 entries (2 adequate, 1 warning, 1 critical, 1 planned_expansion)
- [x] `tests/test_capacity_planning_log.py` — 22 tests
- [x] `risk_assessment_log`, `backup_recovery_log`, `capacity_planning_log` added to `SCHEMA_FILENAMES` (total schemas: 154)
- [x] `techno-search risk-assessment-summary`, `techno-search backup-recovery-summary`, `techno-search capacity-planning-summary` CLI commands
- [x] `validate-all` gates: `risk_assessment_entry_count >= 1`, `backup_recovery_entry_count >= 1`, `capacity_planning_entry_count >= 1`
- [x] `validation-summary` fields: `risk_assessment_entry_count`, `risk_assessment_mitigated_count`, `backup_recovery_entry_count`, `backup_recovery_completed_count`, `capacity_planning_entry_count`, `capacity_planning_adequate_count`
- [x] DECISION-093: Risk Assessment Log, Backup Recovery Log, And Capacity Planning Log Complete Milestone 46

# Milestone 47 — Software Deployment Log, Performance Monitoring Log, And User Activity Log

- [x] `src/techno_search/software_deployment_log.py` — operational provenance records for software deployment events; deployment_kinds: hotfix, major_release, minor_release, patch, rollback; statuses: completed, failed, in_progress, rolled_back
- [x] `schemas/software_deployment_log.schema.json`
- [x] `tests/fixtures/software_deployment_log.json` — 5 entries (2 completed, 1 in_progress, 1 failed, 1 rolled_back)
- [x] `tests/test_software_deployment_log.py` — 22 tests
- [x] `src/techno_search/performance_monitoring_log.py` — operational provenance records for performance monitoring events; performance_kinds: cpu_utilization, disk_io, memory_utilization, network_throughput, response_time; statuses: alert, critical, degraded, normal
- [x] `schemas/performance_monitoring_log.schema.json`
- [x] `tests/fixtures/performance_monitoring_log.json` — 5 entries (2 normal, 1 alert, 1 degraded, 1 critical)
- [x] `tests/test_performance_monitoring_log.py` — 22 tests
- [x] `src/techno_search/user_activity_log.py` — operational provenance records for user activity events; activity_kinds: admin_action, api_call, config_change, data_export, login; statuses: blocked, failed, succeeded, warning
- [x] `schemas/user_activity_log.schema.json`
- [x] `tests/fixtures/user_activity_log.json` — 5 entries (2 succeeded, 1 warning, 1 failed, 1 blocked)
- [x] `tests/test_user_activity_log.py` — 22 tests
- [x] `software_deployment_log`, `performance_monitoring_log`, `user_activity_log` added to `SCHEMA_FILENAMES` (total schemas: 157)
- [x] `techno-search software-deployment-summary`, `techno-search performance-monitoring-summary`, `techno-search user-activity-summary` CLI commands
- [x] `validate-all` gates: `software_deployment_entry_count >= 1`, `performance_monitoring_entry_count >= 1`, `user_activity_entry_count >= 1`
- [x] `validation-summary` fields: `software_deployment_entry_count`, `software_deployment_completed_count`, `performance_monitoring_entry_count`, `performance_monitoring_normal_count`, `user_activity_entry_count`, `user_activity_succeeded_count`
- [x] DECISION-094: Software Deployment Log, Performance Monitoring Log, And User Activity Log Complete Milestone 47

# Milestone 49 — Firmware Update Log, Configuration Audit Log, And Event Correlation Log

- [x] `src/techno_search/firmware_update_log.py` — operational provenance records for firmware lifecycle events; firmware_kinds: component_update, driver_update, firmware_rollback, hotfix_patch, scheduled_update; statuses: applied, failed, pending, rolled_back
- [x] `schemas/firmware_update_log.schema.json`
- [x] `tests/fixtures/firmware_update_log.json` — 5 entries (2 applied, 1 pending, 1 failed, 1 rolled_back)
- [x] `tests/test_firmware_update_log.py` — 22 tests
- [x] `src/techno_search/configuration_audit_log.py` — operational provenance records for configuration compliance audit events; audit_kinds: baseline_check, compliance_scan, drift_detection, manual_audit, scheduled_audit; statuses: compliant, drifted, failed, inconclusive
- [x] `schemas/configuration_audit_log.schema.json`
- [x] `tests/fixtures/configuration_audit_log.json` — 5 entries (2 compliant, 1 drifted, 1 failed, 1 inconclusive)
- [x] `tests/test_configuration_audit_log.py` — 22 tests
- [x] `src/techno_search/event_correlation_log.py` — operational provenance records for cross-system event correlation runs; correlation_kinds: alert_cluster, causal_chain, fault_event, observation_link, temporal_cluster; statuses: correlated, inconclusive, no_match, pending
- [x] `schemas/event_correlation_log.schema.json`
- [x] `tests/fixtures/event_correlation_log.json` — 5 entries (2 correlated, 1 inconclusive, 1 no_match, 1 pending)
- [x] `tests/test_event_correlation_log.py` — 22 tests
- [x] `firmware_update_log`, `configuration_audit_log`, `event_correlation_log` added to `SCHEMA_FILENAMES` (total schemas: 163)
- [x] `techno-search firmware-update-summary`, `techno-search configuration-audit-summary`, `techno-search event-correlation-summary` CLI commands
- [x] `validate-all` gates: `firmware_update_entry_count >= 1`, `configuration_audit_entry_count >= 1`, `event_correlation_entry_count >= 1`
- [x] `validation-summary` fields: `firmware_update_entry_count`, `firmware_update_applied_count`, `configuration_audit_entry_count`, `configuration_audit_compliant_count`, `event_correlation_entry_count`, `event_correlation_correlated_count`
- [x] DECISION-096: Firmware Update Log, Configuration Audit Log, And Event Correlation Log Complete Milestone 49

# Milestone 48 — Health Check Log, License Management Log, And Storage Management Log

- [x] `src/techno_search/health_check_log.py` — operational provenance records for system and service health check events; check_kinds: api_health, database_health, network_health, service_health, storage_health; statuses: degraded, failed, passed, timeout
- [x] `schemas/health_check_log.schema.json`
- [x] `tests/fixtures/health_check_log.json` — 5 entries (2 passed, 1 degraded, 1 failed, 1 timeout)
- [x] `tests/test_health_check_log.py` — 22 tests
- [x] `src/techno_search/license_management_log.py` — operational provenance records for software license lifecycle events; license_kinds: activation, deactivation, expiry_warning, renewal, transfer; statuses: active, expired, failed, renewed
- [x] `schemas/license_management_log.schema.json`
- [x] `tests/fixtures/license_management_log.json` — 5 entries (2 active, 1 expired, 1 failed, 1 renewed)
- [x] `tests/test_license_management_log.py` — 22 tests
- [x] `src/techno_search/storage_management_log.py` — operational provenance records for storage lifecycle events; storage_kinds: allocation, cleanup, deallocation, migration, quota_change; statuses: completed, failed, in_progress, pending
- [x] `schemas/storage_management_log.schema.json`
- [x] `tests/fixtures/storage_management_log.json` — 5 entries (2 completed, 1 in_progress, 1 failed, 1 pending)
- [x] `tests/test_storage_management_log.py` — 22 tests
- [x] `health_check_log`, `license_management_log`, `storage_management_log` added to `SCHEMA_FILENAMES` (total schemas: 160)
- [x] `techno-search health-check-summary`, `techno-search license-management-summary`, `techno-search storage-management-summary` CLI commands
- [x] `validate-all` gates: `health_check_entry_count >= 1`, `license_management_entry_count >= 1`, `storage_management_entry_count >= 1`
- [x] `validation-summary` fields: `health_check_entry_count`, `health_check_passed_count`, `license_management_entry_count`, `license_management_active_count`, `storage_management_entry_count`, `storage_management_completed_count`
- [x] DECISION-095: Health Check Log, License Management Log, And Storage Management Log Complete Milestone 48

# Milestone 50 — SQLite Operational Log Registry Consistency

- [x] `src/techno_search/sqlite_operational_log_registry.py` — registry consistency checks for operational log modules, schemas, fixtures, CLI summary commands, `SCHEMA_FILENAMES` keys, and explicit top-level SQLite production policy visibility
- [x] `schemas/sqlite_operational_log_registry.schema.json`
- [x] `tests/fixtures/sqlite_operational_log_registry.json` — expected registry for 74 operational log families with SQLite policy `top_level_sqlite_required_before_production`
- [x] `tests/test_sqlite_operational_log_registry.py` — guardrail tests for missing modules, CLI commands, schema keys, and SQLite policy drift
- [x] `techno-search sqlite-operational-log-registry-summary` CLI command
- [x] `sqlite_operational_log_registry` added to `SCHEMA_FILENAMES` (total schemas: 164)
- [x] `validate-all` gate: SQLite operational log registry check must pass
- [x] `validation-summary` fields: `sqlite_operational_log_registry_ok`, `sqlite_operational_log_registered_count`, `sqlite_operational_log_missing_cli_command_count`, `sqlite_operational_log_missing_sqlite_policy_count`, `sqlite_operational_log_sqlite_required_before_production_count`
- [x] DECISION-097: Operational Log Registry Must Keep SQLite Policy Visible

# Milestone 51 — SQLite Operational Log Adapter Plan

- [x] `src/techno_search/sqlite_operational_log_adapter_plan.py` — non-destructive SQLite adapter phase planning for all registry-backed operational log families
- [x] `schemas/sqlite_operational_log_adapter_plan.schema.json`
- [x] `tests/fixtures/sqlite_operational_log_adapter_plan.json` — expected five-phase adapter plan with zero mutation allowance
- [x] `tests/test_sqlite_operational_log_adapter_plan.py` — guardrail tests for unassigned logs, policy mismatch, count drift, and mutation drift
- [x] `techno-search sqlite-operational-log-adapter-plan-summary` CLI command
- [x] `sqlite_operational_log_adapter_plan` added to `SCHEMA_FILENAMES` (total schemas: 165)
- [x] `validate-all` gate: SQLite operational log adapter plan check must pass
- [x] `validation-summary` fields: `sqlite_operational_log_adapter_plan_ok`, `sqlite_operational_log_adapter_planned_count`, `sqlite_operational_log_adapter_phase_count`, `sqlite_operational_log_adapter_unassigned_count`, `sqlite_operational_log_adapter_policy_mismatch_count`, `sqlite_operational_log_adapter_mutation_allowed`
- [x] DECISION-098: Operational Log SQLite Migration Must Be Planned Before Adapters Mutate Databases

# Milestone 52 — SQLite Operational Log Adapter Contract

- [x] `src/techno_search/sqlite_operational_log_adapter_contract.py` — non-mutating SQLite adapter contract checks for planned phase tables, required provenance columns, phase counts, and disabled mutation
- [x] `schemas/sqlite_operational_log_adapter_contract.schema.json`
- [x] `tests/fixtures/sqlite_operational_log_adapter_contract.json` — expected five-table contract with required provenance columns and zero mutation allowance
- [x] `tests/test_sqlite_operational_log_adapter_contract.py` — guardrail tests for adapter-plan drift, missing table plans, missing required columns, count mismatch, and mutation drift
- [x] `techno-search sqlite-operational-log-adapter-contract-summary` CLI command
- [x] `sqlite_operational_log_adapter_contract` added to `SCHEMA_FILENAMES` (total schemas: 166)
- [x] `validate-all` gate: SQLite operational log adapter contract check must pass
- [x] `validation-summary` fields: `sqlite_operational_log_adapter_contract_ok`, `sqlite_operational_log_adapter_contract_phase_count`, `sqlite_operational_log_adapter_contract_missing_table_count`, `sqlite_operational_log_adapter_contract_missing_column_count`, `sqlite_operational_log_adapter_contract_phase_mismatch_count`, `sqlite_operational_log_adapter_contract_mutation_allowed`
- [x] DECISION-099: Operational Log SQLite Adapters Must Keep Non-Mutating Table Contracts Before Implementation

# Milestone 53 — SQLite Operational Log Adapter DDL Preview

- [x] `src/techno_search/sqlite_operational_log_adapter_ddl_preview.py` — preview-only SQLite DDL renderer for future operational log phase tables
- [x] `schemas/sqlite_operational_log_adapter_ddl_preview.schema.json`
- [x] `tests/fixtures/sqlite_operational_log_adapter_ddl_preview.json` — expected statement count, required SQL clauses, and zero execution allowance
- [x] `tests/test_sqlite_operational_log_adapter_ddl_preview.py` — guardrail tests for contract drift, statement-count drift, missing SQL clauses, and execution drift
- [x] `techno-search sqlite-operational-log-adapter-ddl-preview-summary` CLI command
- [x] `sqlite_operational_log_adapter_ddl_preview` added to `SCHEMA_FILENAMES` (total schemas: 167)
- [x] `validate-all` gate: SQLite operational log adapter DDL preview check must pass
- [x] `validation-summary` fields: `sqlite_operational_log_adapter_ddl_preview_ok`, `sqlite_operational_log_adapter_ddl_statement_count`, `sqlite_operational_log_adapter_ddl_missing_clause_count`, `sqlite_operational_log_adapter_ddl_execution_allowed`
- [x] DECISION-100: Operational Log SQLite DDL Must Remain Preview-Only Before Adapter Execution

# Milestone 54 — SQLite Operational Log Adapter Row Preview

- [x] `src/techno_search/sqlite_operational_log_adapter_row_preview.py` — preview-only SQLite row-payload renderer for future operational log adapter inserts
- [x] `schemas/sqlite_operational_log_adapter_row_preview.schema.json`
- [x] `tests/fixtures/sqlite_operational_log_adapter_row_preview.json` — expected row count, phase count, required row fields, JSON payload requirement, and zero execution allowance
- [x] `tests/test_sqlite_operational_log_adapter_row_preview.py` — guardrail tests for contract drift, plan drift, row-count drift, missing fields, missing table mappings, and execution drift
- [x] `techno-search sqlite-operational-log-adapter-row-preview-summary` CLI command
- [x] `sqlite_operational_log_adapter_row_preview` added to `SCHEMA_FILENAMES` (total schemas: 168)
- [x] `validate-all` gate: SQLite operational log adapter row preview check must pass
- [x] `validation-summary` fields: `sqlite_operational_log_adapter_row_preview_ok`, `sqlite_operational_log_adapter_row_count`, `sqlite_operational_log_adapter_row_phase_count`, `sqlite_operational_log_adapter_row_missing_field_count`, `sqlite_operational_log_adapter_row_execution_allowed`
- [x] DECISION-101: Operational Log SQLite Row Payloads Must Remain Preview-Only Before Adapter Execution

# Milestone 55 — SQLite Operational Log Adapter Insert Preview

- [x] `src/techno_search/sqlite_operational_log_adapter_insert_preview.py` — preview-only SQLite insert renderer for future operational log adapter writes
- [x] `schemas/sqlite_operational_log_adapter_insert_preview.schema.json`
- [x] `tests/fixtures/sqlite_operational_log_adapter_insert_preview.json` — expected insert count, phase count, bound value count, parameter placeholder, and zero execution allowance
- [x] `tests/test_sqlite_operational_log_adapter_insert_preview.py` — guardrail tests for row-preview drift, insert-count drift, missing table names, missing bound values, value-count mismatch, placeholder mismatch, and execution drift
- [x] `techno-search sqlite-operational-log-adapter-insert-preview-summary` CLI command
- [x] `sqlite_operational_log_adapter_insert_preview` added to `SCHEMA_FILENAMES` (total schemas: 169)
- [x] `validate-all` gate: SQLite operational log adapter insert preview check must pass
- [x] `validation-summary` fields: `sqlite_operational_log_adapter_insert_preview_ok`, `sqlite_operational_log_adapter_insert_count`, `sqlite_operational_log_adapter_insert_phase_count`, `sqlite_operational_log_adapter_insert_value_mismatch_count`, `sqlite_operational_log_adapter_insert_execution_allowed`
- [x] DECISION-102: Operational Log SQLite Inserts Must Remain Preview-Only Before Adapter Execution

# Milestone 56 — SQLite Operational Log Adapter Execution Preview

- [x] `src/techno_search/sqlite_operational_log_adapter_execution_preview.py` — preview-only SQLite transaction-order renderer for future operational log adapter writes
- [x] `schemas/sqlite_operational_log_adapter_execution_preview.schema.json`
- [x] `tests/fixtures/sqlite_operational_log_adapter_execution_preview.json` — expected insert count, phase count, transaction operation count, transaction markers, and zero execution/mutation allowance
- [x] `tests/test_sqlite_operational_log_adapter_execution_preview.py` — guardrail tests for insert-preview drift, count drift, missing transaction markers, phase table ambiguity, execution drift, and mutation drift
- [x] `techno-search sqlite-operational-log-adapter-execution-preview-summary` CLI command
- [x] `sqlite_operational_log_adapter_execution_preview` added to `SCHEMA_FILENAMES` (total schemas: 170)
- [x] `validate-all` gate: SQLite operational log adapter execution preview check must pass
- [x] `validation-summary` fields: `sqlite_operational_log_adapter_execution_preview_ok`, `sqlite_operational_log_adapter_execution_operation_count`, `sqlite_operational_log_adapter_execution_phase_count`, `sqlite_operational_log_adapter_execution_allowed`, `sqlite_operational_log_adapter_execution_mutation_allowed`
- [x] DECISION-103: Operational Log SQLite Execution Ordering Must Remain Preview-Only Before Adapter Execution

# Milestone 57 — SQLite Operational Log Adapter Dry-Run Manifest

- [x] `src/techno_search/sqlite_operational_log_adapter_dry_run_manifest.py` — preview-only SQLite adapter dry-run manifest that reconciles DDL and execution previews
- [x] `schemas/sqlite_operational_log_adapter_dry_run_manifest.schema.json`
- [x] `tests/fixtures/sqlite_operational_log_adapter_dry_run_manifest.json` — expected DDL count, insert count, phase count, execution operation count, preview-only status, and disabled database-open/execution/mutation/authorization flags
- [x] `tests/test_sqlite_operational_log_adapter_dry_run_manifest.py` — guardrail tests for upstream preview drift, count drift, phase alignment drift, preview status drift, database-open drift, execution drift, mutation drift, live-data drift, and external-submission drift
- [x] `techno-search sqlite-operational-log-adapter-dry-run-manifest-summary` CLI command
- [x] `sqlite_operational_log_adapter_dry_run_manifest` added to `SCHEMA_FILENAMES` (total schemas: 171)
- [x] `validate-all` gate: SQLite operational log adapter dry-run manifest check must pass
- [x] `validation-summary` fields: `sqlite_operational_log_adapter_dry_run_manifest_ok`, `sqlite_operational_log_adapter_dry_run_manifest_status`, `sqlite_operational_log_adapter_dry_run_phase_count`, `sqlite_operational_log_adapter_dry_run_phase_mismatch_count`, `sqlite_operational_log_adapter_dry_run_database_open_allowed`, `sqlite_operational_log_adapter_dry_run_execution_allowed`, `sqlite_operational_log_adapter_dry_run_mutation_allowed`, `sqlite_operational_log_adapter_dry_run_live_data_authorized`, `sqlite_operational_log_adapter_dry_run_external_submission_authorized`
- [x] DECISION-104: Operational Log SQLite Dry-Run Manifests Must Reconcile Previews Before Adapter Execution

# Milestone 58 — SQLite Operational Log Adapter Readiness Preflight

- [x] `src/techno_search/sqlite_operational_log_adapter_readiness_preflight.py` — non-mutating readiness preflight that reconciles registry, plan, contract, preview, and dry-run gates
- [x] `schemas/sqlite_operational_log_adapter_readiness_preflight.schema.json`
- [x] `tests/fixtures/sqlite_operational_log_adapter_readiness_preflight.json` — expected registry count, plan count, phase count, DDL count, row count, insert count, execution operation count, schema count, preflight-only status, and disabled database-open/execution/mutation/authorization flags
- [x] `tests/test_sqlite_operational_log_adapter_readiness_preflight.py` — guardrail tests for upstream gate drift, count drift, dry-run status drift, preflight status drift, database-open drift, execution drift, mutation drift, live-data drift, and external-submission drift
- [x] `techno-search sqlite-operational-log-adapter-readiness-preflight-summary` CLI command
- [x] `sqlite_operational_log_adapter_readiness_preflight` added to `SCHEMA_FILENAMES` (total schemas: 172)
- [x] `validate-all` gate: SQLite operational log adapter readiness preflight check must pass
- [x] `validation-summary` fields: `sqlite_operational_log_adapter_readiness_preflight_ok`, `sqlite_operational_log_adapter_readiness_preflight_status`, `sqlite_operational_log_adapter_readiness_preflight_failed_gate_count`, `sqlite_operational_log_adapter_readiness_preflight_schema_count`, `sqlite_operational_log_adapter_readiness_preflight_database_open_allowed`, `sqlite_operational_log_adapter_readiness_preflight_execution_allowed`, `sqlite_operational_log_adapter_readiness_preflight_mutation_allowed`, `sqlite_operational_log_adapter_readiness_preflight_live_data_authorized`, `sqlite_operational_log_adapter_readiness_preflight_external_submission_authorized`
- [x] DECISION-105: Operational Log SQLite Adapter Readiness Must Remain Preflight-Only Before Execution

# Milestone 59 — SQLite Operational Log Adapter Authorization Gate

- [x] `src/techno_search/sqlite_operational_log_adapter_authorization_gate.py` — disabled authorization gate that keeps future adapter implementation and execution blocked pending explicit approval
- [x] `schemas/sqlite_operational_log_adapter_authorization_gate.schema.json`
- [x] `tests/fixtures/sqlite_operational_log_adapter_authorization_gate.json` — expected readiness-preflight count alignment, authorization status, schema count, and disabled implementation/database-open/execution/fixture-migration/mutation/authorization flags
- [x] `tests/test_sqlite_operational_log_adapter_authorization_gate.py` — guardrail tests for readiness-preflight drift, count drift, authorization status drift, adapter-implementation drift, database-open drift, execution drift, fixture-migration drift, mutation drift, live-data drift, external-submission drift, and upstream safety flag drift
- [x] `techno-search sqlite-operational-log-adapter-authorization-gate-summary` CLI command
- [x] `sqlite_operational_log_adapter_authorization_gate` added to `SCHEMA_FILENAMES` (total schemas: 173)
- [x] `validate-all` gate: SQLite operational log adapter authorization gate check must pass
- [x] `validation-summary` fields: `sqlite_operational_log_adapter_authorization_gate_ok`, `sqlite_operational_log_adapter_authorization_status`, `sqlite_operational_log_adapter_authorization_gate_schema_count`, `sqlite_operational_log_adapter_authorization_gate_adapter_implementation_allowed`, `sqlite_operational_log_adapter_authorization_gate_database_open_allowed`, `sqlite_operational_log_adapter_authorization_gate_execution_allowed`, `sqlite_operational_log_adapter_authorization_gate_fixture_migration_allowed`, `sqlite_operational_log_adapter_authorization_gate_mutation_allowed`, `sqlite_operational_log_adapter_authorization_gate_live_data_authorized`, `sqlite_operational_log_adapter_authorization_gate_external_submission_authorized`
- [x] DECISION-106: Operational Log SQLite Adapter Authorization Must Remain Blocked Before Execution

# Milestone 60 — Project-Scoped MCP Bootstrap

- [x] `docs/Technosignatures_MCP_BOOTSTRAP.md` fully read and applied as the MCP rollout source of truth
- [x] `.mcp.json` — project-scoped Claude Code MCP config with project files, read-only git inspection, and fixed validation guard servers
- [x] `.codex/config.toml` — project-scoped Codex MCP config pointing to the same local stdio servers
- [x] `src/techno_search/mcp_servers.py` — stdlib-only MCP stdio servers for repository file inspection, read-only git commands, and fixed `.venv` validation commands
- [x] `tests/test_mcp_bootstrap.py` — guardrail tests for denied paths, fixed command allowlists, no arbitrary shell tools, no secrets, and no live-provider defaults
- [x] MCP bootstrap keeps `.venv`, `.git`, caches, artifacts, top-level SQLite logs, and bulk data paths inaccessible through project file tools
- [x] MCP bootstrap does not enable live provider access, external submission, candidate score changes, pathway changes, or report interpretation changes
- [x] DECISION-107: Project-Scoped MCP Bootstrap Must Stay Conservative And Local

# Milestone 61 — MCP Bootstrap Consistency Gate

- [x] `src/techno_search/mcp_bootstrap_consistency.py` — local MCP config drift gate for `.mcp.json` and `.codex/config.toml`
- [x] `schemas/mcp_bootstrap_consistency.schema.json`
- [x] `tests/fixtures/mcp_bootstrap_consistency.json` — expected project-scoped server names, server kinds, command, and args prefix
- [x] `tests/test_mcp_bootstrap_consistency.py` — guardrail tests for command drift, server-kind drift, forbidden token drift, arbitrary shell drift, live-provider drift, and external-submission drift
- [x] `techno-search mcp-bootstrap-consistency-summary` CLI command
- [x] `mcp_bootstrap_consistency` added to `SCHEMA_FILENAMES` (total schemas: 174)
- [x] `validate-all` gate: MCP bootstrap consistency check must pass
- [x] `validation-summary` fields: `mcp_bootstrap_consistency_ok`, `mcp_bootstrap_consistency_issue_count`, `mcp_bootstrap_claude_server_count`, `mcp_bootstrap_codex_server_count`, `mcp_bootstrap_forbidden_token_count`, `mcp_bootstrap_arbitrary_shell_enabled`, `mcp_bootstrap_live_provider_enabled`, `mcp_bootstrap_external_submission_enabled`
- [x] DECISION-108: MCP Bootstrap Config Must Remain Guarded By Local Consistency Checks

# Milestone 62 — MCP Server Policy Gate

**Status**: complete

## Tasks

- [x] MCP server policy fixture and JSON schema added
- [x] `src/techno_search/mcp_server_policy.py` local implementation drift summary added
- [x] `techno-search mcp-server-policy-summary` CLI command
- [x] `mcp_server_policy` added to `SCHEMA_FILENAMES` (total schemas: 175)
- [x] `validate-all` gate: MCP server policy check must pass
- [x] `validation-summary` fields: `mcp_server_policy_ok`, `mcp_server_policy_issue_count`, `mcp_server_policy_git_read_command_count`, `mcp_server_policy_techno_guard_command_count`, `mcp_server_policy_forbidden_command_token_count`, `mcp_server_policy_mutating_git_command_count`, `mcp_server_policy_venv_enforced`, `mcp_server_policy_arbitrary_shell_enabled`, `mcp_server_policy_live_provider_enabled`, `mcp_server_policy_external_submission_enabled`
- [x] DECISION-109: MCP Server Implementation Must Stay Allowlisted And Local

## Done When

- MCP server tool names remain allowlisted
- Git inspection commands remain fixed and read-only
- Local validation commands remain fixed and `.venv`-scoped
- Private/cache/log/bulk-data paths remain denied
- Arbitrary shell, live-provider, and external-submission defaults remain absent

# Milestone 63 — Data Transfer Log, System Diagnostics Log, And Resource Allocation Log

**Status**: complete

## Tasks

- [x] `src/techno_search/data_transfer_log.py` — operational provenance records for data transfer and synchronization events; transfer_kinds: bulk_export, emergency_transfer, inbound_transfer, internal_sync, outbound_transfer; statuses: cancelled, completed, failed, in_progress
- [x] `schemas/data_transfer_log.schema.json`
- [x] `tests/fixtures/data_transfer_log.json` — 5 entries (2 completed, 1 in_progress, 1 failed, 1 cancelled)
- [x] `tests/test_data_transfer_log.py` — 22 tests
- [x] `src/techno_search/system_diagnostics_log.py` — operational provenance records for system diagnostic check events; diagnostics_kinds: hardware_check, network_check, performance_check, software_check, storage_check; statuses: failed, not_run, passed, warning
- [x] `schemas/system_diagnostics_log.schema.json`
- [x] `tests/fixtures/system_diagnostics_log.json` — 5 entries (2 passed, 1 warning, 1 failed, 1 not_run)
- [x] `tests/test_system_diagnostics_log.py` — 22 tests
- [x] `src/techno_search/resource_allocation_log.py` — operational provenance records for compute and facility resource allocation events; allocation_kinds: compute_allocation, memory_allocation, network_allocation, personnel_allocation, storage_allocation; statuses: allocated, deallocated, exhausted, pending
- [x] `schemas/resource_allocation_log.schema.json`
- [x] `tests/fixtures/resource_allocation_log.json` — 5 entries (2 allocated, 1 deallocated, 1 pending, 1 exhausted)
- [x] `tests/test_resource_allocation_log.py` — 22 tests
- [x] `system_diagnostics_log`, `resource_allocation_log` added to `SCHEMA_FILENAMES` (total schemas: 177)
- [x] `techno-search system-diagnostics-summary`, `techno-search resource-allocation-summary` CLI commands
- [x] `validate-all` gates: `system_diagnostics_entry_count >= 1`, `resource_allocation_entry_count >= 1`
- [x] `validation-summary` fields: `system_diagnostics_entry_count`, `system_diagnostics_passed_count`, `resource_allocation_entry_count`, `resource_allocation_allocated_count`
- [x] DECISION-110: Data Transfer Log, System Diagnostics Log, And Resource Allocation Log Complete Milestone 63

## Done When

- Data transfer entries are operational provenance records
- System diagnostics entries are operational provenance records
- Resource allocation entries are operational provenance records
- No entry modifies candidate scores or pathway routing
- No entry authorizes external submission or constitutes a detection claim

# Milestone 64 — Access Control Log, Change Management Log, And Incident Log

**Status**: complete

## Tasks

- [x] `src/techno_search/access_control_log.py` — operational provenance records for access control events; access_kinds: access_grant, access_revocation, authentication_attempt, authorization_check, permission_change; statuses: allowed, blocked, expired, pending
- [x] `schemas/access_control_log.schema.json`
- [x] `tests/fixtures/access_control_log.json` — 5 entries (2 allowed, 1 blocked, 1 expired, 1 pending)
- [x] `tests/test_access_control_log.py` — 22 tests
- [x] `src/techno_search/change_management_log.py` — operational provenance records for change management events; change_kinds: configuration_change, emergency_change, planned_change, rollback, service_change; statuses: approved, completed, pending, rejected
- [x] `schemas/change_management_log.schema.json` (pre-existing)
- [x] `tests/fixtures/change_management_log.json` — 5 entries (2 completed, 1 approved, 1 pending, 1 rejected)
- [x] `tests/test_change_management_log.py` — 22 tests
- [x] `src/techno_search/incident_log.py` — operational provenance records for incident events; incident_kinds: data_integrity_incident, hardware_incident, network_incident, security_incident, software_incident; statuses: closed, escalated, open, under_investigation
- [x] `schemas/incident_log.schema.json`
- [x] `tests/fixtures/incident_log.json` — 5 entries (2 closed, 1 open, 1 under_investigation, 1 escalated)
- [x] `tests/test_incident_log.py` — 22 tests
- [x] `access_control_log`, `incident_log` added to `SCHEMA_FILENAMES` (total schemas: 179)
- [x] `techno-search access-control-summary`, `techno-search change-management-summary`, `techno-search incident-summary` CLI commands
- [x] `validate-all` gates: `access_control_entry_count >= 1`, `change_mgmt_entry_count >= 1`, `incident_entry_count >= 1`
- [x] `validation-summary` fields: `access_control_entry_count`, `access_control_allowed_count`, `incident_entry_count`, `incident_open_count`
- [x] DECISION-111: Access Control Log, Change Management Log, And Incident Log Complete Milestone 64

## Done When

- Access control entries are operational provenance records
- Change management entries are operational provenance records
- Incident entries are operational provenance records
- No entry modifies candidate scores or pathway routing
- No entry authorizes external submission or constitutes a detection claim

# Milestone 65 — Patch Management Log, Vulnerability Scan Log, And Compliance Audit Log

Status: Complete

Added patch_management_log, vulnerability_scan_log, compliance_audit_log.
Total schemas: 182.

- Patch management entries are operational provenance records
- Vulnerability scan entries are operational provenance records
- Compliance audit entries are operational provenance records
- No entry modifies candidate scores or pathway routing
- No entry authorizes external submission or constitutes a detection claim

# Milestone 66 — Disaster Recovery Log, Service Level Log, And Asset Management Log

Status: Complete

Added disaster_recovery_log, service_level_log, asset_management_log.
Total schemas: 185.

## Done When

- Disaster recovery entries are operational provenance records
- Service level entries are operational provenance records
- Asset management entries are operational provenance records
- No entry modifies candidate scores or pathway routing
- No entry authorizes external submission or constitutes a detection claim

---

# Milestone 67 — Network Monitoring Log, Identity Management Log, And Certificate Management Log

Added network_monitoring_log, identity_management_log, certificate_management_log.
Total schemas: 188.

## Done When

- Network monitoring entries are operational provenance records
- Identity management entries are operational provenance records
- Certificate management entries are operational provenance records
- No entry modifies candidate scores or pathway routing
- No entry authorizes external submission or constitutes a detection claim
