# Production Readiness Assessment

**Last updated:** 2026-06-29
**Current milestone:** 79 (Production Scan Hardening And Artifact Hygiene)
**Current phase:** Phase 0 — Strip & Fix (multi-modal realignment)
**Current app version:** 1.1.0

---

## Mission

Search publicly available multi-modal astronomical data for signals that cannot
be explained by natural phenomena. Use rigorous, literature-grounded methods
consistent with publication-grade science. Report surviving candidates for
expert review. Never claim detection without external validation.

**Review chain:**
1. Automated multi-modal pipeline (radio + photometry + IR + spectroscopy)
2. Adversarial review agent (purpose-built to refute each specific candidate)
3. Third-party expert review (Breakthrough Listen, Penn State SETI, Galileo
   Project, IAU SETI Committee, per IAU post-detection protocol)

---

## What Is Scientifically Aligned (Keep)

These modules do real science or directly support it:

| Capability | Module / Script | Status |
|---|---|---|
| Radio hit-table reader (turboSETI format) | `radio/hit_table_reader.py` | ✅ Keep |
| Data quality validator (turboSETI `.dat` files) | `data_quality.py` | ✅ Keep |
| Pipeline runner (`.dat` → candidate manifest) | `pipeline_runner.py` | ✅ Keep |
| ON/OFF cadence RFI rejection | `pipeline_runner.py` (partial) | ⚠️ Needs hardening |
| Cross-band feature normalization | `radio/cross_band_features.py` | ✅ Keep |
| GLOBULAR density pre-filter (HDBSCAN) | `globular_filter.py` | ✅ Keep |
| Semi-supervised anomaly scorer (IsolationForest) | `semisupervised_scorer.py` | ⚠️ Unfitted — needs real MeerKAT training |
| Multi-epoch hit comparison | `pipeline_runner.py` | ✅ Keep |
| Cross-target RFI suppression | existing CLI | ✅ Keep |
| Candidate escalation gate | `prod_scan_queue.py` | ✅ Keep (simplified) |
| Production scan queue + history | `prod_scan_queue.py` | ✅ Keep |
| BL extended corpus download script | `scripts/download_bl_extended_corpus.sh` | ✅ Keep |
| turboSETI batch script | `scripts/run_turboseti_on_extended_corpus.sh` | ✅ Keep |
| Stratified target sample | `data/bl_hprc_seed_targets.csv`, `data/target_sample_manifest.json` | ✅ Keep |
| MeerKAT BLUSE ingest script | `scripts/ingest_meerkat_hits.py` | ✅ Keep (for real training) |
| Injection-recovery grid (setigen) | `scripts/setigen_injection_grid.py` | ✅ Keep |
| Gaia/WISE catalog CSV reader | `infrared/catalog_reader.py` | ✅ Keep |
| SIMBAD known-object cross-match | `live_data.py` | ✅ Keep |
| CI workflow | `.github/workflows/ci.yml` | ✅ Keep |
| `validate-all` (simplified) | `cli.py` | ✅ Keep (needs cleanup) |
| Production scan runbook | `docs/PRODUCTION_SCAN_RUNBOOK.md` | ✅ Keep |
| 110 JSON schema artifacts | `schemas/` | ⚠️ ~100 are misaligned overhead; delete in Phase 0 |

---

## What Must Be Deleted (Misaligned Overhead)

The following modules were built as operational overhead and do not advance
technosignature search. They should be deleted in Phase 0 to reduce complexity,
free storage space, and eliminate doom-loop maintenance burden.

**Operational log modules (~86 log types):** `risk_assessment_log.py`,
`backup_recovery_log.py`, `capacity_planning_log.py`, `polarization_log.py`,
`telescope_status_log.py`, `observation_parameter_log.py`,
`source_catalog_log.py`, `noise_measurement_log.py`,
`spectral_feature_log.py`, `frequency_channel_log.py`,
`pipeline_checkpoint_log.py`, `candidate_status_log.py`,
`signal_classification_log.py`, `rfi_mitigation_log.py`,
`candidate_annotation_log.py`, `observation_request_log.py`,
`candidate_export_log.py`, `quality_gate_log.py`, `data_gap_log.py`,
`candidate_match_log.py`, `pipeline_error_log.py`,
`candidate_deduplication_log.py`, `intake_queue_log.py`,
`workflow_state_log.py`, `alert_resolution_log.py`,
`config_version_history.py`, `operator_escalation_log.py`,
`candidate_alert_log.py`, `pipeline_replay_log.py`,
`scoring_threshold_audit.py`, and associated schemas, fixtures, tests.

