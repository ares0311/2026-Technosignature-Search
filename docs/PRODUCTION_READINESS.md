# Production Readiness Assessment

**Last updated:** 2026-06-17
**Current milestone:** 78 (AI Hardening Production Evidence Gate — Tier 3 Production Blocker)

---

## Summary

The pipeline has closed the documented Tier 1 and Tier 2 engineering blockers,
but it is **not yet cleared for live production promotion** because a new Tier 3
AI hardening production blocker is open. DECISION-134 requires held-out
real-data evidence, independent-method citizen-science review, and production
run evidence before the learned or AI-assisted scoring stack can be treated as
production-promotable. Optional expert/institutional review remains a future
external opportunity, not an assumed dependency. The calibration gate passed
`calibration_ready: true` against 213 real GBT hits from 5 cadences, 5 targets,
and 2 epochs (HIP99427, HIP100670, HIP99560, HIP99759, VOYAGER-1). Derived
thresholds: noise_floor_snr=42.4, follow_up_snr=54.8, high_interest_snr=118.3,
max_rfi_like_drift_hz_s=5.21. Thresholds and learned model outputs remain local
scheduling aids until the AI hardening gate is satisfied. A first bounded
held-out HIP17147 GBT HDF5 has been admitted into `data/extended_corpus` and
preserved as zero-hit negative evidence, but it does not close DECISION-134
because candidate-level independent-method comparison still needs valid
held-out hit rows or injection-recovery rows. Expert review and external
validation are not claimed.

---

## What Is Complete

