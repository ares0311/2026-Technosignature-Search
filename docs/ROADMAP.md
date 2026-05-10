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

## Candidate Methods

- CNNs for radio waterfall/image morphology, survey-image artifacts, and spatial context
- Transformers for sequential radio features, multi-epoch catalog histories, and multimodal candidate packets
- Self-supervised or contrastive learning for representation learning on large unlabeled astronomical datasets
- Foundation-model-style embeddings where they improve retrieval, clustering, or human review triage
- Hybrid models that combine learned features with explicit physical, instrumental, and catalog-quality features

## Guardrails

- Learned models must not replace provenance, negative evidence, blocking issues, or pathway logic.
- Black-box scores must be calibrated against synthetic injections, known contaminants, known artifacts, and human-reviewed labels.
- AI outputs should be treated as decision-support signals, not discovery claims.
- Model versions, training data, features, prompts where applicable, and evaluation metrics must be recorded.

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