**Scheduling/planning scaffolding:** `candidate_triage.py`,
`candidate_observation_notes.py`, `epoch_plan.py`,
`aggregate_blockers.py`, `candidate_score_history.py`,
`operator_assignment.py`, `pipeline_health.py`, `review_deadlines.py`,
`candidate_flags.py`, `pipeline_throughput.py`, `candidate_lifecycle.py`,
`observation_schedule.py`, `weekly_review.py`, `target_watchlist.py`,
`candidate_comparison.py`, `pipeline_telemetry.py`,
`provenance_audit.py`, `candidate_rescore.py`, `operator_handoff.py`,
and associated schemas, fixtures, tests.

**SQLite operational log system:** `log_store.py` (keep the background run
tracking, delete the 86-type adapter scaffolding), all SQLite adapter
consistency gates.

**MCP bootstrap configuration** and associated consistency gates.

**Consensus/calibration/benchmark scaffolding built on synthetic data:**
`consensus_labels.py`, `calibration_metrics.py`, `benchmark_metadata.py`,
`validation_promotion_rules.py`, `validation_dataset_manifest.py`,
`consensus_export.py`, `benchmark_run_results.py`, `sensitivity_config.py`,
`scoring_config.py`, and associated schemas, fixtures, tests.

**Synthetic-only scoring infrastructure** (non-scientific v0 scoring): the
rule-based `baseline_model.py`, `baseline_eval.py`, synthetic calibration
fixture set, score regression snapshots derived from synthetic data.

**Synthetic training data files** — delete to free storage:
- `tests/fixtures/calibration_false_positives.json`
- `tests/fixtures/score_regressions.json`
- Any fixture built purely from synthetic candidates, not real observations

---

## Engineering Foundation Status

All Tier 1 gaps are closed for the radio pipeline as of Milestone 79. All Tier 2
gaps are closed. The project now pivots to multi-modal science (Phases 0–4).

---

## What Is Missing for Science (Phases 0–4)

### Phase 0 — Strip & Fix (NOW)

