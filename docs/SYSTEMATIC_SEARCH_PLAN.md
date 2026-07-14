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

## Current honest state (updated 2026-07-13; originally recorded 2026-07-05)

**Execution-tooling handoff — 2026-07-13:** future explicitly approved
six-manifest Step 3a batches no longer require six terminal tabs.
`scripts/run_six_shard_downloads.py` launches the six disjoint
`stream_process_evict` shards from one terminal, applies the 100GB worst-case
chunk preflight, gates six-worker-per-shard post-processing to 12 aggregate CPU
workers, and refuses completed manifests by default. This is orchestration for
already-approved, metadata-first manifests only; it does not reopen completed
Step 0 or authorize another bulk download. Repository validation likewise uses
`scripts/run_parallel_validation.py` with six xdist workers/six non-overlapping
test shards.

**Step 0 completion handoff — 2026-07-12 23:58 UTC:** PR #251/version 1.2.1
is merged (`5507030`) and all six isolated shards completed 33/33 targets with
198 combined downloads, 198 evictions, zero failures, zero warnings/errors,
and no duplicate target observed by the one-minute process monitor. Six
distinct per-shard v1.2.1 entries with complete target detail are tracked in
`docs/data_collection_status.json`. The corrected corpus contains 215/215
10-Hz/s `.dat` files, zero 4-Hz/s files, 8,988 hit rows across 215 targets,
7,571 cross-target RFI flags, and zero follow-up or escalation-ready
candidates. Raw retention returned to 17 HDF5 files and data usage to 9.0 GB.
Step 0 is complete. Proceed to the Step 1 project-owned human review set; do
not repeat bulk acquisition or infer labels from these automated filters.

| Capability | Status |
|---|---|
| Pipeline processes real data end-to-end per file/target | ✅ Real, repeatedly demonstrated (Voyager, HIP99427, all 18 KIC 8462852 quarters) |
| Track A known-explanation classification | ✅ Real, implemented |
| Track B 9-condition gate | ✅ Real, implemented, conservative-by-construction |
| Semisupervised anomaly/OOD calibration | ❌ Blocked — see Step 1 |
| Operator UI hardening | ⚠️ Substantially underway — 12 operator-facing commands now default to compact summaries with `--json` opt-in, across three rounds of hardening: `prod-target-status`/`prod-follow-ups`/`prod-non-detections` (before 2026-07-09), `review-dashboard` (2026-07-09), and `track-b-unknown-candidate-gate`/`track-b-candidate-readiness`/`gbt-cadence-abacab-review`/`gbt-cadence-raw-status`/`adversarial-review-dossier`/`multi-modal-crossmatch-summary`/`prod-runs`/`scan-summary` (2026-07-10/11, 8 commands — the commit message for this round undercounted it as "7 more", missing `scan-summary`; verified by counting `_print_*` functions directly, not trusting the commit message). `escalation-gate-check`/`cross-target-rfi-summary`/`health`/`prod-show` deliberately left alone — small flat dicts, already scannable. See Step 2 for what a future audit should still check. |
| Detection-optimized target selection algorithm | ⚠️ 3a (novel-target selection) real and running: 13 discover→preflight→promote rounds completed (`top25`/`next25`/`batch3`-`batch13`) as of 2026-07-11, 195 targets / ~49 GB promoted to `raw_download_approval_required` (as of `batch12`; `batch13` built, discovery pending), all pending explicit raw-download approval — no payloads downloaded. 3b (follow-up-target selection) remains design-only per its documented gate (no real qualifying candidate exists yet to validate it against). See Step 3a. |
| Extended-corpus completion | ✅ Complete — corrected v1.2.1 six-shard rerun finished 198/198 targets with zero failures or duplicate processing; the full 215-target local corpus is now at 10 Hz/s and contains 8,988 triage rows, with zero follow-up/escalation-ready candidates. See Step 0 completion below. |

---

## Step 0 (complete): corrected extended-corpus bootstrap

**Correction, 2026-07-12 — this supersedes the stale “paused” status below.**
The first bounded 198-target, approximately 49.9 GB `stream_process_evict`
batch completed with zero transport/process failures, but its scientific
outputs need reprocessing. The extended-corpus runner used `max_drift=4` on
`.0002.h5` products whose preserved logs report an approximately 9.8 Hz/s
first drift bin; with DC blanking enabled, the run could not search a nonzero
drift bin. A retained real HIP17147 product produced 13 rows when rerun at the
already-reviewed 10 Hz/s ingestion ceiling, confirming the root cause.