| Capability | Status |
|---|---|
| Synthetic scoring pipeline (radio, infrared, anomaly) | ✅ Complete |
| Candidate report generation (Markdown, JSON, manifest) | ✅ Complete |
| Calibration fixture set (15 false-positive classes) | ✅ Complete |
| Score regression + determinism checks | ✅ Complete |
| Interpretable baseline classifier | ✅ Complete |
| 110 JSON schema artifacts | ✅ Complete |
| Local validation gate (`validate-all`) | ✅ Complete |
| Provenance, audit trail, lifecycle tracking | ✅ Complete |
| Operational log system (86 log types) | ✅ Complete |
| CI workflow (GitHub Actions) | ✅ Complete |
| Real hit-table CSV reader (turboSETI format) | ✅ Complete |
| Real Gaia+WISE catalog CSV reader (IRSA TAP format) | ✅ Complete |
| End-to-end pipeline runner (CSV → scored report) | ✅ Complete |
| Data quality validator (`validate-input`) | ✅ Complete |
| Direct `run-pipeline` CLI with validation-first execution | ✅ Complete |
| Archival anomaly CSV reader scaffold | ✅ Complete |
| Synthetic/local RFI database guardrails | ✅ Complete |
| RFI database admission gates | ✅ Complete |
| Curated dataset admission gates | ✅ Complete |
| Project status consistency gates | ✅ Complete |
| Operations alert review consistency gates | ✅ Complete |
| Operations action resolution staleness gates | ✅ Complete |
| Operations blocker-progress consistency gates | ✅ Complete |
| Top-level SQLite log consistency gates | ✅ Complete |
| Production blocker visibility consistency gates | ✅ Complete |
| SQLite operational log registry consistency gate | ✅ Complete |
| SQLite operational log adapter plan gate | ✅ Complete |
| SQLite operational log adapter contract gate | ✅ Complete |
| SQLite operational log adapter DDL preview gate | ✅ Complete |
| SQLite operational log adapter row preview gate | ✅ Complete |
| SQLite operational log adapter insert preview gate | ✅ Complete |
| SQLite operational log adapter execution preview gate | ✅ Complete |
| SQLite operational log adapter dry-run manifest gate | ✅ Complete |
| SQLite operational log adapter readiness preflight gate | ✅ Complete |
| SQLite operational log adapter authorization gate | ✅ Complete |
| Project-scoped MCP bootstrap configuration | ✅ Complete |
| MCP bootstrap consistency gate | ✅ Complete |
| MCP server policy gate | ✅ Complete |
| Labeled candidate dataset v0 (10 synthetic entries) | ✅ Complete |
| Scoring model evaluation against labeled dataset | ✅ Complete |
| Live catalog clients (Gaia TAP, SIMBAD) with opt-in guard | ✅ Complete |
| Real-observation artifact audit and human-approval gate | ✅ Complete |
| Checksum-verified HIP99427 GBT ABACAD cadence ingestion | ✅ Complete |
| Real turboSETI processing with explicit ON/OFF evidence | ✅ Complete |
| Frequency-matched OFF-target rejection guard validated against real cadence data | ✅ Complete |
| Real HIP99427 cadence label set (124 evidence groups) | ✅ Complete |
| Independent-method citizen-science label audit | ✅ Complete |
| Public reproducibility review package | ✅ Complete |
| Current scoring model evaluated against real labels (54.03% diagnostic agreement) | ✅ Complete |
| **Scoring model v1 with calibrated SNR tiers and drift neutralization** — 77.42% diagnostic agreement (96/124); tiered SNR using noise_floor/follow_up/high_interest thresholds; drift artifact neutralized for real GBT data; NOISE boost for sub-noise-floor single-hit candidates | ✅ Complete |
| Unit-safe, provenance-aware real-noise calibration preflight | ✅ Complete |
| Cadence/target/epoch, dominance, bootstrap, and leave-one-cadence-out gates | ✅ Complete |
| Operational log system (86 log types) | ✅ Complete |
| Resumable parallel BL data download scripts (16-thread, LFS + SSL) | ✅ Complete |
| Voyager 1 GBT turboSETI test H5 downloaded and scored end-to-end (3 real hits, pipeline OK) | ✅ Complete |
| GBT provisional RFI catalog (15 bands, ITU/GPS/ICAO/FCC citations, all inactive pending review) | ✅ Complete |
| Calibration corpus download manifest (5 BL targets, admission gate, pipeline script, operator review protocol) | ✅ Complete |
| GBT provisional RFI catalog operator sign-off (15 entries reviewed, admission gate cleared, ready_for_local_fixture) | ✅ Complete |
| **Calibrated scoring thresholds from real GBT noise data** — calibration gate passed `calibration_ready: true`; 213 hits, 5 cadences, 5 targets, 2 epochs; noise_floor_snr=42.4, follow_up_snr=54.8, high_interest_snr=118.3 | ✅ Complete |
| **Multi-epoch hit-table comparison** — `compare_epochs()` groups hits within frequency tolerance across .dat files; persistence scores; `multi-epoch-compare` CLI (DECISION-129) | ✅ Complete |
| **Parallel candidate scoring** — `score_candidates_parallel()` with `ProcessPoolExecutor`; deterministic; falls back to serial for ≤1 candidate or workers=0/None (DECISION-129) | ✅ Complete |
| **SQLite candidate store** — `CandidateStore` with init/insert/get/list/summary; `candidate-store-init/summary/list` CLI; local triage aid only (DECISION-129) | ✅ Complete |
| **Multi-epoch pipeline injection** — `epoch_dat_files` param wired through `run_pipeline` → `_build_radio_candidate`; `multi_epoch_persistence_score`, `multi_epoch_group_count`, `multi_epoch_epoch_count` injected as candidate features and provenance; `--epoch-files` CLI arg | ✅ Complete |
| **SIMBAD known-object injection** — `simbad_match_count`, `simbad_known_object_score`, `simbad_match_names` injected into radio and infrared candidate features/provenance on every live cross-match query (zero-match also recorded) | ✅ Complete |
| **Gaia/WISE cross-match at scale** — `catalog_crossmatch` wired into `_build_infrared_candidate`; `gaia_match_count`, `known_object_score` injected; both radio and infrared tracks now run live Gaia+SIMBAD queries on `TECHNO_SEARCH_ENABLE_LIVE_DATA=1` | ✅ Complete |
| **Independent reproduction** — `validate-all` confirmed passing in a separate citizen-science environment (2026-06-12) | ✅ Complete |
| **Learned scoring model v1** — logistic regression trained on 124 real GBT/HIP99427 citizen-science labels; 3-class pathway classifier (false_positive / insufficient_evidence / follow_up); 3-fold stratified CV accuracy 99.19% (rule-based baseline: 77.42%); `real-labels-model-summary` CLI; `validate-all` gate: `learned_scoring_model_v1_trained=True`; closes final Tier 2 gap (DECISION-130) | ✅ Complete |
| **Operator review dashboard** — `review_dashboard_summary()` aggregates open flags, overdue deadlines, review queue, blockers, watchlist elevated targets, and real-label accuracy gate into a single operator scheduling aid; `techno-search review-dashboard` CLI with exit code 1 on needs_attention; closes Tier 3 operator UI gap | ✅ Complete |
| **Data release snapshot** — `data_release_snapshot_summary()`, `snapshot_from_batch_manifest()`, `compare_snapshots()`; deterministic SHA-256 pathway assignment hash; `data-release-snapshot-summary` and `compare-data-releases` CLI; 105 JSON schema artifacts; closes Tier 3 reproducibility gap (DECISION-131) | ✅ Complete |
| **Multi-target scan orchestration** — `run_multi_target_scan()` with parallel scoring; per-target result tracking; `MultiTargetScanResult` dataclass; `scan-summary` CLI for ranked anomaly list across N targets (Milestone 76) | ✅ Complete |
| **Cross-target RFI suppression** — `flag_cross_target_rfi()`; signals in ≥2 independent targets at same frequency (within 500 Hz default) flagged as likely terrestrial; `cross-target-rfi-summary` CLI | ✅ Complete |
| **Candidate escalation gate** — `escalation_gate_check()` requiring `candidate_review_packet` + SNR ≥ 42.4; `create_escalation_record()` with SHA-256 reproduction checklist; `operator_cleared` and `external_review_authorized` always start False; `escalation-gate-check` CLI | ✅ Complete |
| **Cross-store position deduplication** — `find_cross_store_matches()` and `cross_store_dedup_summary()` for radio+infrared corroboration by angular separation; 10 arcsec default tolerance | ✅ Complete |
| **Gaia DR3 scan workflow** — `query_gaia_for_targets()` for batch sky queries; guarded behind `TECHNO_SEARCH_ENABLE_LIVE_DATA=1`; per-target JSON output; `load_targets_from_json()` for target list ingestion | ✅ Complete |
| **Weekly automated scan schedule** — `.github/workflows/weekly_scan.yml`; runs Sunday 02:00 UTC; validate-all gate before scan; escalation check on results; commits scan summary to `results/scans/` | ✅ Complete |
| **Calibration transfer protocol** — `docs/CALIBRATION_TRANSFER_PROTOCOL.md`; recalibration steps for new telescope/band; independent-method audit requirement documented | ✅ Complete |
| **Production scan guide** — `docs/PRODUCTION_SCAN_GUIDE.md`; step-by-step operator instructions for multi-store anomaly scanning; escalation triage criteria | ✅ Complete |
| **110 JSON schema artifacts** | ✅ Complete |
| **Hardened escalation gate** — `escalation_gate_check()` returns structured dict; adds `multi_epoch_persistence_score > 0` as third gate (single-epoch candidates cannot pass); `ESCALATION_MULTI_EPOCH_GATE` constant; `negative_result_summary()` for zero-gate scans; `negative-result-summary` CLI (Milestone 77) | ✅ Complete |
| **External submission protocol** — `docs/EXTERNAL_SUBMISSION_PROTOCOL.md`; 7 preconditions (P1–P7) required before any external submission; all currently unmet; DECISION-132; closes Tier 3 external submission workflow gap | ✅ Complete |
| **CHANGELOG.md** — engineering milestone history from v0.10 through current; follows Keep a Changelog format | ✅ Complete |
| **Expert review gate closed** — no institutional expert available; citizen-science reproducibility protocol per AGENTS.md independence standard substituted; expert review explicitly unclaimed | ✅ Complete (Tier 3) |
| **Model generalizability suite (DECISION-133)** — 6 priorities closing the single-campaign generalization gap: (1) extended GBT corpus download script (5 non-Cygnus L-band targets); (2) MeerKAT BLUSE 2M-hit ingest (Sheikh et al. 2025, 900–1670 MHz, false-positive training corpus); (3) setigen injection-recovery grid (SNR × drift × freq); (4) cross-band feature normalization module (`normalized_drift_hz_s_per_ghz`, `is_earth_drift_consistent`, `relative_snr`, `on_off_consistency_score`); (5) GLOBULAR density-based pre-filter (HDBSCAN, 13 features, Jacobson-Bell et al. 2024, ~93% FP reduction, zero labels); (6) semi-supervised anomaly scorer (PCA + IsolationForest, sklearn only, fit on unlabeled RFI corpus); 90 new tests; validate-all gates added | ✅ Complete |
| **AI hardening review protocol** — `docs/AI_HARDENING_REVIEW_PROTOCOL.md`; defines DECISION-134 held-out evidence streams, independent-method review requirements, review-safe evidence bundle contents, and non-claim guardrails | ✅ Complete |
| **AI hardening evidence population accounting (DECISION-135)** — `ai-hardening-gate-summary` and `validation-summary` distinguish configured, existing, populated, and empty DECISION-133 evidence paths; provisional local calibration holdouts remain explicitly insufficient for gate closure | ✅ Complete |
| **Extended-corpus acquisition fail-closed hardening (DECISION-138)** — `scripts/download_bl_extended_corpus.sh` discovers current Breakthrough Open Data HDF5 links and exits nonzero when it produces zero held-out evidence files; this supports DECISION-134 but does not by itself close it | ✅ Complete |
| **First DECISION-134 held-out evidence population** — HIP17147 GBT HDF5 acquired from current BL Open Data, validated as HDF5, processed with turboSETI, and preserved as review-safe zero-hit negative evidence with checksums and method abstentions; this supports DECISION-134 but does not close it because no valid hit rows were available for independent candidate-level method comparison | ✅ Complete |

