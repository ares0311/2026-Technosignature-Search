# Production Readiness Assessment

**Last updated:** 2026-07-03
**Current milestone:** 79 (Production Scan Hardening And Artifact Hygiene)
**Current phase:** Phase 0 complete; Phases 1-5 all have real, tested baseline
implementations as of 2026-07-03 (Phase 4 opened this date). Remaining gaps
per phase are either genuinely blocked on real data/network access the
agent's sandbox cannot reach, or correctly deferred pending a surviving
candidate (see the Phase 1-5 tables below for specifics).
**Current app version:** 1.2.0

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
| Phase 4 gas-band/MAST research answers (HITRAN peak extraction, C3F8, N2O, MAST `instrument_name`) | `docs/technosignature_detection_research_answers.md` | ✅ Keep — authoritative provenance for `spectroscopy/technosignature_gases.py`'s band centers and the unblocked `jwst_search.py` MAST query fields; integrated into this file's Phase 4 table 2026-07-03 |
| Verified real JWST MIRI LRS MAST target (WASP-43) | `docs/jwst_miri_lrs_mast_targets.md` | ✅ Keep — real target used for the first live-MAST spectroscopy run (PR #212/#217) |
| HITRAN cross-section temperature/pressure inventory (CF4/C2F6/C3F8/SF6/NF3) | `docs/hitran_xsc_tp_inventory.md` | ✅ Keep — real live-queried HITRAN metadata answer, 2026-07-04. **Bottom line: none of the 5 gases have any HITRAN cross-section dataset in the real hot-Jupiter-relevant 500-2000 K range** — every listed dataset is 180-350 K (lab measurements for terrestrial atmospheric monitoring, not exoplanet science; a genuine limit of the real data, not a gap this project can close). Real, usable finding: CF4 and SF6 have viable very-low-pressure alternatives (down to ~0.01-0.07 Torr vs. the 760 Torr room-pressure files already downloaded) that are much closer to the low-pressure regime relevant to transmission spectroscopy (less pressure-broadening, sharper real line shapes); C2F6 has moderate 24.9-75 Torr alternatives; C3F8 only has 0.0-Torr (vacuum-labeled) alternatives; NF3 has no alternative beyond the room-pressure file already downloaded. Candidate next downloads identified but not yet fetched: CF4 dataset ID `3392` (292.7 K, 0.066 Torr, covers the real 7.792935 μm/1283.21 cm⁻¹ band center) and SF6 dataset ID `3331` (294 K, 0.017 Torr, covers the real 10.549570 μm/947.91 cm⁻¹ band center) — both closest-to-room-temperature low-pressure options covering this project's real band centers. |
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
| Astrometrics cross-repo detection/data/storage policies | `docs/astrometrics_coding_agents_master_guide.md`, `docs/astrometrics_data_selection_policy.md`, `docs/astrometrics_external_and_cloud_storage_policy.md` | ✅ Keep — active policy inputs for manifests, data roles, acquisition modes, storage/cache rules, model promotion, and target queues |
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
| Track A known-explanation classifier before Track B `unknown_candidate` routing | ⚠️ Partial — Track A HTRU2 baseline, four known-source catalogs, satellite-transmitter matching, and 13/13 historical replay are implemented from real sources. Track B Phase 4 gate is implemented in `track_b_gate.py` and exposed as `techno-search track-b-unknown-candidate-gate`/`track-b-candidate-readiness`. **First real end-to-end Track B run completed 2026-07-02** on `data/bl_hits/voyager1_hits.dat` (real Voyager 1 X-band downlink hit, 8.419 GHz) using NRAO's own published GBT reference-point coordinates (38.4331211, -79.8398350, 807.43m — verified via GBT Proposer's Guide + National Radio Quiet Zone page, not guessed): **7 of 9 conditions satisfied**, 2 correctly unresolved (single-file cadence evidence; uncalibrated anomaly threshold), `eligible_for_unknown_candidate: false` — no false claim either direction. Surfaced a real, non-urgent scope gap: none of the 9 conditions covers "known human deep-space spacecraft" (SatNOGS/CelesTrak only cover Earth-orbiting objects), so Voyager-class signals fall through to unresolved rather than being confidently attributed — conservative-by-construction design means this causes no wrong claim. **Blocker 2 (real 6-scan ABACAB cadence evidence) closed 2026-07-02**: the real evidence already existed in the committed HIP99427 dataset (124 evidence groups, 2 real `follow_up` candidates), but predated the `abacab_cadence_score` feature and hit a real bug (PR #186 — `_candidate_mapping()` omitted `source_artifact`, so genuine 3-distinct-ON/0-OFF cadences scored the neutral 0.5 instead of 1.0). Fixed; user re-ran `scripts/build_citizen_science_labels.py` and confirmed both real follow-up candidates now report `abacab_cadence_score: 1.0`. **Real 8/9 result 2026-07-02**: HIP99427's real RA/Dec (302.7191, 77.2411125) and observation time were extracted directly from the raw `.dat` header (not guessed or externally looked up), converted with this project's own tested functions, and run through the real crossmatch (`no_known_match`) and real satellite match (`no_known_match`, verified GBT coordinates). `track-b-candidate-readiness` reports **8 of 9 conditions satisfied** on this real candidate — every implemented known-source, RFI, artifact, cadence, and satellite check found no explanation. `eligible_for_unknown_candidate: false`, correctly, since condition 8 remains unresolved. This is not evidence of anomaly; it reflects that the deterministic checks implemented so far have nothing further to say, and false positive remains the default hypothesis per AGENTS.md. **Blocker 1 (calibrated anomaly/OOD threshold) is the only remaining Track B blocker, and a real calibration attempt 2026-07-02 found it can't be resolved with available data.** Ran the real fitted MeerKAT-trained semisupervised scorer against all 124 real HIP99427 evidence groups: `false_positive` (n=81) mean 0.0755, `follow_up` (n=2) mean 0.0456, `insufficient_evidence` (n=41) mean 0.0907 — the two real follow_up candidates score *lower* than confirmed false positives, the opposite of what a "high score = interesting" threshold assumes. A naive percentile-of-false_positive threshold would filter out the exact candidates it should flag. Two real reasons, not implementation gaps: (1) `follow_up` n=2 is too small for any percentile estimate, (2) the scorer is trained on real MeerKAT data, this corpus is real GBT L-band data — cross-instrument feature transfer likely doesn't hold. Real calibration needs either a same-instrument (GBT-native) scorer or a substantially larger real positive sample; neither exists yet. **Literature search for more real per-hit labeled data closed, 2026-07-05** (`docs/seti_labeled_hit_data_research.md`, the user's research agent, run from a machine with real network access): checked 8 real BL/SETI sources (Enriquez 2017, Price 2020, Sheikh/Smith 2021 BLC1, Jacobson-Bell 2025/GLOBULAR arXiv:2411.16556, Lacki 2021 Exotica Catalog, Ma 2023, Choza 2024) against a strict acceptance rule (real downloadable table, one row per hit/candidate, independent human verdict column, mappable label categories) — none qualified. Price et al. 2020's Berkeley SETI event CSVs are the closest real machine-readable artifact found, but their documented columns (`Source`/`DriftRateMax`/`Nevent`/`FreqMid`/`DriftBW`/`DriftRates`/`Freqs`/`FileID`/`SNR`) are event-summary quantities, not verdict labels — explicitly do **not** infer `false_positive` for every row from the paper's "zero surviving candidates" conclusion, since that would fabricate row-level labels never actually published. **Confirmed real conclusion: the 124-row HIP99427 citizen-science set remains the only real per-hit labeled ground truth this project has**, and the recommended real next step is a project-owned human review set (target ≥1,000 reviewed rows, ≥50 follow-up-like, spanning multiple targets/bands/score-deciles — see the research note's `hit_id`/`review_label`/`reviewer_id` schema), using precision-at-k rather than a fixed global threshold if the positive class stays rare. This is genuine unstarted work requiring human review effort, not a data-acquisition or implementation gap. |
| Proper ON/OFF cadence verification (ABACAB from raw files) | ⚠️ Partial — `gbt-cadence-raw-status` verifies approved raw HDF5 presence, size, MD5, and HDF5 signature before cadence processing; local HIP99427 raw files are present under `~/technosignature-data`, the official ingest reproduces the 213-row cadence CSV, and `gbt-cadence-abacab-review` summarizes candidate-level ON/OFF outcomes |
| Real training corpus loaded into semisupervised_scorer | ✅ Done locally — local GBT/turboSETI `.dat` corpus can fit the scorer and production radio packets can carry fitted-model anomaly scores; verified MeerKAT BLUSE/SETICORE JSON source is documented, `scripts/ingest_meerkat_hits.py` supports its schema, and `data/meerkat_hits/semisupervised_scorer_metadata.json` records `train_hit_count: 200000`; payload/model artifacts remain ignored and non-redistributed |
| Drift rate analysis: Earth-rotation-consistent candidates flagged | ⚠️ Partial — radio candidate packets, ranked summaries, and production ledgers now carry normalized drift and Earth-drift consistency features; `radio-real-corpus-summary` validates drift rows from local `.dat` files and can include real normalized hit-NDJSON evidence from the verified MeerKAT BLUSE corpus. On 2026-07-02, the bounded local review counted 5,003 hit rows (5,000 MeerKAT rows plus Voyager control rows), all Earth-consistent under the current drift check; no escalation-ready candidates survived automated filters. Broader candidate-level stratified-corpus review remains open. |
| Cross-target RFI suppression on full stratified corpus | ⚠️ Partial — production ledgers now carry per-candidate cross-target RFI flags from independent target recurrence; current local GBT `.dat` evidence has 18 files, 17 zero-hit observations, and only 1 hit-bearing target (Voyager control), so `.dat`-only recurrence validation remains limited; `radio-real-corpus-summary --hit-ndjson data/meerkat_hits/meerkat_normalised_200000.ndjson` admits the verified real MeerKAT BLUSE hit corpus as hit-bearing Phase 1 validation evidence without committing payloads and reported `cross_target_rfi_validation_ready: true` on a bounded 5,000-row review. `scripts/download_bl_extended_corpus.sh --manifest data/target_sample_manifest.json` follows the 31-target stratified manifest, supports `--discover-only` live availability preflight, can write a target-to-HDF5 URL availability TSV, and applies `TECHNO_EXTENDED_CORPUS_MAX_TARGETS` to new URL-available HDF5 downloads rather than raw manifest position or already-downloaded evidence. |
| Ranked candidate/non-detection output ready for Phase 5 | ⚠️ Partial — zero-hit observations are preserved as negative evidence ledgers. Production scan `RUN-2026-07-02_130330Z-3ZNT-prod-scan` scanned 11 pending extended-corpus targets, failed 0, flagged 0 escalations, produced 0 follow-up entries, produced 39 non-detection/no-follow-up ledger entries across the current local result set, and left 0 pending targets. This is negative evidence only, not a detection, discovery, expert review, external validation, or external-submission authorization. |
| GLOBULAR filter (HDBSCAN, Jacobson-Bell et al. 2024) wired to real data | ✅ Done, 2026-07-02 — `globular_filter.py` existed but was never actually applied to a real hit table (only a `globular-filter-summary` metadata CLI command existed). Wired into `radio_real_corpus_summary()`'s corpus-wide `hit_rows_for_scorer` population (already accumulated across every `.dat`/hit-NDJSON file in a summary run), which is the correct granularity for this filter. **Root-caused and reverted one wrong placement first**: an initial attempt wired GLOBULAR into `build_radio_candidate()` itself (per-candidate, i.e. within one target's own small ON/OFF cadence hit list); this caused the real-label accuracy gate to drop from 77.42% to 65.32% and broke golden-example reproducibility, because a real signal's own naturally-similar repeated hits were mistaken for a dense RFI cluster — the opposite of the intended cross-target RFI signature Jacobson-Bell et al. 2024 actually targets. Reverted before committing; re-implemented at the correct (multi-target corpus) granularity, verified via `.venv/bin/python -m pytest -q` (1478 passed, 0 regressions) and a real 30-dense-hit-plus-1-outlier test confirming the outlier survives as noise while the dense recurring signal is flagged. |

