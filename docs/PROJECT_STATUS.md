# PROJECT STATUS

## Project
Technosignature Search

## Status
Multi-modal publication-grade technosignature search — Phase 0 (Strip & Fix)

## Current Phase
Phase 0 — Delete misaligned overhead, harden radio pipeline, prepare for multi-modal expansion

## Package Name
`techno_search`

## Current Production Gate

Tier 1 and Tier 2 engineering blockers are closed for local radio pipeline
operations.

**AI hardening gate:** The AI hardening production blocker (DECISION-134) is
closed for local operations via the injection-recovery closure evidence bundle
(DECISION-139). Radio pipeline functional for BL/GBT `.dat` files. The verified
Berkeley SETI / Breakthrough Listen MeerKAT BLUSE/SETICORE JSON source has been
normalized into ignored local storage, and the local semi-supervised scorer is
trained on 200,000 real rows. The payload and fitted model remain ignored local
artifacts and must not be redistributed without explicit license terms.

**Current milestone:** Milestone 79 (Production Scan Hardening And Artifact Hygiene)

**Current phase work:** Phase 1 radio hardening. The current local real-corpus
review treats the verified MeerKAT BLUSE/SETICORE ATLAS rows as public
null-search context and reports zero follow-up candidates.
`docs/technosignature_datasets_agent_brief.md` is now the formal Track A dataset
handoff for known-explanation classification before any Track B
`unknown_candidate` routing. Track A baseline training, known-source catalog
cross-match, satellite-transmitter matching, and small historical replay are
implemented. The Track B Phase 4 gate exists and has CLI wiring; calibrated
anomaly/OOD threshold work remains open. Real-candidate validation now has a
fail-closed packet-readiness audit so missing coordinates, observation time,
telescope location, crossmatch evidence, or satellite evidence are reported
explicitly instead of being guessed. Real turboSETI headers with tabbed
sexagesimal RA/Dec now populate packet RA/Dec, MJD, and derived UTC timestamps;
the remaining measured packet-level satellite blocker is verified observer-site
coordinates.

---

## Current Capability (Honest Assessment)

**Radio pipeline:** Functional for BL/GBT `.dat` files. Produces non-detection
manifests and candidate manifests. ON/OFF cadence scoring follows the ABACAB
feature added in Phase 0; raw-file ABACAB verification remains Phase 1 hardening.
Semi-supervised scorer integration is locally fitted on the verified real
MeerKAT BLUSE/SETICORE corpus. The current local summary reports
`public_null_search_context_candidate_count: 200000`,
`follow_up_candidate_count: 0`, and
`independent_escalation_ready_candidate_count: 0`; no candidate is ready for
external escalation. Track B `unknown_candidate` eligibility remains blocked by
the intentionally unresolved anomaly/OOD threshold unless and until a real
calibration study sets one.

**Photometry, IR, spectroscopy:** Not implemented. No `lightkurve`, no WISE SED
fitting, no JWST spectral ingest.

**Candidate output:** Radio pipeline produces candidate manifests from real GBT data
(stratified sample of 31 targets, 18 strata). No multi-modal candidates yet.

**Review chain:** Steps 2 (adversarial agent) and 3 (expert review) not yet functional.
Step 3 blocked pending surviving candidates.

---

## Completed (Engineering Foundation)

- [x] Radio hit-table reader (turboSETI format)
- [x] Data quality validator (turboSETI `.dat` files)
- [x] Pipeline runner (`.dat` → candidate manifest)
- [x] ON/OFF cadence RFI rejection (partial — needs ABACAB hardening)
- [x] Cross-band feature normalization
- [x] GLOBULAR density pre-filter (HDBSCAN)
- [x] Semi-supervised anomaly scorer (IsolationForest — fitted locally on real MeerKAT rows)
- [x] Multi-epoch hit comparison
- [x] Cross-target RFI suppression
- [x] Candidate escalation gate
- [x] Production scan queue + history (DECISION-141)
- [x] Stratified random sampling of BL HPRC targets (DECISION-143, 31 targets, 18 strata)
- [x] BL extended corpus download script
- [x] turboSETI batch script
- [x] Gaia/WISE catalog CSV reader
- [x] SIMBAD known-object cross-match (opt-in)
- [x] CI workflow
- [x] `validate-all` (simplified)
- [x] Production scan runbook (`docs/PRODUCTION_SCAN_RUNBOOK.md`)
- [x] AGENTS.md and PRODUCTION_READINESS.md rewritten for multi-modal mission
- [x] Pre-commit hook updated for phase-based validation

---

## Phase 0 — Strip & Fix (Current)