---

## What Is Missing for Production

### Tier 1 — Blockers (nothing ships without these)

**All Tier 1 gaps are closed.** The calibration gate produced `calibration_ready: true` on 2026-06-12.

### Tier 2 — Required for Research-Grade Use

**All Tier 2 gaps are closed as of 2026-06-12.**

| Gap | Status |
|---|---|
| Learned scoring model (replace rule-based baseline) | ✅ Complete — logistic regression v1 on 124 real HIP99427 labels; 3-fold CV accuracy 99.19%; closes Tier 2 |

### Tier 3 — Production Hardening

| Gap | Effort estimate |
|---|---|
| **AI hardening production blocker (DECISION-134)** | 🚫 Open — production promotion is blocked until held-out DECISION-133 real-data evidence exists, the learned/rule-based/semi-supervised methods are compared on that evidence, disagreements and negative evidence are preserved, and a review-safe production run evidence bundle is produced. This does not reopen Tier 1/Tier 2 engineering closure, but it blocks live production promotion of learned or AI-assisted pathway routing. |
| Parallelized batch processing | ✅ Complete (Tier 3) |
| Database-backed candidate store (not file-based) | ✅ Complete (Tier 3) |
| Operator UI / review dashboard | ✅ Complete (Tier 3) |
| External submission workflow | ✅ Complete (Tier 3) — protocol documented in `docs/EXTERNAL_SUBMISSION_PROTOCOL.md`; all preconditions currently unmet; DECISION-132 |
| Reproducibility verification across data releases | ✅ Complete (Tier 3) |
| Optional expert or institutional review | ✅ Closed (Tier 3) — no institutional expert available; citizen-science reproducibility protocol substituted per AGENTS.md independence standard; expert review explicitly unclaimed and remains a future opportunity if external collaboration arises |

