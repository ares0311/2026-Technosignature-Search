# PROJECT STATUS

## Project
Technosignature Search

## Status
Multi-modal publication-grade technosignature search — Phase 1 radio hardening

## Current Phase
Phase 0 complete; integrated radio resolution is implemented, but real
cadence-complete `unknown`/adversarial Hunter acceptance remains open

## Package Name
`techno_search`

## Current Production Gate

Local deterministic radio pipeline operations are functional. Hunter is not
currently PROD: the retained real corpus verifies the integrated `known` and
`unresolved` branches, but contains no cadence-complete observation that can
exercise the automatic `unknown`/adversarial branch through the installed
Hunter entry points. Learned-model calibration and promotion remain separately
open and fail-closed; that limitation does not block deterministic
known/unknown resolution.

**AI hardening production blocker:** DECISION-134 is open and fail-closed under
DECISION-144. DECISION-139's
synthetic injection-recovery bundle remains valid recovery evidence, but it
cannot supply independent row-level labels or calibrate a global
real-background anomaly/OOD threshold. Learned/AI production promotion is
therefore blocked; the semi-supervised score is ranking-only. New labeling is
prohibited. Radio pipeline functional for BL/GBT `.dat` files. The verified
Berkeley SETI / Breakthrough Listen MeerKAT BLUSE/SETICORE JSON source has been
normalized into ignored local storage, and the local semi-supervised scorer is
trained on 200,000 real rows. The payload and fitted model remain ignored local
artifacts and must not be redistributed without explicit license terms.

**Label-creation boundary:** Project-owned label generation is retired under
DECISION-145. Deterministic cadence review may rank or reject observations for
triage, but it cannot write training, calibration, threshold-selection, or
evaluation labels. The frozen HIP99427 artifact is legacy diagnostic evidence
only and cannot be regenerated, expanded, used to train a model, satisfy an
accuracy gate, or receive real-labeled-data authorization.

**Current phase work:** Phase 1 radio hardening. The current local real-corpus
review retains public null-search information as corpus metadata, never a row
label or rejection condition. It reports 1,072 unlabeled automated triage
survivors and 0 independently escalation-ready rows. A full-source stream over
all 2,028,537 raw MeerKAT rows found no additional ±500 Hz neighbor for the
three rows that clear target-concentration checks; full-band family analysis of
their observation artifacts also did not flag those three rows.
`docs/technosignature_datasets_agent_brief.md` is now the formal Track A dataset
handoff for known-explanation classification before any Track B `unknown`
routing. Version 1.2.44 integrates the catalog and satellite checks into the
production radio path and emits exactly `known`, `unknown`, or `unresolved`.
Anomaly/OOD scores are ranking evidence only and do not define or block
`unknown`. Missing coordinates, observation time, telescope location, cadence,
crossmatch evidence, or satellite evidence resolve loudly to `unresolved`
rather than a guessed negative match. An `unknown` result automatically
receives a durable adversarial dossier. PROD remains revoked until a real
cadence-complete installed-Hunter run exercises that branch.
Retained-data search `SEARCH-20260722T012732Z-759A1D93` from code commit
`10dfb9e` proves that the
installed entry points propagate HIP103096's `unresolved` state and exact
evidence into the durable follow-up ledger; it does not close `unknown`.

---

## Current Capability (Honest Assessment)

**Radio pipeline:** Functional for BL/GBT `.dat` files. Produces non-detection
manifests and candidate manifests. ON/OFF cadence scoring follows the ABACAB
feature added in Phase 0; raw-file ABACAB verification remains Phase 1 hardening.
Semi-supervised scorer integration is locally fitted on the verified real
MeerKAT BLUSE/SETICORE corpus. The current local summary reports
`public_null_search_context_candidate_count: 200000`,
`follow_up_candidate_count: 1072`, and
`independent_escalation_ready_candidate_count: 0`; no candidate is ready for
external escalation. The learned score remains uncalibrated and ranking-only;
it does not control the deterministic known/unknown boundary.

**Photometry, IR, spectroscopy:** Real, tested baseline implementations exist;
their current evidence and remaining Phase 2-4 gaps are tracked in
`docs/PRODUCTION_READINESS.md`.

**Candidate output:** Radio pipeline produces candidate manifests from real GBT data
(stratified sample of 31 targets, 18 strata). No multi-modal candidates yet.

**Review chain:** The deterministic adversarial dossier is automatically
persisted for `unknown`; no retained real observation has reached that branch.
External expert review remains blocked pending a surviving candidate and is
never automatically authorized.

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
| Integrated known-explanation resolution before `unknown` routing | ⚠️ Code complete and verified for real `known`/`unresolved` plus dispatch-tested `unknown`; real cadence-complete installed-Hunter `unknown`/adversarial acceptance remains open |
| Proper ON/OFF cadence verification (ABACAB from raw files) | ⚠️ Partial — HIP99427 raw HDF5 status and derived cadence review are wired locally |
| MeerKAT BLUSE real training corpus loaded into semisupervised_scorer | ✅ Done locally — 200,000 verified real rows train the ignored local scorer |
| Drift rate analysis: Earth-rotation-consistent candidates flagged | ⚠️ Partial — real-corpus summary exposes stationary, Earth-consistent, and inconsistent rows |
| Cross-target RFI suppression on full stratified corpus | ⚠️ Partial — the combined review exercises recurrence, and explicit survivor frequencies can now be checked against all 2,028,537 local raw MeerKAT rows without another materialized corpus |
| Ranked candidate list output ready for Phase 5 | ⚠️ Partial — 1,072 unlabeled rows survive current deterministic filters, but source-context and artifact-independence gates leave 0 independently escalation-ready |

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

1. Continue the Step 2 operator-workflow audit for candidate, non-detection,
   and follow-up handoffs; do not create a review-label workflow.
2. Broaden raw-file ABACAB cadence verification beyond HIP99427 only where
   approved public raw files are locally available.
3. Continue deterministic false-positive investigation of unresolved real-corpus
   triage survivors using the case-study synthesis and existing local evidence;
   without independent evidence, leave them unresolved and unlabeled.

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