| Task | Status |
|---|---|
| Delete ~141 misaligned overhead modules | ✅ Done (PR #124) |
| Delete synthetic training data files | ✅ Done (PR #127) |
| Harden ON/OFF cadence RFI rejection (Enriquez 2017 ABACAB) | ✅ Done (PR #125) |
| Train `semisupervised_scorer` on real MeerKAT BLUSE corpus | ✅ Done locally — verified MeerKAT BLUSE/SETICORE source normalized and fitted on 200,000 real rows |
| Update `validate-all` to scientific-only gates | ✅ Done — public gate is Phase 0 science-only |
| Storage cleanup documented in runbook | ✅ Done |

---

## Phase 1 — Radio: GBT/MeerKAT Hardening

| Task | Status |
|---|---|
| Track A known-explanation classifier before Track B `unknown_candidate` routing | ⚠️ Partial — Track A HTRU2 baseline, known-source catalogs, satellite-transmitter matching, historical replay, Track B gate CLI, and fail-closed real-packet readiness audit are implemented; calibrated anomaly/OOD threshold and hit-bearing real-candidate gate review remain open |
| Proper ON/OFF cadence verification (ABACAB from raw files) | ⚠️ Partial — HIP99427 raw HDF5 status and derived cadence review are wired locally |
| MeerKAT BLUSE real training corpus loaded into semisupervised_scorer | ✅ Done locally — 200,000 verified real rows train the ignored local scorer |
| Drift rate analysis: Earth-rotation-consistent candidates flagged | ⚠️ Partial — real-corpus summary exposes stationary, Earth-consistent, and inconsistent rows |
| Cross-target RFI suppression on full stratified corpus | ⚠️ Partial — verified real corpus exercises recurrence and public-null context; broader independent hit-bearing GBT validation remains open |
| Ranked candidate list output ready for Phase 5 | ⚠️ Partial — public-null context, controls, and RFI rows are separated; independent-ready count is currently 0 |

---

## Phase 2 — Transit Photometry: Kepler/TESS

| Task | Status |
|---|---|
| `lightkurve` integration for TESS/Kepler light curve ingest (NASA MAST) | ❌ Not started |
| Box Least Squares (BLS) transit detection | ❌ Not started |
| Non-circular / non-achromatic transit shape analysis | ❌ Not started |
| Asymmetric ingress/egress detection | ❌ Not started |
| Boyajian's Star methodology applied to corpus | ❌ Not started |
| Candidate transit anomaly output | ❌ Not started |

---

## Phase 3 — Infrared: WISE Dyson Sphere Candidates

| Task | Status |
|---|---|
| WISE W1/W2/W3/W4 photometry ingest for target stars | ❌ Not started |
| SED fitting against stellar photosphere models (Kurucz/BT-Settl) | ❌ Not started |
| W3/W4 excess above stellar photosphere detection | ❌ Not started |
| Natural contaminant rejection (dust, debris disk, AGN) | ❌ Not started |
| IR excess candidate output with SED residual provenance | ❌ Not started |

---

## Phase 4 — Spectroscopy: JWST Disequilibrium Gases

| Task | Status |
|---|---|
| JWST NIRSpec/NIRISS transmission spectra ingest (MAST) | ❌ Not started |
| NO₂ (combustion) detection | ❌ Not started |
| CFC/HFC (no natural source) detection | ❌ Not started |
| N₂O (agricultural enhancement) detection | ❌ Not started |
| SF₆ (electrical insulation, no natural source) detection | ❌ Not started |
| Spectral anomaly candidate output with significance | ❌ Not started |

---

## Phase 5 — Multi-Modal Cross-Correlation & Expert Review

| Task | Status |
|---|---|
| Cross-modal candidate matching by sky position | ❌ Not started |
| Multi-modal priority scoring (targets in ≥2 modalities) | ❌ Not started |
| Adversarial review agent (purpose-built per candidate) | ❌ Not started |
| Candidate submission package (IAU post-detection protocol) | ❌ Not started |
| Third-party expert contact (BL, Penn State, Galileo Project) | ❌ Blocked pending surviving candidate |

---

## Next 3 Actions

1. Resolve the remaining Track B blocker by replacing the naive high-anomaly
   threshold with a same-instrument GBT-native calibration plan, or document why
   the current real evidence still cannot support a threshold.
2. Broaden raw-file ABACAB cadence verification beyond HIP99427 where approved
   public raw files are locally available.
3. Use the fully converted 17-file extended corpus as negative evidence for
   regression checks while prioritizing acquisition of real hit-bearing GBT
   examples; the 2026-07-02 extended-corpus production scan produced 0
   follow-ups and left 0 pending targets.

---

## Current Risks

- Doom loop: operational overhead commits with zero science progress (already occurred PRs #103–#119)
- Overclaiming candidate significance
- Large data files, caches, SQLite logs accidentally committed
- External submission attempted before protocol preconditions are met
- Training on synthetic data (explicitly prohibited)

---

## Mitigations

- Every commit must advance a named phase (Phases 0–4) per AGENTS.md ANTI-DOOM-LOOP directives.
- Keep all outputs conservative and false-positive-first.
- Keep live data opt-in; default tests non-networked.
- No synthetic training data. Real corpora only: MeerKAT BLUSE, real GBT hits.
- External submission disabled unless documented protocol is fully satisfied.

---

## Definition of Done (per Phase)

- Scientific capability implemented (not operational overhead)
- Tests passing against real or realistic data
- `docs/PRODUCTION_READINESS.md` phase status updated
- No unsupported scientific claims
- No new synthetic training data introduced

---

## Recommended Operator Branching

The user stays on `main` and pulls after each merged PR. Agents develop on
`claude/general-session-Bb2dZ` and merge through a PR before starting new work.
