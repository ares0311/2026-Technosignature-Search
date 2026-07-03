# Production Readiness Assessment

**Last updated:** 2026-07-02
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
| GLOBULAR density pre-filter (HDBSCAN) | `globular_filter.py` | ✅ Keep — now wired into `radio_real_corpus_summary()`'s corpus-level `globular_filter` section |
| Semi-supervised anomaly scorer (IsolationForest) | `semisupervised_scorer.py` | ⚠️ Unfitted — needs real MeerKAT training |
| Multi-epoch hit comparison | `pipeline_runner.py` | ✅ Keep |
| Cross-target RFI suppression | existing CLI | ✅ Keep |
| Candidate escalation gate | `prod_scan_queue.py` | ✅ Keep (simplified) |
| Track A known-explanation dataset brief | `docs/technosignature_datasets_agent_brief.md` | ✅ Keep — now production gate input |
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
| Track A known-explanation classifier before Track B `unknown_candidate` routing | ⚠️ Partial — Track A HTRU2 baseline, four known-source catalogs, satellite-transmitter matching, and 13/13 historical replay are implemented from real sources. Track B Phase 4 gate is implemented in `track_b_gate.py` and exposed as `techno-search track-b-unknown-candidate-gate`/`track-b-candidate-readiness`. **First real end-to-end Track B run completed 2026-07-02** on `data/bl_hits/voyager1_hits.dat` (real Voyager 1 X-band downlink hit, 8.419 GHz) using NRAO's own published GBT reference-point coordinates (38.4331211, -79.8398350, 807.43m — verified via GBT Proposer's Guide + National Radio Quiet Zone page, not guessed): **7 of 9 conditions satisfied**, 2 correctly unresolved (single-file cadence evidence; uncalibrated anomaly threshold), `eligible_for_unknown_candidate: false` — no false claim either direction. Surfaced a real, non-urgent scope gap: none of the 9 conditions covers "known human deep-space spacecraft" (SatNOGS/CelesTrak only cover Earth-orbiting objects), so Voyager-class signals fall through to unresolved rather than being confidently attributed — conservative-by-construction design means this causes no wrong claim. **Blocker 2 (real 6-scan ABACAB cadence evidence) closed 2026-07-02**: the real evidence already existed in the committed HIP99427 dataset (124 evidence groups, 2 real `follow_up` candidates), but predated the `abacab_cadence_score` feature and hit a real bug (PR #186 — `_candidate_mapping()` omitted `source_artifact`, so genuine 3-distinct-ON/0-OFF cadences scored the neutral 0.5 instead of 1.0). Fixed; user re-ran `scripts/build_citizen_science_labels.py` and confirmed both real follow-up candidates now report `abacab_cadence_score: 1.0`. **Real 8/9 result 2026-07-02**: HIP99427's real RA/Dec (302.7191, 77.2411125) and observation time were extracted directly from the raw `.dat` header (not guessed or externally looked up), converted with this project's own tested functions, and run through the real crossmatch (`no_known_match`) and real satellite match (`no_known_match`, verified GBT coordinates). `track-b-candidate-readiness` reports **8 of 9 conditions satisfied** on this real candidate — every implemented known-source, RFI, artifact, cadence, and satellite check found no explanation. `eligible_for_unknown_candidate: false`, correctly, since condition 8 remains unresolved. This is not evidence of anomaly; it reflects that the deterministic checks implemented so far have nothing further to say, and false positive remains the default hypothesis per AGENTS.md. **Blocker 1 (calibrated anomaly/OOD threshold) is the only remaining Track B blocker, and a real calibration attempt 2026-07-02 found it can't be resolved with available data.** Ran the real fitted MeerKAT-trained semisupervised scorer against all 124 real HIP99427 evidence groups: `false_positive` (n=81) mean 0.0755, `follow_up` (n=2) mean 0.0456, `insufficient_evidence` (n=41) mean 0.0907 — the two real follow_up candidates score *lower* than confirmed false positives, the opposite of what a "high score = interesting" threshold assumes. A naive percentile-of-false_positive threshold would filter out the exact candidates it should flag. Two real reasons, not implementation gaps: (1) `follow_up` n=2 is too small for any percentile estimate, (2) the scorer is trained on real MeerKAT data, this corpus is real GBT L-band data — cross-instrument feature transfer likely doesn't hold. Real calibration needs either a same-instrument (GBT-native) scorer or a substantially larger real positive sample; neither exists yet. |
| Proper ON/OFF cadence verification (ABACAB from raw files) | ⚠️ Partial — `gbt-cadence-raw-status` verifies approved raw HDF5 presence, size, MD5, and HDF5 signature before cadence processing; local HIP99427 raw files are present under `~/technosignature-data`, the official ingest reproduces the 213-row cadence CSV, and `gbt-cadence-abacab-review` summarizes candidate-level ON/OFF outcomes |
| Real training corpus loaded into semisupervised_scorer | ✅ Done locally — local GBT/turboSETI `.dat` corpus can fit the scorer and production radio packets can carry fitted-model anomaly scores; verified MeerKAT BLUSE/SETICORE JSON source is documented, `scripts/ingest_meerkat_hits.py` supports its schema, and `data/meerkat_hits/semisupervised_scorer_metadata.json` records `train_hit_count: 200000`; payload/model artifacts remain ignored and non-redistributed |
| Drift rate analysis: Earth-rotation-consistent candidates flagged | ⚠️ Partial — radio candidate packets, ranked summaries, and production ledgers now carry normalized drift and Earth-drift consistency features; `radio-real-corpus-summary` validates drift rows from local `.dat` files and can include real normalized hit-NDJSON evidence from the verified MeerKAT BLUSE corpus. On 2026-07-02, the bounded local review counted 5,003 hit rows (5,000 MeerKAT rows plus Voyager control rows), all Earth-consistent under the current drift check; no escalation-ready candidates survived automated filters. Broader candidate-level stratified-corpus review remains open. |
| Cross-target RFI suppression on full stratified corpus | ⚠️ Partial — production ledgers now carry per-candidate cross-target RFI flags from independent target recurrence; current local GBT `.dat` evidence has 18 files, 17 zero-hit observations, and only 1 hit-bearing target (Voyager control), so `.dat`-only recurrence validation remains limited; `radio-real-corpus-summary --hit-ndjson data/meerkat_hits/meerkat_normalised_200000.ndjson` admits the verified real MeerKAT BLUSE hit corpus as hit-bearing Phase 1 validation evidence without committing payloads and reported `cross_target_rfi_validation_ready: true` on a bounded 5,000-row review. `scripts/download_bl_extended_corpus.sh --manifest data/target_sample_manifest.json` follows the 31-target stratified manifest, supports `--discover-only` live availability preflight, can write a target-to-HDF5 URL availability TSV, and applies `TECHNO_EXTENDED_CORPUS_MAX_TARGETS` to new URL-available HDF5 downloads rather than raw manifest position or already-downloaded evidence. |
| Ranked candidate/non-detection output ready for Phase 5 | ⚠️ Partial — zero-hit observations are preserved as negative evidence ledgers. Production scan `RUN-2026-07-02_130330Z-3ZNT-prod-scan` scanned 11 pending extended-corpus targets, failed 0, flagged 0 escalations, produced 0 follow-up entries, produced 39 non-detection/no-follow-up ledger entries across the current local result set, and left 0 pending targets. This is negative evidence only, not a detection, discovery, expert review, external validation, or external-submission authorization. |
| GLOBULAR filter (HDBSCAN, Jacobson-Bell et al. 2024) wired to real data | ✅ Done, 2026-07-02 — `globular_filter.py` existed but was never actually applied to a real hit table (only a `globular-filter-summary` metadata CLI command existed). Wired into `radio_real_corpus_summary()`'s corpus-wide `hit_rows_for_scorer` population (already accumulated across every `.dat`/hit-NDJSON file in a summary run), which is the correct granularity for this filter. **Root-caused and reverted one wrong placement first**: an initial attempt wired GLOBULAR into `build_radio_candidate()` itself (per-candidate, i.e. within one target's own small ON/OFF cadence hit list); this caused the real-label accuracy gate to drop from 77.42% to 65.32% and broke golden-example reproducibility, because a real signal's own naturally-similar repeated hits were mistaken for a dense RFI cluster — the opposite of the intended cross-target RFI signature Jacobson-Bell et al. 2024 actually targets. Reverted before committing; re-implemented at the correct (multi-target corpus) granularity, verified via `.venv/bin/python -m pytest -q` (1478 passed, 0 regressions) and a real 30-dense-hit-plus-1-outlier test confirming the outlier survives as noise while the dense recurring signal is flagged. |

