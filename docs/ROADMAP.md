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

- [ ] Unified pipeline configuration module tying scoring config, model serving, and track configs
- [ ] Pipeline configuration schema and JSON schema artifact
- [ ] `pipeline-config-summary` CLI command
- [ ] End-to-end pipeline smoke test: candidate → scoring → serving → audit → handoff
- [ ] Submission readiness checker: gate ensuring all required provenance fields are present before any external handoff is considered
- [ ] `submission-readiness-summary` CLI command
- [ ] Pipeline integration tests covering multi-step candidate flow
- [ ] DECISION-047: Pipeline Integration And Submission Readiness Checks Gate External Handoff

## Done When

- A single candidate can flow through scoring, model serving, audit logging, and operator handoff with full provenance recorded
- Submission readiness check blocks any pathway missing required provenance
- All integration tests pass without network access