The code now refuses a drift ceiling below the input product's resolvable bin,
passes 10 Hz/s explicitly for the `.0002` corpus, and recognizes lower-ceiling
`.dat` files as stale when their HDF5 source is present. The 17 retained files
were reprocessed first; the authorized v1.2.1 six-shard rerun then completed all
198 evicted targets. Do not use the superseded 4-Hz/s zero-hit results as null
evidence or calibration rows. The historical text below remains only as
context for why this one-time corpus widening was required.

The first authorized corrected rerun was stopped after 120 unique downloads
and 60 evictions because concurrent shards were discovered recursively
post-processing the same global corpus and racing on identical `.dat` outputs.
Those raced outputs are not validation evidence. Version 1.2.1 isolates
turboSETI and pipeline work to each shard's current target, preserves distinct
per-shard status entries, and locks concurrent status-manifest publication.
Seventy-seven complete raw HDF5 files plus one resumable partial remained at
termination. The subsequent v1.2.1 restart reused/resumed them and completed
all manifests. Final measured results are in the Step 0 completion handoff.

The 554-target manifest discovery is complete (399/554 targets have a real
BL archive URL). The actual download (capped at
`TECHNO_EXTENDED_CORPUS_MAX_TARGETS=390`, ~90GB) was never restarted after
being paused. This is a prerequisite for Step 1's follow-up-value inputs
and for broader cross-target RFI validation (`docs/PRODUCTION_READINESS.md`
Phase 1) — more real hit-bearing targets are needed before novelty/coverage
scoring in Step 3 has anything real to work with beyond the current 18-file
local corpus.

**This is explicitly a one-time corpus-widening bootstrap, not the ongoing
acquisition model.** It's still driven by the stratified manifest — the
same mechanism `AGENTS.md`'s TARGET SELECTION PHILOSOPHY says should not be
the primary target-selection driver going forward. It's done once here
because Step 1 and Step 3a need a large enough real corpus to work with at
all (18 local files isn't enough to compute meaningful novelty scores or
build a 1,000-row review set), not because bulk-downloading a static
manifest is the intended long-term pattern.

**Once Step 3 exists, the sequence flips**: the algorithm decides which
specific targets to acquire next (driven by real novelty/follow-up
scoring), and acquisition happens per-target, continuously — not
"bulk-download broadly first, then apply an algorithm to whatever landed."
Do not treat a future large stratified-manifest download as a template to
repeat; Step 0 is a bootstrap exception, made once to unblock Steps 1 and
3, not a recurring operating pattern.

**Action:** resume
`scripts/download_bl_extended_corpus.sh --manifest data/target_sample_manifest_expanded.json`
per the command already given earlier in this session, but only after applying
the Astrometrics data/storage policy now tracked in:

- `docs/astrometrics_data_selection_policy.md`
- `docs/astrometrics_external_and_cloud_storage_policy.md`

That means: record the acquisition role and mode, confirm the batch remains
within policy caps, confirm local free-space reserve, preserve metadata and
status in `docs/data_collection_status.json`, and keep raw public archive files
as cache unless a policy-backed pin rule promotes them. Then run turboSETI and
the pipeline over the results (`scripts/run_turboseti_on_extended_corpus.sh`,
`scripts/run_pipeline_on_bl_data.sh`), and update
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
sequencing direction (2026-07-05). The first concrete hardening pass is now
underway: `prod-scan` prints compact completed-target rows; `prod-file-scan`
completed-target lines include follow-up yes/no and pathway context; and the
post-run review commands (`prod-target-status`, `prod-follow-ups`,
`prod-non-detections`) default to compact terminal summaries, with `--json`
preserved for machine-readable ledgers. Candidate Markdown/JSON reports now
include an `operator_review` block with the pathway, follow-up-required flag,
operator action, and no-claim guardrails. The `review-dashboard` CLI and
per-run `*_review_dashboard.json` artifact now summarize real target-status or
candidate-manifest state using `operator_review_dashboard_v1`, including
follow-up-required counts, pathway-specific action items, cross-target RFI flag
counts, and top follow-up targets.