---

## Production Readiness Estimate

- **Current state:** Engineering substrate complete, but live production promotion is blocked by the Tier 3 AI hardening production evidence gate (DECISION-134)
- **After Tier 1 complete:** ~60% ✅ reached
- **After Tier 2 complete:** ~80% ✅ reached 2026-06-12
- **After Tier 3 AI hardening gate complete:** production-promotable for citizen-science operations, while still making no detection, expert-review, external-validation, or external-submission claim

---

## Scientific Guardrails (Non-Negotiable)

Regardless of engineering readiness:

1. No candidate report authorizes external submission.
2. No scoring result constitutes a detection claim.
3. Pathway routing is a local scheduling aid, not a scientific verdict.
4. All external catalog queries remain opt-in via `TECHNO_SEARCH_ENABLE_LIVE_DATA=1`.
5. The pipeline is a provenance and triage tool. Citizen-science production
   decisions require deterministic rules, an independent-method audit,
   published provenance, and visible abstentions or disagreements.
6. Expert review and external validation remain unclaimed unless they actually occur.
7. Learned, semi-supervised, or AI-assisted scores must not be used for
   production pathway promotion until the DECISION-134 AI hardening evidence
   gate is closed.

---

## Decision Reference

See `docs/DECISIONS.md` (DECISION-074) for the formal production readiness
assessment, DECISION-080 for the status-consistency gate, DECISION-081 for the
alert/QC review consistency gate, DECISION-082 for the action-resolution
staleness gate, DECISION-083 for the blocker-progress consistency gate,
DECISION-084 for the top-level SQLite log consistency gate, and DECISION-085
for the production blocker visibility consistency gate, DECISION-097 for
the SQLite operational log registry consistency gate, DECISION-098 for
the SQLite operational log adapter plan gate, DECISION-099 for the SQLite
operational log adapter contract gate, DECISION-100 for the SQLite operational
log adapter DDL preview gate, DECISION-101 for the SQLite operational log
adapter row preview gate, DECISION-102 for the SQLite operational log adapter
insert preview gate, DECISION-103 for the SQLite operational log adapter
execution preview gate, DECISION-104 for the SQLite operational log adapter
dry-run manifest gate, DECISION-105 for the SQLite operational log adapter
readiness preflight gate, DECISION-106 for the SQLite operational log
adapter authorization gate, DECISION-107 for the project-scoped MCP
bootstrap, DECISION-108 for the MCP bootstrap consistency gate,
DECISION-109 for the MCP server policy gate, DECISION-110 for the data
transfer log, system diagnostics log, and resource allocation log,
DECISION-111 for the access control log, change management log, and
incident log, and DECISION-112 for the patch management log, vulnerability
scan log, and compliance audit log, and DECISION-113 for the disaster
recovery log, service level log, and asset management log. DECISION-121 records
the observation admission gate, DECISION-122 records the first approved
real GBT cadence ingestion and OFF-target rejection correction, and
DECISION-123 records the citizen-science reproducibility standard and first
admitted real label set. DECISION-124 records the GBT provisional RFI catalog
from public regulatory documentation. DECISION-125 records the calibration corpus admission gate and download manifest.
DECISION-126 records the GBT provisional RFI catalog operator sign-off.
DECISION-127 records the calibrated scoring configuration from real GBT noise data.
DECISION-128 records scoring model v1 with calibrated SNR tiers and drift neutralization (77.42% diagnostic agreement).
DECISION-134 records the AI hardening production evidence gate as an open Tier 3 production blocker. DECISION-135 records that DECISION-133 evidence paths must be populated before they receive review credit. DECISION-136 records the policy to ignore generated payloads while committing sanitized GitHub-visible artifact maps. DECISION-137 records the M4 Max local optimization directive, including GPU-first AI training when a tested accelerator backend is available. DECISION-138 records that extended-corpus acquisition must discover current Breakthrough Open Data URLs and fail closed on zero evidence.
