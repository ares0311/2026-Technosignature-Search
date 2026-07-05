# Systematic Search Plan

**Status:** Active plan, recorded 2026-07-05. Read this before starting any
work that touches target selection, calibration, or the production UI.

## Why this document exists

`AGENTS.md`'s "TARGET SELECTION PHILOSOPHY" directive established that this
project optimizes for **detection probability**, not statistical
representativeness — stratified sampling is a null-result-defensibility
device only. This document is the concrete, sequenced plan for closing the
gap between "the pipeline can process real data" (already true) and "this
project runs a systematic, detection-optimized search" (not yet true).

**Every future agent must check this document's current step before
starting new work in this area**, so effort isn't duplicated or spent on a
step that's already blocked on an earlier one.

---

## Current honest state (2026-07-05)

| Capability | Status |
|---|---|
| Pipeline processes real data end-to-end per file/target | ✅ Real, repeatedly demonstrated (Voyager, HIP99427, all 18 KIC 8462852 quarters) |
| Track A known-explanation classification | ✅ Real, implemented |
| Track B 9-condition gate | ✅ Real, implemented, conservative-by-construction |
| Semisupervised anomaly/OOD calibration | ❌ Blocked — see Step 1 |
| Operator UI hardening | ❌ Not started — see Step 2 |
| Detection-optimized target selection algorithm | ❌ Not started — see Step 3 |
| Extended-corpus download completion | ⚠️ Paused mid-run — see Step 0 |

---

## Step 0 (unblocks everything below): finish the extended-corpus download

The 554-target manifest discovery is complete (399/554 targets have a real
BL archive URL). The actual download (capped at
`TECHNO_EXTENDED_CORPUS_MAX_TARGETS=390`, ~90GB) was never restarted after
being paused. This is a prerequisite for Step 1's follow-up-value inputs
and for broader cross-target RFI validation (`docs/PRODUCTION_READINESS.md`
Phase 1) — more real hit-bearing targets are needed before novelty/coverage
scoring in Step 3 has anything real to work with beyond the current 18-file
local corpus.

**Action:** resume
`scripts/download_bl_extended_corpus.sh --manifest data/target_sample_manifest_expanded.json`
per the command already given earlier in this session, then run turboSETI
and the pipeline over the results (`scripts/run_turboseti_on_extended_corpus.sh`,
`scripts/run_pipeline_on_bl_data.sh`), then update
`docs/data_collection_status.json` per the standing reporting directive.

---

## Step 1 (blocks Track B `unknown_candidate` and blocks Step 3's follow-up scoring): close the calibration gap

Per `AGENTS.md`'s "CALIBRATION DATA STATUS" section: the literature search
for more real per-hit labeled data is exhausted
(`docs/seti_labeled_hit_data_research.md`). The only real path left is a
**project-owned human review set**.

**Action, per the research note's recommended schema:**
1. Build a review-sampling tool that pulls hits across score deciles from
   the (post-Step-0) expanded real corpus — not just HIP99427 — so the
   review set spans multiple targets and bands, not one target repeated.
2. Produce a review queue with columns: `hit_id`, `source_file`, `target`,
   `frequency_hz`, `drift_rate_hz_s`, `snr`, `score`, `review_label`,
   `reviewer_id`, `review_timestamp_utc`, `review_notes`.
3. Target: ≥1,000 reviewed rows, ≥50 follow-up-like rows, across multiple
   targets/bands/score-deciles (the research note's minimum useful
   calibration target). This requires real human review time from the
   user — an agent cannot generate or fabricate these labels.
