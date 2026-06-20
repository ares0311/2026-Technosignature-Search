# Changelog

All notable changes to the Technosignature Search pipeline are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Scientific guardrail: no entry in this changelog constitutes a detection claim
or authorizes external submission.

---

## [Unreleased]

---

## [v0.79.0] — 2026-06-20 (Milestone 79 — Production Scan Hardening And Artifact Hygiene)

### Added
- Triage label completeness gate: 6th triage note (`triage-006`, label `defer`) added
  to fixture; `validate-all` `triage_label_completeness.all_labels_covered` now `true`
- Batch turboSETI script for extended BL corpus (`scripts/run_turboseti_on_extended_corpus.sh`):
  processes all HDF5 files under `data/extended_corpus/` (HIP66704, HIP74981, HIP82860) idempotently
- Extended corpus runbook update: `docs/PRODUCTION_SCAN_RUNBOOK.md` documents
  multi-target `.dat` acquisition workflow for the five non-Cygnus GBT targets

### Fixed
- Non-deterministic turboSETI `.dat` discovery in `download_bl_hits.sh` and
  `fetch_bl_alternative.sh` replaced with deterministic H5-stem prediction (DECISION-142)
- Race condition and type hint error in `production_scan.py` multi-target path
- HDBSCAN `copy=` FutureWarning silenced in `globular_filter.py`
- `workers` parameter wired correctly through `run_multi_target_scan()` CLI path

---

## [v0.78.0] — 2026-06-19 (Milestone 78 — Production Scan UX And History)

### Added
- Production scan history: atomic NDJSON scan log (`results/scan_history.ndjson`);
  `prod-target-queue`, `prod-record-scan`, `scan-history-summary` CLI commands (DECISION-141)
- History-aware target queue: base priority 0.50 with +0.08 first-scan boost and
  −0.04 per-scan penalty; `parent_run_id` chain for re-scan linking
- `scripts/run_production_scan.sh` fully rewritten: acquires new `.dat` files via
  `prod-target-queue`, runs continuous `while true` scan loop with SIGINT trap,
  records each scan result, displays ranked queue with rationale
- `docs/PRODUCTION_SCAN_RUNBOOK.md`: five rules of correct production scan orchestration
- `prod-scan` and `prod-file-scan` fail closed when no candidate manifests exist;
  zero-candidate runs require explicit `--allow-empty` (DECISION-140)
- Model generalizability suite (DECISION-133): extended GBT corpus download script;
  MeerKAT BLUSE 2M-hit ingest; setigen injection-recovery grid; cross-band feature
  normalization (`normalize_drift_hz_s_per_ghz`, `is_earth_drift_consistent`,
  `relative_snr`, `on_off_consistency_score`); GLOBULAR density pre-filter (HDBSCAN,
  13 features, ~93% FP reduction); semi-supervised anomaly scorer (PCA + IsolationForest)
- AI hardening evidence gate (DECISION-134/135/138/139) closed for local citizen-science
  operations: setigen grid in real Voyager 1 GBT noise produced 75/75 recovered
  injections, 256 valid turboSETI hit rows, and three recorded independent method-family
  reviews; production promotion is local citizen-science operations only

---

## [v0.77.0] — 2026-06-16 (Milestone 77 — Escalation Gate Hardening)

### Added
- External submission protocol (`docs/EXTERNAL_SUBMISSION_PROTOCOL.md`) with 7
  preconditions (P1–P7); DECISION-132
- Hardened escalation gate: `escalation_gate_check()` now returns structured dict;
  adds `multi_epoch_persistence_score > 0` as third gate requirement (single-epoch
  candidates cannot pass); `ESCALATION_MULTI_EPOCH_GATE` constant
- `negative_result_summary()` for multi-target scans with 0 gate-passing candidates;
  `negative-result-summary` CLI command; `scan_id` (UUID) added to `MultiTargetScanResult`

---

## [v0.76.0] — 2026-06-13 (Milestone 76)

### Added
- Multi-target scan orchestration: `run_multi_target_scan()` with per-target result
  tracking; `MultiTargetScanResult` dataclass; `scan-summary` CLI
- Cross-target RFI suppression: `flag_cross_target_rfi()`; signals in ≥2 independent
  targets flagged as likely terrestrial; `cross-target-rfi-summary` CLI
- Candidate escalation gate: `escalation_gate_check()` + `create_escalation_record()`
  with SHA-256 reproduction checklist; `escalation-gate-check` CLI
- Cross-store position deduplication: `find_cross_store_matches()` + 10 arcsec tolerance
- Gaia DR3 scan workflow: `query_gaia_for_targets()`; guarded behind live-data opt-in
- Weekly automated scan schedule: `.github/workflows/weekly_scan.yml` (Sunday 02:00 UTC)
- Calibration transfer protocol: `docs/CALIBRATION_TRANSFER_PROTOCOL.md`
- Production scan guide: `docs/PRODUCTION_SCAN_GUIDE.md`

## [v0.75.0] — 2026-06-12

### Added
- Operator review dashboard: `review_dashboard_summary()`; `techno-search review-dashboard`
  CLI with exit code 1 on `needs_attention`; closes Tier 3 operator UI gap