### Sandbox network restrictions — archives that require the user's research agent

This agent's sandbox proxy blocks outbound access to most scholarly/data
hosts. Confirmed via direct `curl` (not just tool failures), 2026-07-04:
`arxiv.org`, `export.arxiv.org`, `iopscience.iop.org`, `zenodo.org`,
`ui.adsabs.harvard.edu`, `researchgate.net`, `seti.berkeley.edu`, and
`vizier.cds.unistra.fr`/`cdsarc.cds.unistra.fr` all return 403 through this
sandbox's proxy — the same restriction already documented above for
`mast.stsci.edu`. Only `github.com`/`raw.githubusercontent.com` are
reachable from here.

**Before concluding any literature-dependent question is unanswerable or a
real dataset "doesn't exist," this agent must check whether the answer
requires one of these blocked hosts.** If so, hand the question to the
user's research agent (running from their own machine with real network
access) rather than reporting a network-restricted search as a genuine
negative result. `docs/bl_hprc_full_catalog_source_request.md` and
`docs/hitran_xsc_temperature_pressure_coverage.md` are the established
pattern for this: a detailed, self-contained research-question doc the
user pastes to their research agent, with explicit "do not guess" rules.

**Closed, 2026-07-05**: `docs/bl_hit_calibration_labels_source_request.md`
asked whether any published BL/SETI paper hosts real per-hit human-labeled
classification data usable to calibrate the semisupervised anomaly
scorer's threshold. The user's research agent ran this from a machine with
real network access and answered it — see `docs/seti_labeled_hit_data_research.md`
and the Phase 1 row above for the full result: no qualifying source was
found across 8 checked real BL/SETI papers/repos/catalogs. This specific
literature-search lead is exhausted; the real next step is building a
project-owned human review set, not further literature search on this
question.

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
| WISE W1/W2/W3/W4 photometry ingest for target stars | ✅ Done, live search/download wrapper added 2026-07-04 — `infrared/catalog_reader.py` parses real IRSA TAP Gaia+AllWISE CSV columns, now including `w3sigmpro`/`w4sigmpro` real per-source photometric uncertainty (verified AllWISE Explanatory Supplement column names, not guessed). `infrared_wise/irsa_search.py` / `techno-search wise-photometry-search <target>` now performs the real live query (`astroquery.ipac.irsa.Irsa.query_region()` against the real `allwise_p3as_psd` AllWISE Source Catalog, real target-name resolution via `astropy.coordinates.SkyCoord.from_name()`), mirroring the same pattern already established for Kepler/TESS (`lightcurve_search.py`) and JWST (`jwst_search.py`) -- this closes the gap where Phase 3 was the only real-data track with no live acquisition tool at all (only a CSV parser for a file someone already had). Not yet run against real IRSA data -- requires the user's machine (same live-network restriction as Track A catalogs and the other MAST-based tracks). |
| SED fitting against stellar photosphere models (Kurucz/BT-Settl) | ⚠️ Partial — `infrared_wise/photosphere_excess.py` fits a single-temperature blackbody (Planck's law via `astropy.modeling.physical_models.BlackBody`) to the real W1/W2 color, not a full Kurucz/BT-Settl grid (which would require downloading external model files). This is the same first-pass simplification used in the IR-excess literature (e.g. Wright et al. 2014) before deeper SED follow-up; documented honestly as a gap rather than claimed as the full grid fit. |
| W3/W4 excess above stellar photosphere detection | ✅ Done — real, verified WISE zero-point flux densities (Wright et al. 2010: 309.54/171.79/31.676/8.3635 Jy for W1-W4, cross-checked 2026-07-02 via live web search against the WISE explanatory supplement and independent citing papers) convert magnitudes to flux; the W1/W2-fit blackbody predicts W3/W4 flux; observed-vs-predicted significance uses real per-source `w3sigmpro`/`w4sigmpro` uncertainty when present, falling back to a documented 10% relative uncertainty otherwise. Verified against a real forward-modeled blackbody test fixture: zero excess for a pure photosphere, exact recovered significance for an injected excess. Wired into `pipeline_runner._build_infrared_candidate()`, overriding the prior color-heuristic `ir_excess_score`/`sed_fit_residual_score` fallback. |
| Natural contaminant rejection (dust, debris disk, AGN) | ⚠️ Partial — `infrared_wise/agn_indicator.py` computes a real `galaxy_agn_indicator_score` from the real WISE W1-W2 color against the Stern et al. (2012) W1-W2≥0.8 (95% reliable, W2<15.05) and Assef et al. (2013) W1-W2>0.5 (90% complete) literature thresholds, both cross-verified via live web search against independent sources, not invented. Wired into `pipeline_runner._build_infrared_candidate()`, overriding the prior caller-supplied default. **Dust/debris-disk rejection remains genuinely unsolved**, not merely unimplemented: WISE colors alone cannot cleanly separate a real debris-disk/YSO dust excess from an otherwise-unexplained W3/W4 excess (both look similar in raw excess terms); that distinction needs stellar age or resolved imaging, which is out of scope here. `dust_indicator_score` remains a caller-supplied input. |
| IR excess candidate output with SED residual provenance | ✅ Done — real `wise_photosphere_temperature_k`, `wise_w3_excess_significance`, `wise_w4_excess_significance` features and a `wise_excess_method` provenance tag are attached to the candidate packet when W1-W4 photometry is present. |

**References:** Griffith et al. 2015 (ApJ 816, 1), Wright et al. 2014 (ApJ 792, 26)

### Phase 4 — Spectroscopy: JWST Disequilibrium Gases

| Task | Status |
|---|---|
| JWST NIRSpec/NIRISS transmission spectra ingest (MAST) | ✅ Corrected + done, 2026-07-03 — real research (live web search, not memory) found the actual real-world instrument for the CFC/PFC/SF₆/NF₃ group this project's first gas set targets is **JWST MIRI Low Resolution Spectrometer (5-14 μm, R~40-160)**, not NIRSpec/NIRISS as this roadmap line originally assumed (Schwieterman et al. 2024, ApJ 969, 20, used MIRI LRS specifically for this gas group). `spectroscopy/jwst_spectrum_io.py` ingests the real JWST pipeline `x1d` product format (`EXTRACT1D` FITS table extension with `WAVELENGTH`/`FLUX`/`FLUX_ERROR` columns, verified against the official JWST pipeline docs). The MAST blocker is now resolved: the user's research agent ran a real, live `astroquery.mast.Observations.query_criteria()` call and confirmed the real `instrument_name` values for MIRI LRS observations are `MIRI/SLIT` (1526 real observations) and `MIRI/SLITLESS` (742 real observations), additionally filterable by `filters="P750L"` (the LRS prism disperser); `MIRI/LRS`, `MIRI/SLITLESSPRISM`, and `MIRI/LRS-FIXEDSLIT` were live-tested and definitively return zero results. Full findings recorded in `docs/technosignature_detection_research_answers.md`. A live MAST search/download CLI wrapper now exists: `spectroscopy/jwst_search.py` / `techno-search jwst-miri-lrs-search <target>`, mirroring `photometry/lightcurve_search.py`'s established pattern, filtering downloaded products to the real, already-verified `x1d`/`x1dints` filename suffixes (the same convention `jwst_spectrum_io.py` reads) rather than an unverified MAST product-type column value. **Run for real, 2026-07-03**: found 31 real x1d-like products for target `WASP-43` (MAST proposal 1366, verified via `docs/jwst_miri_lrs_mast_targets.md`) and downloaded a real `x1dints` FITS file; running it surfaced and fixed a real bug where multi-integration time-series `x1dints` products were silently flattened into a fake static spectrum (see "Current Production Capability" below for the full root cause) -- `load_jwst_x1d_spectrum` now requires an explicit `integration_index` for such files. |
| NO₂ (combustion) detection in transmission spectra | ❌ Not started — real research found NO₂'s actual diagnostic spectral features are in the UV/visible (0.2-0.7 μm), not JWST's near/mid-infrared range at all; a real implementation would need a different instrument (e.g. a UV-capable spectrograph), not JWST NIRSpec/NIRISS/MIRI. Documented honestly rather than building a JWST-based check that couldn't work. |
| CFC/HFC (no natural source) detection | ✅ Done, refined 2026-07-03 — `spectroscopy/technosignature_gases.py` checks for real statistically significant absorption at real band centers extracted directly from downloaded HITRAN cross-section files (Sharpe et al. 2004 via Kochanov et al. 2019, the same source family Schwieterman et al. 2024 cite): CF4 7.792935 μm (global max), C2F6 8.002651 μm and 8.960738 μm (global max and second-strongest band). **C3F8 is now included** (see next row) — the earlier exclusion no longer applies. Full peak-extraction method and HITRAN dataset IDs in `docs/technosignature_detection_research_answers.md`. |
| C3F8 (no natural source) detection | ✅ Done, added 2026-07-03 — real band center 7.923519 μm (1262.065573 cm⁻¹ global max), extracted directly from a real downloaded HITRAN cross-section file (`C3F8_298.1K-760.0Torr_600.0-6500.0_0.11_N2_208_43.xsc`). This closes the earlier gap where C3F8 (the fifth gas in Schwieterman et al. 2024) had no citable band center; see `docs/technosignature_detection_research_answers.md` Q2 for the full derivation. |
| N₂O (agricultural enhancement) detection | ❌ Not started, refined 2026-07-03 with a real, precise reason — a real HAPI/HITRAN line query (54,049 lines, `N2O_main_700_2000`) confirms N₂O's main band sits at 1297.831450 cm⁻¹ (7.705161 μm), close to CF4's band, and a real separated secondary feature exists at 1181.779840 cm⁻¹ (8.461813 μm) — but that secondary feature carries only ~3.7% of the total line strength of the main band (9.67e-18 vs 3.59e-19 cm/molecule total line strength in the 8.1-9.0 μm window), too weak to serve as a reliable standalone diagnostic without much higher SNR than currently available. N₂O also requires "enhancement over natural background" interpretation (it has a real natural biogenic source, unlike the purely artificial CF4/C2F6/C3F8/SF6/NF3 group), which a bare band-position check cannot provide. Full numbers in `docs/technosignature_detection_research_answers.md` Q3. Not implemented rather than implemented ambiguously. |
| SF₆ (electrical insulation, no natural source) detection | ✅ Done, refined 2026-07-03 — real HITRAN-derived band center 10.549570 μm (947.905963 cm⁻¹ global max). NF3 is also implemented as a related artificial gas with no natural source, from the same Schwieterman et al. 2024 gas set, refined to 10.994894 μm (909.513125 cm⁻¹ global max, corrected from an earlier approximate 11.02 μm literature-search value — a real, non-trivial 0.025 μm precision improvement from using the actual downloaded cross-section grid instead of a secondary-source snippet). |
| Comparison to photochemical equilibrium models | ⚠️ Partial, real step added 2026-07-04 — `spectroscopy/hitran_xsc_matched_filter.py` now uses the *entire* downloaded HITRAN cross-section grid (every real wavelength point, not just the single peak) as a physical template, fit against the observed spectrum via a weighted least-squares matched filter (`continuum - flux = amplitude * cross_section_template`). This is real band-shape matching using real laboratory data, a genuine step beyond the single-peak check, but it is still not a full radiative-transfer/photochemical-equilibrium retrieval (no atmospheric model, no absolute column-density calibration) -- documented honestly as the same kind of scope limitation as the WISE blackbody-vs-Kurucz-grid distinction. Wired as optional: `techno-search run-pipeline --jwst-hitran-xsc-dir DIR` (spectroscopy only), attaching informational `<gas>_matched_filter_significance_sigma` features that do not yet feed into `technosignature_gas_score` pending validation against more real data. Verified against a real-format constructed `.xsc` fixture (real HITRAN header/body layout, synthetic values): recovers an injected template-shaped signal at >5σ, reports <4σ for a flat spectrum, and correctly reports not-computable for a non-overlapping wavelength range. Not yet run against the real downloaded `.xsc` grids on the user's machine. |
| Spectral anomaly candidate output with significance | ✅ Done — `spectroscopy/prototype.py`'s `build_spectroscopy_candidate()` produces a `Track.SPECTROSCOPY` `Candidate` with real per-band significance features (`<gas>_<band>um_significance_sigma`), a real 5-sigma detection-count aggregate (the standard physics/astronomy discovery-significance convention, not invented), and `technosignature_gas_score`; wired into `pipeline_runner.run_pipeline(..., track="spectroscopy")` and `scoring.py`'s `_spectroscopy_scores()`. Verified end-to-end on a real, locally-generated x1d FITS fixture with an injected SF6-band dip: recovered significance >5σ, correctly flat (<4σ) on the other verified bands (now including C3F8). |

**References:** Lin et al. 2014 (ApJ 792, L7), Schwieterman et al. 2018 (Astrobiology 18, 663), Schwieterman et al. 2024 (ApJ 969, 20, "Artificial Greenhouse Gases as Exoplanet Technosignatures" — the real source for the CF4/C2F6/C3F8/SF6/NF3 gas set), Sharpe et al. 2004 (Applied Spectroscopy 58, 1452) and Kochanov et al. 2019 (JQSRT 230, 172) via the real HITRAN cross-section database (the direct source of the band centers used here — see `docs/technosignature_detection_research_answers.md` for the full research trail, real dataset IDs, and reproduction method)

### Phase 5 — Multi-Modal Cross-Correlation & Expert Review

| Task | Status |
|---|---|
| Cross-modal candidate matching by sky position | ✅ Done — `multi_modal_crossmatch.py` groups candidate reports across tracks using real `astropy.coordinates.SkyCoord.separation()` (the same verified API already used for Track A catalog/satellite matching) via union-find over pairwise separations, so transitive matches (A-B, B-C) join correctly even when A-C alone would miss the radius. Exposed as `techno-search multi-modal-crossmatch-summary --report-dir DIR`. The match radius is a caller-supplied parameter (default 60 arcsec, documented as a conservative generic cross-survey value, not a per-instrument-calibrated one — real GBT beam/Kepler-TESS pixel/WISE PSF sizes differ by orders of magnitude). **Real bug found and fixed while verifying this end-to-end**: `_build_infrared_candidate()` only injected `ra_deg`/`dec_deg` into candidate features when a live catalog cross-match query ran (`TECHNO_SEARCH_ENABLE_LIVE_DATA=1`); with live queries off (the default), every infrared candidate reported no position under the `ra_deg`/`dec_deg` convention the radio and photometry tracks already use (`infrared/prototype.py` stores it as `ra`/`dec` instead). Fixed to always inject `ra_deg`/`dec_deg` when available, mirroring the radio track's existing pattern exactly. Verified end-to-end: a real radio candidate and a real infrared candidate sharing the same fixture RA/Dec (83.8221, 22.0145) are correctly grouped as one multi-modal match. |
| Multi-modal priority scoring (targets appearing in ≥2 modalities) | ✅ Done — `multi_modal_crossmatch_summary()`'s groups expose `is_multi_modal`/`distinct_track_count`; a group spanning ≥2 tracks is the priority signal AGENTS.md Phase 5 calls for. This identifies which candidates to prioritize; it does not itself run the adversarial review agent (still not started, see below). |
| Adversarial review agent (purpose-built per candidate) | ⚠️ Partial — `adversarial_review.py` implements Step 2 as a deterministic, reproducible dossier that aggregates every refutation check already computed by `scoring.py` (and, when available, the Track B 9-condition gate) into one itemized checklist per candidate. Design choice researched and grounded in the real published precedent: Sheikh et al. 2021 (Nature Astronomy) verified/refuted Breakthrough Listen's one real signal of interest (blc1) using a deterministic itemized checklist, not a freeform LLM argument — this module follows that same approach rather than inventing a novel LLM-red-team design. Exposed as `techno-search adversarial-review-dossier <report.json> [--track-b-gate-json PATH]`. A candidate reports `requires_human_expert_review: true` only when zero refutations, zero blocking issues, and (when Track B evidence is supplied) Track B eligibility all agree; per AGENTS.md, this still requires a real human to review the dossier before any Step 3 escalation — nothing here claims a candidate is confirmed or ready for external submission. An optional freeform LLM "devil's advocate" pass could layer on top of this deterministic dossier in the future; not built here and not required for this step. Verified end-to-end against a real scored candidate report. |
| Candidate submission package (IAU post-detection protocol) | ❌ Not started |
| Third-party expert contact (BL, Penn State, Galileo Project) | ❌ Blocked pending surviving candidate |

---

### Roadmap: Post-Calibration — UI Hardening, then Detection-Optimized Search Algorithm

Recorded 2026-07-05, see `AGENTS.md`'s "TARGET SELECTION PHILOSOPHY" for the
full directive. Sequence, once both the AI (semisupervised anomaly scorer)
and non-AI (deterministic Track A/B rule-based gates) components are
well-calibrated on real evidence (blocked on the open calibration-set item
above):

1. **Harden the UI** — the operator-facing candidate/non-detection review
   surface must be solid before scaling the algorithm that feeds it.
2. **Build the detection-optimized search-target algorithm**, replacing
   stratified sampling as the *primary* target-selection mechanism (it
   remains only as a null-result-defensibility framing device, per the
   scope correction in `docs/SAMPLING_DESIGN.md`). Two required,
   algorithmically-chosen selection modes:
   - **Novel-target selection**: real observational-coverage-gap-driven
     prioritization of targets with little or no prior search coverage.
   - **Follow-up target selection**: real evidence-gap-driven
     prioritization of the optimal next observation for existing
     candidates needing further checks (e.g. more ON/OFF cadence epochs,
     a different band).

Initial local-coverage target selection is implemented:
`techno-search build-target-priority-queue` writes
`data_selection/target_priority_queue.csv` from the full HPRC metadata seed and
tracked acquisition status. The first queue contains 1,703 unique target IDs:
1,683 queued for metadata discovery, 4 metadata-retry rows from prior
`no_hdf5_url_discovered` outcomes, and 16 already-acquired local-cache controls.
This is a metadata-first acquisition-planning artifact only; it does not
authorize raw downloads, does not close the anomaly/OOD calibration blocker, and
does not make any candidate or external-submission claim. Follow-up-target
scoring remains design-only until a real unresolved candidate exists.

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

**Photometry:** Real BLS transit search, aperiodic-dip/asymmetry detection, and
flat-bottom/V-shape transit-shape discrimination implemented and wired
end-to-end (`photometry/`, `Track.TRANSIT_PHOTOMETRY`). **Run against a real
downloaded Kepler corpus on 2026-07-02**: all 18 real Kepler quarters for
KIC 8462852 (Boyajian's Star) processed with 0 failures; 12 of 18 quarters
independently recovered the real, previously-published ~0.88-day periodicity
and correctly classified it as sinusoidal/rotational rather than transit-like
every time (a genuine validation of the vetting logic on real data, not a
detection claim). Three quarters showed anomalously large BLS-fitted
depths, root-caused to a structural limitation of running BLS on a single
Kepler quarter (only ~3 observable cycles at long candidate periods), not a
code defect.

**Infrared:** Real WISE photospheric blackbody excess check
(`infrared_wise/photosphere_excess.py`) and WISE W1-W2 AGN color indicator
(`infrared_wise/agn_indicator.py`) implemented and wired end-to-end into
`_build_infrared_candidate()`. Verified against real forward-modeled
blackbody test fixtures. Live IRSA search/download
(`infrared_wise/irsa_search.py`, `techno-search wise-photometry-search`)
now exists, using the real AllWISE Source Catalog (`allwise_p3as_psd`) via
`astroquery.ipac.irsa.Irsa`. Not yet run against real IRSA data — requires
the user's machine (same live-network restriction as MAST-based tracks).

**Spectroscopy:** Real JWST MIRI LRS `x1d` spectrum ingest
(`spectroscopy/jwst_spectrum_io.py`) and technosignature-gas absorption-band
search (`spectroscopy/technosignature_gases.py`, 5 real HITRAN-derived band
centers: CF4, C2F6 (2 bands), C3F8, SF6, NF3) implemented and wired
end-to-end into `Track.SPECTROSCOPY`. Verified against a real constructed
x1d FITS fixture with an injected SF6-band dip (recovered significance
>5σ). Band centers were refined 2026-07-03 using real peak-extraction
directly from downloaded HITRAN cross-section files (see
`docs/technosignature_detection_research_answers.md`), superseding the
earlier literature-search-derived approximations; C3F8 was added (previously
excluded for lack of a citable band center). Live MAST search/download (`spectroscopy/jwst_search.py`,
`techno-search jwst-miri-lrs-search`) is now built, using the real MAST
`instrument_name` field values for MIRI LRS (`MIRI/SLIT`, `MIRI/SLITLESS`,
filterable by `filters="P750L"`) confirmed via a real live `astroquery`
query. **Run for real against live MAST on 2026-07-03**: the user ran
`techno-search jwst-miri-lrs-search "WASP-43"` (real target verified via
`docs/jwst_miri_lrs_mast_targets.md` -- MAST proposal 1366, `MIRI/SLITLESS`,
`P750L`, real WASP-43b MIRI/LRS phase-curve observation, arXiv:2301.06350)
and it found 31 real x1d-like products and downloaded a real 16MB
`x1dints` FITS file
(`jw01366011001_04103_00002-seg003_mirimage_x1dints.fits`). Running that
real file through `run-pipeline --track spectroscopy` succeeded end-to-end
(119,892 rows, `ok: true`, `pathway: human_review_queue`), but this exact
run surfaced **a real, correctness-affecting bug, found and fixed
2026-07-03**: `point_count: 119892` was suspiciously large for a MIRI LRS
spectrum (~hundreds of points expected). Direct `astropy.io.fits`
inspection of the real file (`hdul.info()`) confirmed the root cause: a
real x1dints time-series product stores all integrations in a *single*
`EXTRACT1D` table with one row per integration (309 rows here) and
`WAVELENGTH`/`FLUX`/`FLUX_ERROR` as per-row 388-element *vector* columns
(309 x 388 = 119,892, exactly matching the reported count) --
`jwst_spectrum_io.py` was silently flattening this into what
`search_gas_absorption_bands` treated as one static spectrum with 119,892
independent points. WASP-43b is a real full-orbit phase-curve target
(arXiv:2301.06350), so flux at each wavelength genuinely varies across the
orbit -- real, correlated time structure, not independent per-wavelength
noise -- which inflated the apparent significance (the run had reported a
10.7-sigma CF4 band result that this made scientifically meaningless
rather than evidence either way). **Fixed**: `load_jwst_x1d_spectrum` now
detects multi-integration (2D vector-column) `EXTRACT1D` tables and
requires an explicit `integration_index` (there is no default -- pooling or
silently picking one would hide a real methodological choice); wired
through `pipeline_runner.run_pipeline(..., jwst_integration_index=...)` and
`techno-search run-pipeline --jwst-integration-index`. Single-integration
`x1d` files are unaffected. This is the first real, live-MAST-sourced
result for the Phase 4 spectroscopy track (previously only exercised
against a self-constructed single-integration test fixture, which is why
this gap wasn't caught earlier), and a real example of this project's
"false positive is the default hypothesis" discipline catching itself
before over-interpreting a spurious result.

**Corrected real result, 2026-07-03**: after the fix, the user re-ran
`run-pipeline --jwst-integration-index 1` on the same real WASP-43 file,
selecting one real, coherent 388-wavelength-point integration instead of
pooling all 309. Result: all 5 real HITRAN-derived gas bands report
sub-1-sigma significance (`cf4_7p79um`: 0.83σ, `c2f6_8p00um`: 0.47σ,
`c2f6_8p96um`: 0.40σ, `c3f8_7p92um`: -0.54σ, `sf6_10p55um`: -0.23σ,
`nf3_10p99um`: 0.03σ) -- `detected_band_count: 0`, `detected_gases: "none"`,
`false_positive_probability: 0.954`,
`pathway: do_not_submit_false_positive`. This is real, correctly-computed
negative evidence from a single real live-MAST-sourced JWST MIRI LRS
integration: no absorption feature at any of the five known
artificial-gas band centers in this one exposure. It is not a claim that
WASP-43b lacks these gases in general (a single 388-point integration is
not a survey), only that this specific real observed spectrum shows none
of the five signatures searched for.

**Multi-modal:** Real cross-modal candidate matching by sky position
(`multi_modal_crossmatch.py`, using `astropy.coordinates.SkyCoord.separation()`)
and a deterministic adversarial-review dossier (`adversarial_review.py`,
Step 2 of the review chain, grounded in the real Sheikh et al. 2021 BLC1
verification-framework precedent) are both implemented and wired end-to-end.

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

**Review chain:** Step 1 (automated multi-modal pipeline) is functional across
all four tracks (radio, photometry, infrared, spectroscopy). Step 2
(deterministic adversarial-review dossier, `adversarial_review.py`) is
implemented and exposed as `techno-search adversarial-review-dossier`, but has
not yet been exercised against a real candidate that reached an advancing
pathway from a real (not fixture-constructed) corpus run. Step 3 (expert
review) remains blocked pending a surviving candidate, as designed.

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