**Real gap found and fixed, 2026-07-09:** a workflow audit against a real
local production run (`RUN-2026-07-02_130330Z-3ZNT-prod-scan`) found that
`review-dashboard` — despite being documented above as a hardened operator
surface — printed raw indented JSON by default with no compact-table option,
unlike its three sibling commands (`prod-target-status`/`prod-follow-ups`/
`prod-non-detections`), which all default to a header-line-plus-table
summary and only print JSON behind an explicit `--json` flag. This is exactly
the "guessed hardened because it has a command" failure mode this section
warns against. Fixed: `review-dashboard` now defaults to the same compact
style (source/target/follow-up counts, an action-item table, a top-follow-up-
target table) and gained `--json` for the machine-readable form, matching its
siblings. Regression test updated in `tests/test_cli.py`.

Remaining Step 2 work must continue from a workflow audit of the other current
UI surfaces (especially any operator handoff views outside the candidate
packet path) against real operator workflows: reviewing a candidate, reviewing
a non-detection ledger, and approving/rejecting a follow-up. Do not guess that
a UI is hardened because it has a command; verify the operator can answer the
next review question without paging through raw machine output.

**Second workflow audit, 2026-07-10:** surveyed every real (non-deleted-stub)
operator-facing summary command for the same defect. Ten candidates were
raw-JSON-only with no `--json` flag at all: `escalation-gate-check`,
`cross-target-rfi-summary`, `track-b-unknown-candidate-gate`,
`track-b-candidate-readiness`, `gbt-cadence-abacab-review`,
`gbt-cadence-raw-status`, `scan-summary`, `health`, `prod-runs`, `prod-show`.
Applying the same judgment this section calls for (verify the operator can
answer the review question, don't mechanically "fix" every command with a
JSON flag): `escalation-gate-check`, `cross-target-rfi-summary`, and `health`
each return a small flat dict (5-9 keys, no per-item arrays) that is already
scannable as printed JSON — adding `--json` there would be bureaucratic
parity, not a real UX fix, so they were left alone. `prod-show` is similarly
a small flat single-run dict, left alone. The remaining eight genuinely
return large nested/multi-row structures an operator would have to page
through, and each is directly part of the real review chain (Track B
`unknown_candidate` eligibility -- the core "approve/reject" decision;
ABACAB cadence review; the Step 2 adversarial-review dossier; multi-modal
cross-match groups; ranked scan-summary candidates; the run picker):
`track-b-unknown-candidate-gate`, `track-b-candidate-readiness`,
`gbt-cadence-abacab-review`, `gbt-cadence-raw-status`, `scan-summary`,
`adversarial-review-dossier` (already lacked `--json` entirely, not caught
by the raw-JSON survey above since it was not on the original ten-item
list), `multi-modal-crossmatch-summary` (same), and `prod-runs`.
(This paragraph originally said "seven" and omitted `scan-summary` from
this list -- a real arithmetic error caught and fixed 2026-07-11 during a
milestone audit; the ten-item survey, the four left-alone, and the "three
new CLI-level tests... for scan-summary, multi-modal-crossmatch-summary,
and adversarial-review-dossier" sentence below were all already correct,
only this one list and count were wrong.) All eight
now default to a compact table matching the established
`_print_review_dashboard`/`_print_production_target_status` style, with
`--json` for the machine-readable form. Six existing `tests/test_cli.py`
tests that called these commands without `--json` and parsed the stdout as
JSON were fixed to pass `--json` explicitly; new compact-mode assertions
were added to every fixed/new test so the new default path is actually
exercised, not just left unbroken. Three new CLI-level tests were added for
`scan-summary`, `multi-modal-crossmatch-summary`, and
`adversarial-review-dossier`, which previously had no CLI-dispatch test
coverage at all. 1580 tests pass (up from 1577), ruff/mypy clean,
`validate-all` ok.

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

Local-coverage target selection is now initialized. It still improves after
Step 0 widens the local corpus, but the first metadata-first queue exists and
is GitHub-visible. It follows
`docs/astrometrics_data_selection_policy.md`'s metadata-first target-queue
requirements:

1. **Local-coverage gap (real, immediately computable):** cross-reference
   the full real HPRC catalog (`data/bl_hprc_full_seed_targets.csv`, 1,709
   real stars) against which targets this project has actually acquired
   and searched (`data/extended_corpus/`, `docs/data_collection_status.json`).
   Compute a real `novelty_score` input as "has this project ever searched
   this star" (binary or recency-weighted) — this requires no external
   research, only real local provenance data already tracked. **Initial
   implementation:** `techno-search build-target-priority-queue` writes
   `data_selection/target_priority_queue.csv` from the full HPRC seed CSV and
   `docs/data_collection_status.json`. The first committed queue has 1,703
   unique target IDs: 1,683 queued for metadata discovery, 4 requiring metadata
   retry after prior `no_hdf5_url_discovered` results, and 16 already-acquired
   local-cache controls. One status-manifest reused target (`HIP75676`) is not
   present in the full HPRC seed CSV and is therefore not forced into the queue.
2. **External-coverage gap (real, but needs research before building):**
   a stronger "nobody has looked here" claim would require cross-referencing
   against other surveys' published target lists (not just this project's
   own corpus) — e.g. has this star appeared in *any* published SETI survey.
   This is a real, harder research question with its own verification
   burden (same "do not guess" standard as every other archive claim in
   this project) — treat as a stretch goal, not a blocker for shipping 3a's
   local-coverage version first.
3. Produce or update a target-priority queue with the required data-selection
   fields before any new acquisition batch, rather than treating the model score
   alone as a download reason. **Initial implementation done:**
   `data_selection/target_priority_queue.csv`. A bounded downloader-compatible
   manifest for the top 25 local-coverage targets is also available at
   `data_selection/batch_manifests/local_coverage_top25_manifest.json`. The
   first real metadata-only discovery run checked all 25 targets, found current
   BL HDF5 URLs for 15 targets, found no current HDF5 URL for 10 targets, and
   downloaded zero raw payloads. The regenerated queue now marks those 15 rows
   as `size_preflight_required`; use
   `data_selection/batch_manifests/local_coverage_top25_size_preflight_manifest.json`
   for URL-size/checksum/storage preflight before any raw download. **Preflight
   implementation done:** `techno-search target-priority-size-preflight` writes
   `data_selection/batch_manifests/local_coverage_top25_size_preflight_report.json`.
   The first HEAD-only run verified 15/15 URLs with content lengths, estimated
   3.803966 GB total, found no checksum headers, and left
   `raw_download_authorized: false`. The regenerated queue marked those 15
   rows as `raw_download_approval_required`.

   **Second round (`next25`), 2026-07-09:** the same discover → size-preflight
   → promote sequence ran against the next 25 highest-priority
   `queued_metadata_discovery` rows, finding 14 current HDF5 URLs (11 without)
   and verifying 14/14 with a 3.608361 GB total. This surfaced and fixed a
   real bug: `build-target-priority-queue` only read one hard-coded
   size-preflight report, so promoting `next25`'s 14 targets would have
   silently regressed `top25`'s 15 back out of
   `raw_download_approval_required`. Fixed by merging every committed
   `*_size_preflight_report.json` under `data_selection/batch_manifests/`
   (new `--extra-size-preflight-report-path`, default: auto-glob) — see
   `docs/LOCAL_DATA_INVENTORY.md`'s "2026-07-09 Local-Coverage `next25`"
   entry for the full root cause and regression test. The queue now reports
   29 targets in `raw_download_approval_required`, consolidated in
   `data_selection/batch_manifests/local_coverage_raw_download_approval_manifest.json`
   (~7.41 GB combined) as the review input for explicit bounded raw-download
   approval. This same discover → preflight → promote pattern is the
   repeatable, safe (metadata-only) way to keep advancing 3a through further
   rounds without needing raw-download approval at each step.

   **Third round (`batch3`), 2026-07-10:** building the next 25-target
   manifest the same way surfaced a second real merge bug, one step earlier
   in the pipeline than the `next25` size-preflight bug:
   `docs/data_collection_status.json` keeps only the single most recent
   `download_bl_extended_corpus_discovery` run, so `top25`'s 10 "no HDF5 URL
   found" targets were lost once `next25`'s discovery ran, and resurfaced as
   10 of the 25 rows in a first `batch3` manifest attempt — which would have
   wasted a live-network re-check on targets already known to have no
   current URL. Fixed with the analogous mechanism already proven for
   size-preflight reports: `build_target_priority_queue`/
   `build-target-priority-queue` now also merges every committed
   `*_discovery_result.json` file (`--extra-discovery-result-path`, default:
   auto-glob), and `scripts/download_bl_extended_corpus.sh` gained
   `--discovery-result-output PATH` so future discovery rounds persist their
   full outcome durably instead of only writing into the single-slot status
   file. `top25`'s and `next25`'s lost discovery outcomes were reconstructed
   from already-committed evidence (each round's discovery manifest minus
   that round's size-preflight manifest is exactly its checked-but-no-URL
   set — not guessed) and committed as
   `local_coverage_top25_discovery_result.json` /
   `local_coverage_next25_discovery_result.json`; see
   `data_selection/batch_manifests/README.md` for full detail and
   regression test
   `test_build_target_priority_queue_merges_multiple_discovery_results`.
   `batch3`'s own discovery round is not yet run (needs live network access
   from the user's machine — `breakthroughinitiatives.org`/
   `bldata.berkeley.edu` are unreachable from this agent's sandbox, same
   restriction already documented for MAST/IRSA/arXiv hosts).