- Data release snapshot: `data_release_snapshot_summary()`, `snapshot_from_batch_manifest()`,
  `compare_snapshots()`; deterministic SHA-256 pathway assignment hash;
  `data-release-snapshot-summary` / `compare-data-releases` CLI; closes Tier 3
  reproducibility gap (DECISION-131)

## [v0.74.0] — 2026-06-12

### Added
- Learned scoring model v1: logistic regression on 124 real GBT/HIP99427 citizen-science
  labels; 3-class pathway classifier; 3-fold stratified CV accuracy 99.19%;
  `real-labels-model-summary` CLI; `validate-all` gate; closes final Tier 2 gap (DECISION-130)
- Independent reproduction: `validate-all` confirmed passing in a separate
  citizen-science environment (2026-06-12)

## [v0.73.0] — 2026-06-12

### Added
- Calibrated scoring thresholds from real GBT noise data: calibration gate passed
  `calibration_ready: true`; 213 hits, 5 cadences, 5 targets, 2 epochs;
  noise_floor_snr=42.4, follow_up_snr=54.8, high_interest_snr=118.3 (DECISION-127)
- Multi-epoch hit-table comparison: `compare_epochs()`; persistence scores;
  `multi-epoch-compare` CLI (DECISION-129)
- Parallel candidate scoring: `score_candidates_parallel()` with `ProcessPoolExecutor`
- SQLite candidate store: `CandidateStore`; `candidate-store-init/summary/list` CLI
- Multi-epoch pipeline injection: `epoch_dat_files` wired through `run_pipeline`
- SIMBAD known-object injection into candidate features
- Gaia/WISE cross-match at scale wired into `_build_infrared_candidate`

## [v0.72.0] — 2026-06-12

### Added
- GBT provisional RFI catalog operator sign-off: 15 entries reviewed; admission gate
  cleared; ready_for_local_fixture (DECISION-126)
- Calibration corpus download manifest: 5 BL targets; admission gate; pipeline script;
  operator review protocol (DECISION-125)
- Unit-safe, provenance-aware real-noise calibration preflight
- Cadence/target/epoch, dominance, bootstrap, leave-one-cadence-out gates
- Scoring model v1 with calibrated SNR tiers and drift neutralization:
  77.42% diagnostic agreement (96/124) (DECISION-128)

## [v0.71.0] — 2026-06-11

### Added
- Real HIP99427 cadence label set (124 evidence groups)
- Independent-method citizen-science label audit
- Public reproducibility review package
- Current scoring model evaluated against real labels: 54.03% diagnostic agreement

## [v0.70.0] — 2026-06-10

### Added
- Checksum-verified HIP99427 GBT ABACAD cadence ingestion (DECISION-122)
- Real turboSETI processing with explicit ON/OFF evidence
- Frequency-matched OFF-target rejection guard validated against real cadence data
- GBT provisional RFI catalog: 15 bands; ITU/GPS/ICAO/FCC citations (DECISION-124)

## [v0.69.0] — 2026-06-09

### Added
- Voyager 1 GBT turboSETI test H5 downloaded and scored end-to-end (3 real hits)
- Resumable parallel BL data download scripts (16-thread, LFS + SSL)

## [v0.68.0] — 2026-06-08

### Added
- Live catalog clients: Gaia TAP, SIMBAD — with `TECHNO_SEARCH_ENABLE_LIVE_DATA=1` opt-in
- Real-observation artifact audit and human-approval gate
- Multi-target citizen-science label combination and combined model training

## [v0.67.0] — 2026-06-07

### Added
- Project-scoped MCP bootstrap configuration (DECISION-107)
- MCP bootstrap consistency gate (DECISION-108)
- MCP server policy gate (DECISION-109)
- SQLite operational log adapter authorization gate (DECISION-106)

## [v0.66.0] — 2026-06-06

### Added
- SQLite operational log adapter plan, contract, DDL preview, row preview, insert preview,
  execution preview, dry-run manifest, readiness preflight gates (DECISION-098–105)
- SQLite operational log registry consistency gate (DECISION-097)

## [v0.65.0] — 2026-06-05

### Added
- Operational log system: 86 log types covering all pipeline stages and operations
- Top-level SQLite log consistency gates (DECISION-084)
- Production blocker visibility consistency gates (DECISION-085)
- Operations blocker-progress consistency gates (DECISION-083)

## [v0.27.0] — 2026-05-20

### Added
- End-to-end pipeline runner (CSV → scored report)
- Data quality validator (`validate-input`)
- Direct `run-pipeline` CLI with validation-first execution
- Real hit-table CSV reader (turboSETI format)
- Real Gaia+WISE catalog CSV reader (IRSA TAP format)
- CI workflow (GitHub Actions)
- Labeled candidate dataset v0 (10 synthetic entries)
- Scoring model evaluation against labeled dataset
- Production readiness assessment (DECISION-074)

## [v0.10.0] — 2026-05-10

### Added
- Synthetic scoring pipeline (radio, infrared, anomaly tracks)
- Candidate report generation (Markdown, JSON, manifest)
- Calibration fixture set (15 false-positive classes)
- Score regression + determinism checks
- Interpretable baseline classifier
- 109+ JSON schema artifacts
- Local validation gate (`validate-all`)
- Provenance, audit trail, lifecycle tracking

---

*This changelog covers engineering milestones. It is not a record of candidate
signals or detection claims. No entry implies a confirmed technosignature.*