### Phase 2 — Transit Photometry: Kepler/TESS

| Task | Status |
|---|---|
| `lightkurve` integration for TESS/Kepler light curve ingest (NASA MAST) | ✅ Done — `src/techno_search/photometry/`; `techno-search photometry-lightcurve-search` wraps real `lightkurve.search_lightcurve()`/`download_all()`. Live MAST access is unreachable from this project's sandbox (verified live: `https://mast.stsci.edu` returns 403 through the sandbox's outbound proxy) so the search/download command must be run on a machine with real network access, same pattern as Track A catalog acquisition. |
| Box Least Squares (BLS) transit detection | ✅ Done — `photometry/bls_detection.py` wraps `lightkurve.LightCurve.to_periodogram(method="bls")`/`astropy.timeseries.BoxLeastSquares`, verified via direct `inspect.getsource()` of the installed packages (not memory/docs). Recovers period/depth/duration plus real vetting statistics (`depth_odd`/`depth_even`/`depth_half`/`harmonic_delta_log_likelihood`/per-transit fit consistency) from `BoxLeastSquares.compute_stats()`. |
| Non-circular / non-achromatic transit shape analysis | ⚠️ Partial — `photometry/transit_shape.py` now fits real flat-bottom (box) and V-shape (triangular) models by ordinary least squares to the real phase-folded in-transit photometry (the same idea as Kepler's own Data Validation transit-shape diagnostic), and reports which fits better as `grazing_eclipse_score` — a real, independent discriminator from the existing odd/even depth mismatch and sinusoidal-vs-transit checks. Verified against constructed box-shaped and V-shaped injected dips: each is correctly classified. Wired into `pipeline_runner._build_photometry_candidate()` and `scoring.py`'s `_transit_photometry_scores()`. Achromaticity itself remains out of scope — it is not testable from a single-band Kepler/TESS light curve and would require real multi-band follow-up photometry; documented as a gap rather than guessed at. |
| Asymmetric ingress/egress detection | ✅ Done — `photometry/aperiodic_dip.py`'s `detect_aperiodic_dips()` fits linear ingress/egress slopes per event from real light curve data (MAD-based robust significance, no invented thresholds) and reports a real ingress/egress asymmetry score. |
| Boyajian's Star (KIC 8462852) methodology applied to corpus | ✅ Done (methodology) — `detect_aperiodic_dips()` implements the same general diagnostic Boyajian et al. 2016 applied to KIC 8462852's dips (symmetric vs. asymmetric ingress/egress on irregular, non-periodic dimming events), independent of the periodic BLS search. Not yet run against a real downloaded corpus (blocked on live MAST access from this sandbox). |
| Candidate transit anomaly output | ✅ Done — `photometry/prototype.py`'s `build_transit_photometry_candidate()` produces a `Track.TRANSIT_PHOTOMETRY` `Candidate` from real BLS + dip-detector output; wired into `pipeline_runner.run_pipeline(..., track="photometry")` and `scoring.py`'s `_transit_photometry_scores()`. Verified end-to-end (`run_pipeline` → BLS → scoring → `candidate_review_packet` pathway) on a real, locally-generated FITS light curve with an injected transit (`tests/fixtures/photometry/sample_lightcurve.fits`): recovered period 2.198d vs. injected 2.2d, depth SNR 94, correctly reported low blended-eclipsing-binary and sinusoidal-preference scores. No real downloaded Kepler/TESS corpus has been run yet — that requires the user's machine (live MAST access). |

### Phase 3 — Infrared: WISE Dyson Sphere Candidates

| Task | Status |
|---|---|
| WISE W1/W2/W3/W4 photometry ingest for target stars | ✅ Done — `infrared/catalog_reader.py` parses real IRSA TAP Gaia+AllWISE CSV columns, now including `w3sigmpro`/`w4sigmpro` real per-source photometric uncertainty (verified AllWISE Explanatory Supplement column names, not guessed). Real download/acquisition of a live corpus still requires the user's machine (same IRSA/AllWISE network restriction as other astronomy sources from this sandbox). |
| SED fitting against stellar photosphere models (Kurucz/BT-Settl) | ⚠️ Partial — `infrared_wise/photosphere_excess.py` fits a single-temperature blackbody (Planck's law via `astropy.modeling.physical_models.BlackBody`) to the real W1/W2 color, not a full Kurucz/BT-Settl grid (which would require downloading external model files). This is the same first-pass simplification used in the IR-excess literature (e.g. Wright et al. 2014) before deeper SED follow-up; documented honestly as a gap rather than claimed as the full grid fit. |
| W3/W4 excess above stellar photosphere detection | ✅ Done — real, verified WISE zero-point flux densities (Wright et al. 2010: 309.54/171.79/31.676/8.3635 Jy for W1-W4, cross-checked 2026-07-02 via live web search against the WISE explanatory supplement and independent citing papers) convert magnitudes to flux; the W1/W2-fit blackbody predicts W3/W4 flux; observed-vs-predicted significance uses real per-source `w3sigmpro`/`w4sigmpro` uncertainty when present, falling back to a documented 10% relative uncertainty otherwise. Verified against a real forward-modeled blackbody test fixture: zero excess for a pure photosphere, exact recovered significance for an injected excess. Wired into `pipeline_runner._build_infrared_candidate()`, overriding the prior color-heuristic `ir_excess_score`/`sed_fit_residual_score` fallback. |
| Natural contaminant rejection (dust, debris disk, AGN) | ⚠️ Partial — `infrared_wise/agn_indicator.py` computes a real `galaxy_agn_indicator_score` from the real WISE W1-W2 color against the Stern et al. (2012) W1-W2≥0.8 (95% reliable, W2<15.05) and Assef et al. (2013) W1-W2>0.5 (90% complete) literature thresholds, both cross-verified via live web search against independent sources, not invented. Wired into `pipeline_runner._build_infrared_candidate()`, overriding the prior caller-supplied default. **Dust/debris-disk rejection remains genuinely unsolved**, not merely unimplemented: WISE colors alone cannot cleanly separate a real debris-disk/YSO dust excess from an otherwise-unexplained W3/W4 excess (both look similar in raw excess terms); that distinction needs stellar age or resolved imaging, which is out of scope here. `dust_indicator_score` remains a caller-supplied input. |
| IR excess candidate output with SED residual provenance | ✅ Done — real `wise_photosphere_temperature_k`, `wise_w3_excess_significance`, `wise_w4_excess_significance` features and a `wise_excess_method` provenance tag are attached to the candidate packet when W1-W4 photometry is present. |

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
| Cross-modal candidate matching by sky position | ✅ Done — `multi_modal_crossmatch.py` groups candidate reports across tracks using real `astropy.coordinates.SkyCoord.separation()` (the same verified API already used for Track A catalog/satellite matching) via union-find over pairwise separations, so transitive matches (A-B, B-C) join correctly even when A-C alone would miss the radius. Exposed as `techno-search multi-modal-crossmatch-summary --report-dir DIR`. The match radius is a caller-supplied parameter (default 60 arcsec, documented as a conservative generic cross-survey value, not a per-instrument-calibrated one — real GBT beam/Kepler-TESS pixel/WISE PSF sizes differ by orders of magnitude). **Real bug found and fixed while verifying this end-to-end**: `_build_infrared_candidate()` only injected `ra_deg`/`dec_deg` into candidate features when a live catalog cross-match query ran (`TECHNO_SEARCH_ENABLE_LIVE_DATA=1`); with live queries off (the default), every infrared candidate reported no position under the `ra_deg`/`dec_deg` convention the radio and photometry tracks already use (`infrared/prototype.py` stores it as `ra`/`dec` instead). Fixed to always inject `ra_deg`/`dec_deg` when available, mirroring the radio track's existing pattern exactly. Verified end-to-end: a real radio candidate and a real infrared candidate sharing the same fixture RA/Dec (83.8221, 22.0145) are correctly grouped as one multi-modal match. |
| Multi-modal priority scoring (targets appearing in ≥2 modalities) | ✅ Done — `multi_modal_crossmatch_summary()`'s groups expose `is_multi_modal`/`distinct_track_count`; a group spanning ≥2 tracks is the priority signal AGENTS.md Phase 5 calls for. This identifies which candidates to prioritize; it does not itself run the adversarial review agent (still not started, see below). |
| Adversarial review agent (purpose-built per candidate) | ⚠️ Partial — `adversarial_review.py` implements Step 2 as a deterministic, reproducible dossier that aggregates every refutation check already computed by `scoring.py` (and, when available, the Track B 9-condition gate) into one itemized checklist per candidate. Design choice researched and grounded in the real published precedent: Sheikh et al. 2021 (Nature Astronomy) verified/refuted Breakthrough Listen's one real signal of interest (blc1) using a deterministic itemized checklist, not a freeform LLM argument — this module follows that same approach rather than inventing a novel LLM-red-team design. Exposed as `techno-search adversarial-review-dossier <report.json> [--track-b-gate-json PATH]`. A candidate reports `requires_human_expert_review: true` only when zero refutations, zero blocking issues, and (when Track B evidence is supplied) Track B eligibility all agree; per AGENTS.md, this still requires a real human to review the dossier before any Step 3 escalation — nothing here claims a candidate is confirmed or ready for external submission. An optional freeform LLM "devil's advocate" pass could layer on top of this deterministic dossier in the future; not built here and not required for this step. Verified end-to-end against a real scored candidate report. |
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
summarizes local real `.dat` evidence without writing payloads. On the current
local GBT `.dat` corpus it scanned 10 `.dat` files, found 9 zero-hit observations
and 1 hit-bearing Voyager calibration file, preserved 3 drift rows, reported 3
Earth-consistent drift rows, found 0 cross-target RFI recurrence flags, and
confirmed the MeerKAT-trained scorer scored 3 hits. The `.dat`-only summary
marks `phase1_radio_validation_ready: false` because only 1 independent
hit-bearing target is available; cross-target RFI suppression needs at least 2
independent hit-bearing targets before a zero-recurrence result can be treated as
validation evidence. `radio-real-corpus-summary` now also accepts
`--hit-ndjson data/meerkat_hits/meerkat_normalised_200000.ndjson` and
`--max-hit-rows` so the verified real MeerKAT BLUSE hit corpus can exercise
cross-target RFI recurrence, drift-evidence, fitted-scorer integration, and
bounded candidate-review samples without redistributing or committing the
payload. `SemisupervisedScorer.score_hits` now scores batches with one vectorized
sklearn `decision_function` call, so the full 200,000-row local MeerKAT review is
practical. A full local review with `--candidate-sample-limit 0` reviewed
200,003 candidate rows, reported 799 hit-bearing targets, 195,469 cross-target
RFI recurrence flags, 3 known Voyager control rows, 148,215 stationary-drift
rows, 4,887 drift-inconsistent rows, and `phase1_radio_validation_ready: true`.
The verified MeerKAT BLUSE/SETICORE ATLAS corpus is now treated as public
null-search context because the public Breakthrough Listen 3I/ATLAS summary
reports no technosignatures detected and ATel #17499 reports the detected
MeerKAT signals were spatially inconsistent with 3I/ATLAS and likely RFI. The
current local summary therefore reports
`public_null_search_context_candidate_count: 200000`,
`follow_up_candidate_count: 0`, `escalation_ready_candidate_count: 0`, and
`independent_escalation_ready_candidate_count: 0`. Known control targets are
preserved as positive controls, and stationary-frequency rows are separated from
nonstationary rows rather than promoted as follow-up candidates.
These summaries are local validation evidence only; they are not detections,
discoveries, expert review, external validation, or external-submission
approval.

**Photometry:** Real BLS transit search and aperiodic-dip/asymmetry detection
implemented and wired end-to-end (`photometry/`, `Track.TRANSIT_PHOTOMETRY`).
Not yet run against a real downloaded Kepler/TESS corpus — live MAST access
is unreachable from this project's sandbox (verified live 403), so
`techno-search photometry-lightcurve-search` must be run on a machine with
real network access next. **IR, spectroscopy:** Not implemented. No WISE SED
fitting, no JWST spectral ingest.

**Candidate output:** The radio pipeline can produce candidate manifests and
zero-hit non-detection ledgers from real GBT data (stratified sample of 31
targets, 18 strata). Production follow-up, non-detection, and target-status
ledgers now expose per-candidate cross-target RFI recurrence flags so repeated
frequencies across independent targets are visible at the operator review row.
No multi-modal candidates have been produced.
No candidate should be labeled `unknown_candidate` until the Track A
known-explanation classifier from `docs/technosignature_datasets_agent_brief.md`
has a tested, reproducible baseline and the event has failed known-source,
satellite/transmitter, RFI, cadence, and instrument-artifact checks.

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
5. Track A known-explanation classification must precede Track B
   `unknown_candidate` routing. `unknown_candidate` is a local triage queue
   state only.
6. Expert review and external validation remain unclaimed unless they actually
   occur and are documented here.
7. A candidate that the adversarial agent cannot refute goes to third-party
   expert review — not to public disclosure.
8. Negative results are valuable. Document them with full provenance.

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