4. Wire the computed `novelty_score` into `target_priority_score()`'s
   existing weighting, don't reinvent the scoring formula. **Initial
   implementation done:** queue rows include a normalized
   `background_target_priority_score` using the existing
   `target_priority_score()` component shape; the data-selection
   `total_priority` remains the policy-required 0-3 live-search sum.

### 3b. Follow-up-target selection ("candidates needing follow-on checks")

**Corrected 2026-07-05 — do not treat this as "buildable now" the way 3a
is.** The original version of this section assumed a real backlog of
partial candidates to drive follow-up scoring from. That assumption does
not hold: the current real local corpus is 17 zero-hit non-detections and
1 hit-bearing target (Voyager, a known human signal, not an unresolved
candidate). **There is no real backlog of near-miss candidates today.**
Building 3b's scoring logic now means building machinery with nothing real
to exercise it — a genuine risk of it sitting untested and silently broken
until the day a real candidate needs it.

**Correct sequencing: design now, implement/validate once a real
qualifying candidate actually exists.** Concretely:

1. **Design (do now):** `track-b-candidate-readiness`'s
   `missing_track_b_candidate_features` output (per
   `docs/PRODUCTION_READINESS.md` Phase 1) is the right real, structured
   data source for this — per real candidate, it already reports exactly
   which of the 9 conditions is unresolved and why. The intended
   `followup_value` computation: a candidate one real-evidence-gap away
   from full Track B resolution ranks higher than one with many unresolved
   conditions or none at all. The output must map the specific missing
   condition to a concrete next-observation ask (e.g. "needs 3 more ON/OFF
   cadence epochs," "needs a repeat observation in a different band"), not
   a bare priority number.
2. **Implementation gate:** do not write and merge the scoring code for
   this until a real candidate with a genuine partial-evidence gap exists
   to test it against (not a synthetic/constructed fixture standing in for
   "a candidate exists" — that would validate the code runs, not that the
   scoring behavior is right, since there's no real case to check it
   against). Prioritize **3a** as the actual near-term buildable work
   instead; revisit 3b when Step 0/ongoing scanning produces a real
   qualifying candidate.
3. Wire the computed `followup_value` into `target_priority_score()`'s
   existing weighting, same as 3a, once triggered by a real case.

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
Step 3a (novel-target selection: real, buildable now once Step 0 lands)
  -> prioritize this as the actual near-term Step 3 work
Step 3b (follow-up-target selection)
  -> design only; implementation waits on a real qualifying candidate existing —
     do not build/merge scoring code against a backlog that doesn't exist yet
```

Steps 0 and 1 can proceed in parallel with Step 2 (UI audit/hardening
doesn't depend on either). Step 3 should not start until Step 2 is
substantively underway, per the user's explicit sequencing direction. Within
Step 3, 3a is the real near-term target; 3b stays design-only until a real
candidate exists to validate it against — see the correction in 3b's
section above (2026-07-05).
