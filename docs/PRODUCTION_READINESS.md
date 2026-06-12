# Production Readiness Assessment

**Last updated:** 2026-06-12
**Current milestone:** 73 (Communication Log, Document Management Log, And Procurement Log)

---

## Summary

The pipeline is approximately **60–65% of the way to citizen-science
production**. All Tier 1 gaps are now closed. The calibration gate passed
`calibration_ready: true` against 213 real GBT hits from 5 cadences, 5
targets, and 2 epochs (HIP99427, HIP100670, HIP99560, HIP99759, VOYAGER-1).
Derived thresholds: noise_floor_snr=42.4, follow_up_snr=54.8,
high_interest_snr=118.3, max_rfi_like_drift_hz_s=5.21. Thresholds require
independent-method citizen-science review before use in production scoring.
Expert review and external validation are not claimed.

---

## What Is Complete

| Capability | Status |
|---|---|
| Synthetic scoring pipeline (radio, infrared, anomaly) | ✅ Complete |
| Candidate report generation (Markdown, JSON, manifest) | ✅ Complete |
| Calibration fixture set (15 false-positive classes) | ✅ Complete |
| Score regression + determinism checks | ✅ Complete |
| Interpretable baseline classifier | ✅ Complete |
| 104 JSON schema artifacts | ✅ Complete |
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

---

## What Is Missing for Production

### Tier 1 — Blockers (nothing ships without these)

**All Tier 1 gaps are closed.** The calibration gate produced `calibration_ready: true` on 2026-06-12.

### Tier 2 — Required for Research-Grade Use

| Gap | Effort estimate |
|---|---|
| Learned scoring model (replace rule-based baseline) | Large |

### Tier 3 — Production Hardening

| Gap | Effort estimate |
|---|---|
| Parallelized batch processing | Small |
| Database-backed candidate store (not file-based) | Medium |
| Operator UI / review dashboard | Large |
| External submission workflow | Large (outside current citizen-science production scope) |
| Reproducibility verification across data releases | Medium |
| Optional expert or institutional review | External opportunity, not assumed |

---

## Production Readiness Estimate

- **Current state:** ~75% (all Tier 1 gaps closed 2026-06-12; 4 of 5 Tier 2 gaps closed 2026-06-12)
- **After Tier 1 complete:** ~60% ✅ reached
- **After Tier 2 complete:** ~80%
- **After Tier 3 complete:** ~100%

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