| Task | Status |
|---|---|
| Delete ~141 misaligned overhead modules | ✅ Done (PR #124, 2026-06-27) — 74 modules deleted, stubs in place |
| Delete synthetic training data files | ✅ Done — synthetic calibration, score-regression, and labeled-training fixtures removed |
| Harden ON/OFF cadence RFI rejection (Enriquez 2017 ABACAB) | ✅ Done (PR #125, 2026-06-27) — abacab_cadence_score feature, source_artifact tracking |
| Train `semisupervised_scorer` on real corpus | ✅ Done locally — trainer CLI and real turboSETI `.dat` corpus builder are wired; local GBT/turboSETI training path verified on 259 real hits; verified MeerKAT BLUSE/SETICORE source ingested to ignored local storage and scorer trained on 200,000 real rows; radio pipeline injects fitted local scorer anomaly features into candidate packets; see `docs/meerkat_bluse_hit_table_research.md` |
| Update `validate-all` to scientific-only gates | ✅ Done — public gate now omits legacy operational/synthetic payloads and checks Phase 0 science gates |
| Add "delete synthetic training data" to production scan runbook | ✅ Done |

**Runbook maintenance task (from user):** ✅ Done — `techno-search
radio-corpus-cleanup` dry-runs and applies local storage cleanup for
`data/extended_corpus/` payloads only after converted `.dat` or zero-hit manifest
evidence exists; `docs/PRODUCTION_SCAN_RUNBOOK.md` now uses exact cleanup
commands instead of placeholder `rm` recipes.

### Phase 1 — Radio: GBT/MeerKAT Hardening

| Task | Status |
|---|---|
| Proper ON/OFF cadence verification (ABACAB from raw files) | ⚠️ Partial — `gbt-cadence-raw-status` verifies approved raw HDF5 presence, size, MD5, and HDF5 signature before cadence processing; local HIP99427 raw files are present under `~/technosignature-data`, the official ingest reproduces the 213-row cadence CSV, and `gbt-cadence-abacab-review` summarizes candidate-level ON/OFF outcomes |
| Real training corpus loaded into semisupervised_scorer | ✅ Done locally — local GBT/turboSETI `.dat` corpus can fit the scorer and production radio packets can carry fitted-model anomaly scores; verified MeerKAT BLUSE/SETICORE JSON source is documented, `scripts/ingest_meerkat_hits.py` supports its schema, and `data/meerkat_hits/semisupervised_scorer_metadata.json` records `train_hit_count: 200000`; payload/model artifacts remain ignored and non-redistributed |
| Drift rate analysis: Earth-rotation-consistent candidates flagged | ⚠️ Partial — radio candidate packets, ranked summaries, and production ledgers now carry normalized drift and Earth-drift consistency features; `radio-real-corpus-summary` validated the current local 6-file real `.dat` corpus with 3 drift rows and 3 Earth-consistent rows; broader hit-bearing stratified-corpus validation remains open |
| Cross-target RFI suppression on full stratified corpus | ⚠️ Partial — production ledgers now carry per-candidate cross-target RFI flags from independent target recurrence; `radio-real-corpus-summary` reported 0 cross-target recurrence flags in the current local 6-file corpus, which has only 1 hit-bearing target, so broader hit-bearing validation remains open; `scripts/download_bl_extended_corpus.sh --manifest data/target_sample_manifest.json` now follows the 31-target stratified manifest, supports `--discover-only` live availability preflight, can write a target-to-HDF5 URL availability TSV, and applies `TECHNO_EXTENDED_CORPUS_MAX_TARGETS` to URL-available HDF5 targets rather than raw manifest position |
| Ranked candidate/non-detection output ready for Phase 5 | ⚠️ Partial — zero-hit observations are preserved as negative evidence ledgers |

### Phase 2 — Transit Photometry: Kepler/TESS

| Task | Status |
|---|---|
| `lightkurve` integration for TESS/Kepler light curve ingest (NASA MAST) | ❌ Not started |
| Box Least Squares (BLS) transit detection | ❌ Not started |
| Non-circular / non-achromatic transit shape analysis | ❌ Not started |
| Asymmetric ingress/egress detection | ❌ Not started |
| Boyajian's Star (KIC 8462852) methodology applied to corpus | ❌ Not started |
| Candidate transit anomaly output | ❌ Not started |

### Phase 3 — Infrared: WISE Dyson Sphere Candidates

| Task | Status |
|---|---|
| WISE W1/W2/W3/W4 photometry ingest for target stars | ❌ Not started |
| SED fitting against stellar photosphere models (Kurucz/BT-Settl) | ❌ Not started |
| W3/W4 excess above stellar photosphere detection | ❌ Not started |
| Natural contaminant rejection (dust, debris disk, AGN) | ❌ Not started |
| IR excess candidate output with SED residual provenance | ❌ Not started |

**References:** Griffith et al. 2015 (ApJ 816, 1), Wright et al. 2014 (ApJ 792, 26)

### Phase 4 — Spectroscopy: JWST Disequilibrium Gases

| Task | Status |
|---|---|
| JWST NIRSpec/NIRISS transmission spectra ingest (MAST) | ❌ Not started |
| NO₂ (combustion) detection in transmission spectra | ❌ Not started |
| CFC/HFC (no natural source) detection | ❌ Not started |
| N₂O (agricultural enhancement) detection | ❌ Not started |
| SF₆ (electrical insulation, no natural source) detection | ❌ Not started |
| Comparison to photochemical equilibrium models | ❌ Not started |
| Spectral anomaly candidate output with significance | ❌ Not started |

**References:** Lin et al. 2014 (ApJ 792, L7), Schwieterman et al. 2018 (Astrobiology 18, 663)

### Phase 5 — Multi-Modal Cross-Correlation & Expert Review

| Task | Status |
|---|---|
| Cross-modal candidate matching by sky position | ❌ Not started |
| Multi-modal priority scoring (targets appearing in ≥2 modalities) | ❌ Not started |
| Adversarial review agent (purpose-built per candidate) | ❌ Not started |
| Candidate submission package (IAU post-detection protocol) | ❌ Not started |
| Third-party expert contact (BL, Penn State, Galileo Project) | ❌ Blocked pending surviving candidate |

---

## Current Production Capability (Honest Assessment)

**Radio pipeline:** Functional for BL/GBT `.dat` files. Produces non-detection
manifests and candidate manifests. Zero-hit turboSETI observations are preserved
as negative-evidence ledger entries instead of being dropped as empty scans.
ON/OFF cadence rejection now exposes an ABACAB cadence score from cadence source
artifacts. `techno-search gbt-cadence-raw-status` verifies the approved
HIP99427 six-scan raw HDF5 cadence against manifest size, MD5, and HDF5
signature evidence before processing. The six approved raw HDF5 files are
present locally under `~/technosignature-data/bl_observations/`, and
`scripts/ingest_gbt_cadence.py` reproduces the 213-row ABACAD cadence CSV with
clean JSON output. `techno-search gbt-cadence-abacab-review` now summarizes
candidate-level ON/OFF cadence outcomes from that derived CSV: the local HIP99427
review has 124 evidence groups, 81 false positives, 41 insufficient-evidence
groups, and 2 local follow-up candidates, with zero primary/audit disagreements.
These follow-up rows are triage candidates only; they are not detections,
discoveries, expert review, external validation, or external-submission approval.
Radio candidate packets, ranked summaries, and production ledgers expose raw
drift, cross-band normalized drift, Earth-drift consistency, and explicit
drift-evidence availability flags for the best hit, making measured drift-rate
evidence distinguishable from compatibility defaults in candidate review and
operator triage artifacts.
Semi-supervised scorer training is executable from real turboSETI `.dat` files
via `techno-search semisupervised-corpus-build` and
`techno-search semisupervised-scorer-train`; the local ignored model was verified
on 259 real GBT/turboSETI hits. `SemisupervisedScorer` now defaults to bounded
12-worker sklearn CPU training and records an explicit accelerator fallback
policy because no tested Apple Metal/MPS or MLX backend exists for PCA +
IsolationForest in this project yet. `run-pipeline` now injects fitted local
semi-supervised anomaly-score features and provenance into radio candidate
packets when `data/meerkat_hits/semisupervised_scorer.joblib` exists, or when a
model is provided with `--semisupervised-model`. These scores are local triage
evidence only and do not alter external-claim guardrails. The earlier claimed
MeerKAT BLUSE hit-table URL was invalid, but
`docs/meerkat_bluse_hit_table_research.md` now records the verified Berkeley
SETI / Breakthrough Listen 3I/ATLAS MeerKAT BLUSE/SETICORE JSON source,
including direct URL, size, SHA256, and schema notes. `scripts/ingest_meerkat_hits.py`
now maps the verified schema into scorer-ready features and fails loudly if the
required schema keys are absent. On 2026-06-29, the verified 94,246,793-byte
payload was downloaded to ignored `data/meerkat_hits/`, checksum
`f0ba629077825097b1c247cf94131858992636d5bf8cea3b5bfde23b0384ea17` was
verified, 200,000 rows were normalized, and the local semi-supervised scorer was
trained with 12 workers. The payload and fitted model must not be redistributed
or committed unless explicit license terms are identified.
`techno-search semisupervised-scorer-summary` now reads the ignored local
metadata/model artifacts by default and reports `model_ready: true` only when the
real-corpus metadata and fitted joblib model are both present; on the current
local system it reports `train_hit_count: 200000`.
`techno-search radio-real-corpus-summary --dat-dir data/extended_corpus --dat-dir data/bl_hits`
now summarizes local real `.dat` evidence without writing payloads. On the
current local corpus it scanned 6 `.dat` files, found 5 zero-hit observations and
1 hit-bearing Voyager calibration file, preserved 3 drift rows, reported 3
Earth-consistent drift rows, found 0 cross-target RFI recurrence flags, and
confirmed the MeerKAT-trained scorer scored 3 hits. The summary now marks
`phase1_radio_validation_ready: false` for the current local corpus because only
1 independent hit-bearing target is available; cross-target RFI suppression
needs at least 2 independent hit-bearing targets before a zero-recurrence result
can be treated as validation evidence. This is local validation evidence only;
the current corpus is not a full hit-bearing stratified validation set.

**Photometry, IR, spectroscopy:** Not implemented. No `lightkurve`, no WISE SED
fitting, no JWST spectral ingest.

**Candidate output:** The radio pipeline can produce candidate manifests and
zero-hit non-detection ledgers from real GBT data (stratified sample of 31
targets, 18 strata). Production follow-up, non-detection, and target-status
ledgers now expose per-candidate cross-target RFI recurrence flags so repeated
frequencies across independent targets are visible at the operator review row.
No multi-modal candidates have been produced.

**Review chain:** Steps 1 (automated) and 2 (adversarial agent) not yet
functional for real candidates. Step 3 (expert review) blocked pending
surviving candidates.

---

## Scientific Guardrails (Non-Negotiable)

1. No candidate report authorizes external submission.
2. No scoring result constitutes a detection claim.
3. All external catalog queries remain opt-in via `TECHNO_SEARCH_ENABLE_LIVE_DATA=1`.
4. No synthetic training data. Models trained on synthetic data are not used for
   real signal detection.
5. Expert review and external validation remain unclaimed unless they actually
   occur and are documented here.
6. A candidate that the adversarial agent cannot refute goes to third-party
   expert review — not to public disclosure.
7. Negative results are valuable. Document them with full provenance.

---

## Decision Reference

Key scientific decisions:
- DECISION-121: Observation admission gate
- DECISION-122: First approved real GBT cadence ingestion; OFF-target rejection
- DECISION-123: Citizen-science reproducibility standard (now superseded by
  publication-grade standard — see AGENTS.md PRIMARY DIRECTIVE)
- DECISION-127: Calibrated scoring thresholds from real GBT noise data
- DECISION-128: Scoring model v1 (77.42% diagnostic agreement on real labels)
- DECISION-133: Model generalizability suite (cross-band features, GLOBULAR,
  semi-supervised scorer — all need real training data)
- DECISION-139: AI hardening production blocker closed for local operations (closes DECISION-134)
- DECISION-141: Production scan history and history-aware queue
- DECISION-143: Stratified random sampling of BL HPRC target list (31 targets,
  18 strata, Isaacson et al. 2017)