4. If the positive class remains rare even at that scale, calibrate via
   precision-at-k rather than forcing a fixed global threshold (per the
   research note's guidance) — do not invent a cutoff to force a binary
   decision.
5. Once calibrated, re-run `track-b-candidate-readiness` on real
   candidates and confirm `eligible_for_unknown_candidate` can now
   genuinely resolve `true` for a qualifying real candidate, not just
   `false` by default.

**This step is genuine unstarted scientific/human-labor work.** Do not
attempt to shortcut it with rule-derived proxy labels or by re-running the
literature search again.

---

## Step 2 (blocks nothing downstream directly, but must precede Step 3 per user direction): harden the UI

The operator-facing candidate/non-detection review surface must be solid
before scaling the algorithm that feeds it, per the user's explicit
sequencing direction (2026-07-05). Scope not yet defined in detail —
**the next agent picking this up must first audit the current UI
surfaces** (`tui.py`, `prod-scan`/`prod-file-scan` console output,
`reporting.py`'s candidate packets/markdown reports) against real operator
workflows (reviewing a candidate, reviewing a non-detection ledger,
approving/rejecting a follow-up) before proposing specific hardening work,
rather than guessing what "hardened" means without that audit.

---

## Step 3: build the detection-optimized search algorithm

Two required, algorithmically-chosen selection modes, per
`AGENTS.md`'s TARGET SELECTION PHILOSOPHY directive. **Reuse the existing
`target_priority_score`/`target_selection_score` scoring mechanism
(`background_search.py`)** — it already has the right weighted-component
shape (`followup_value`, `novelty_score`, `data_quality_score`,
`observability_score`, `false_positive_probability`, blocking-issue
penalty, never-reviewed boost). **The gap is not the scoring formula — it's
wiring real data into the inputs that formula already expects.**

### 3a. Novel-target selection ("places nobody has looked")

Real, buildable now (after Step 0 gives a larger corpus to compute
coverage against):

1. **Local-coverage gap (real, immediately computable):** cross-reference
   the full real HPRC catalog (`data/bl_hprc_full_seed_targets.csv`, 1,709
   real stars) against which targets this project has actually acquired
   and searched (`data/extended_corpus/`, `docs/data_collection_status.json`).
   Compute a real `novelty_score` input as "has this project ever searched
   this star" (binary or recency-weighted) — this requires no external
   research, only real local provenance data already tracked.
2. **External-coverage gap (real, but needs research before building):**
   a stronger "nobody has looked here" claim would require cross-referencing
   against other surveys' published target lists (not just this project's
   own corpus) — e.g. has this star appeared in *any* published SETI survey.
   This is a real, harder research question with its own verification
   burden (same "do not guess" standard as every other archive claim in
   this project) — treat as a stretch goal, not a blocker for shipping 3a's
   local-coverage version first.
3. Wire the computed `novelty_score` into `target_priority_score()`'s
   existing weighting, don't reinvent the scoring formula.

### 3b. Follow-up-target selection ("candidates needing follow-on checks")

Real, buildable now, independent of Step 1's calibration blocker:

1. **Track B candidate-readiness gaps are already real, structured data.**
   `track-b-candidate-readiness`'s `missing_track_b_candidate_features`
   output (per `docs/PRODUCTION_READINESS.md` Phase 1) already tells you,
   per real candidate, exactly which of the 9 conditions is unresolved and
   why (e.g. insufficient cadence evidence, missing anomaly score).
2. Compute a real `followup_value` input from this: a candidate one
   real-evidence-gap away from full Track B resolution should rank higher
   than one with many unresolved conditions or none at all (nothing to
   follow up on).
3. Map the specific missing condition to a concrete next-observation
   ask (e.g. "needs 3 more ON/OFF cadence epochs," "needs a repeat
   observation in a different band") rather than a bare priority number —
   the output must be actionable, not just a ranked list.
4. Wire the computed `followup_value` into `target_priority_score()`'s
   existing weighting, same as 3a.

### Acceptance criteria for Step 3

- Both modes produce a real, auditable, printed rationale per target
  (matching the existing `docs/PRODUCTION_SCAN_RUNBOOK.md` Rule 4
  requirement that target selection be visible at runtime, not silent).
- Neither mode fabricates or guesses a priority input — every score
  component must trace to real local provenance data or real candidate
  evidence.
- `docs/PRODUCTION_SCAN_RUNBOOK.md`'s existing re-scan/novelty heuristic
  (`prod_scan_queue.py`'s `_selection_score`, first-scan boost / re-scan
  penalty) is a **local re-scan scheduler for already-acquired files** —
  a different, narrower scope than 3a/3b's acquisition-level target
  selection across the full real catalog. Do not conflate the two; wire
  3a/3b as the acquisition-level layer feeding what gets downloaded and
  searched next, distinct from the existing local re-scan queue.

---

## Sequencing summary

```
Step 0 (resume extended-corpus download)
  -> unblocks broader real corpus for Step 1 review sampling and Step 3a coverage data
Step 1 (human-review calibration set)
  -> unblocks Track B unknown_candidate eligibility and Step 3b's real followup_value scoring
Step 2 (UI hardening)
  -> precedes Step 3 per explicit user sequencing direction
Step 3 (detection-optimized search algorithm: 3a novel-target, 3b follow-up-target)
  -> the systematic search capability itself
```

Steps 0 and 1 can proceed in parallel with Step 2 (UI audit/hardening
doesn't depend on either). Step 3 should not start until Step 2 is
substantively underway, per the user's explicit sequencing direction.
