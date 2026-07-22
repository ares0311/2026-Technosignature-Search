# Systematic Search Plan

## STOP — LABEL ACQUISITION IS NOT A PROJECT STEP

Only pre-existing, independently supplied, row-level labels with provenance may
be used for training, calibration, threshold selection, or evaluation. Never
ask the user or anyone else to create labels; never build a review/annotation
queue; never infer labels from automated filters, papers, anomalies, or
follow-up states. No positive technosignature labels exist. If the available
labels are insufficient, the relevant learned-model gate stays fail-closed.
This rule supersedes every older human-review-set proposal in project history.

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

## Current honest state (updated 2026-07-21; originally recorded 2026-07-05)

**Current open phase — real unknown/adversarial acceptance:** a code-path audit
found that `run_pipeline` scored radio candidates
without calling the implemented Track A catalog resolver, satellite matcher,
Track B gate, or adversarial dossier. In addition, the pre-1.2.44 Track B gate
requires an anomaly threshold that cannot be established from the available
pre-existing labels, making `unknown_candidate` unreachable. This was an
architecture error: anomaly scoring ranks results; it does not define whether
all known explanations failed. Version 1.2.44 repairs the integrated code path:
it durably emits `known`, `unknown`, or `unresolved`, and automatically creates
an adversarial dossier for `unknown`. Real retained Voyager and HIP107788 data
verify `known` and `unresolved`; unit and dispatch tests verify `unknown` and its
dossier. The retained corpus has no real cadence-complete observation that can
reach `unknown`. Do not call Hunter PROD before an installed-entry-point run on
real complete evidence proves that remaining branch.
Retained-data follow-up `SEARCH-20260722T012732Z-759A1D93` from code commit
`10dfb9e` now proves the
installed entry points propagate HIP103096's `unresolved` state and exact
evidence into the durable follow-up ledger; it does not close the missing real
`unknown` branch.

**First approval-gated Hunter acquisition — 2026-07-21:** HIP107788 completed
the immutable new-target lifecycle after one loud, durable DNS failure and an
approved resumable retry. The 264,353,134-byte raw HDF5 was downloaded inside
the repository workspace, processed at the reviewed 10 Hz/s drift ceiling, and
evicted only after its DAT and candidate report existed. The real run exposed a
fail-open interpretation defect: uncalibrated heuristic weights had been labeled
as probabilities and missing OFF observations were rewarded as OFF absence.
Version 1.2.42 fails closed to deterministic local follow-up triage, makes the
missing cadence/Earth-drift/repeat/calibration limitations explicit, requires an
eligible Track B result before radio expert-review escalation, persists raw-to-
DAT provenance before future evictions, and keeps every acquisition attempt in
append-only status history. No detection, unknown-candidate, or calibrated
performance claim follows from the 10 HIP107788 hit rows.

The corrected retained-evidence acceptance search
`SEARCH-20260721T173605Z-0F6693E8` subsequently completed three targets at code
commit `63713b0` with zero downloads and three local DAT reuses. All results
fail closed to `human_review_queue` /
`needs_local_deterministic_follow_up_triage`, preserve their evidence and
recommended next action, and deny detection and external submission. A second
execution attempt fails without changing the immutable manifest or append-only
event ledger. The Hunter core lifecycle is therefore production-complete;
later-epoch ON/OFF observations and broader identity resolution remain science
coverage work, not hidden workflow bridges.

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

**Hunter lifecycle handoff — 2026-07-19:** `Create-New-Search` now freezes the
exact new or follow-up selection in an immutable, hash-stamped durable search
manifest; `Run-New-Search` consumes that manifest without regenerating targets,
uses append-only lifecycle events, isolates output, and remains resumable;
`Show-Follow-Ups` aggregates durable production ledgers with resolved identity,
evidence, prior-run provenance, deterministic priority, and a recommended next
action. The real local read-only registry excludes rows whose target identity
cannot be reliably tied to the candidate catalog. The approval-gated HIP107788
run and corrected retained-evidence rerun now close the Hunter lifecycle
acceptance gap. The durable public-archive namespace now contains 12,086
nonempty unique labels, but only 1,184 resolve exactly to current queue
identities and 358 are ranking-eligible; unresolved labels remain fail-closed.

**Step 0 completion handoff — 2026-07-12 23:58 UTC:** PR #251/version 1.2.1
is merged (`5507030`) and all six isolated shards completed 33/33 targets with
198 combined downloads, 198 evictions, zero failures, zero warnings/errors,
and no duplicate target observed by the one-minute process monitor. Six
distinct per-shard v1.2.1 entries with complete target detail are tracked in
`docs/data_collection_status.json`. The corrected corpus contains 215/215
10-Hz/s `.dat` files and zero 4-Hz/s files. Corrected ingestion reports 8,988
raw rows, 3,134 exact normalized duplicates across 39 files, and 5,854 unique
rows across 215 targets; 4,895 unique rows carry cross-target RFI flags and zero
are follow-up or escalation-ready candidates. Raw retention returned to 17 HDF5
files and data usage to 9.0 GB.
Step 0 is complete. Do not repeat bulk acquisition or infer labels from these
automated filters. Step 1 is now a documented fail-closed limitation; label
acquisition is permanently outside project scope.

| Capability | Status |
|---|---|
| Pipeline processes real data end-to-end per file/target | ✅ Real, repeatedly demonstrated (Voyager, HIP99427, all 18 KIC 8462852 quarters) |
| Track A known-explanation classification | ✅ Integrated into the production radio path; real Voyager=`known`, HIP107788=`unresolved` |
| Track B known/unknown resolution | ⚠️ Implemented; `unknown` is reachable without anomaly calibration and dispatch-tested, but lacks a real cadence-complete installed-Hunter acceptance observation |
| Semisupervised anomaly/OOD calibration | ❌ Unavailable for probability/threshold claims; ranking-only and not a blocker for known/unknown resolution |
| Operator UI hardening | ✅ Hunter lifecycle surface verified with a real approval-gated `Run-New-Search`: compact create/follow-up tables, visible acquisition progress, scriptable JSON where useful, loud non-zero failure, same-search resume, and actionable follow-up recommendation. Existing broader production surfaces remain as documented in Step 2. |
| Detection-optimized target selection algorithm | ⚠️ 3a ranks by the real config-driven `target_selection_score`, including production-scan history; the policy sum remains auditable but is no longer the selector. `Create-New-Search` durably freezes exact selections, while follow-up mode ranks resolved real ledger evidence separately. Metadata discovery/size preflight cover the full 1,703-target HPRC queue. Successful batch-3 resume records bring completed controls to 805, leaving 358 sized URL-available targets (89.274678 GB) and 540 completed no-product results. The live archive namespace adds 12,086 durable candidate labels, but exact queue-alias resolution currently yields 1,184 identities and only those same 358 ranking-eligible targets; the remaining labels are not guessed into viability. This is an inventory, not raw-download approval. See Step 3a. |
| Extended-corpus completion | ✅ Complete — corrected v1.2.1 six-shard rerun finished 198/198 targets with zero download-task duplication. The full 215-target local corpus is at 10 Hz/s; ingestion removes 3,134 exact duplicate hit rows from 8,988 raw rows, leaving 5,854 unique triage rows and zero follow-up/escalation-ready candidates. See Step 0 completion below. |

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

The paragraphs formerly here instructed agents to resume a 554-target bootstrap
and build a 1,000-row human-review set. Both instructions are superseded and
must not be executed: the corrected 215-target corpus is complete, and creating
new labels is outside project scope. Future acquisition is Step 3a
metadata-first, detection-priority work and remains separately approval-gated.

---

## Step 1 (permanently fail-closed): document the unavailable calibration evidence

The search for real per-hit labeled SETI/BL data is exhausted
(`docs/seti_labeled_hit_data_research.md`), and no qualifying pre-existing
row-level label source was found. HIP99427's frozen 124-row artifact contains
project-generated cadence outcomes; it is legacy diagnostic evidence, not
ground truth, and is unauthorized for training, calibration, threshold
selection, or scientific evaluation. The previously proposed project-owned
human review set, `radio-review-sample` workflow, label writers, and
label-trained model commands were invalid because this project does not ask
anyone to create labels; they are retired.

**Required behavior:**

1. Keep the semisupervised anomaly score as an uncalibrated ranking diagnostic,
   not a classification or promotion gate.
2. Keep Track B fail-closed wherever adequate independent labels are required.
3. Use unlabeled real observations only for search, ranking, distributional
   analysis, and deterministic false-positive investigation. Do not turn them
   into ground truth.
4. Do not repeat the closed literature search without a genuinely new published
   dataset lead, and do not replace missing evidence with synthetic, inferred,
   automated, expert-requested, or user-created labels.
5. Continue with deterministic false-positive rejection and other named roadmap
   gaps that do not depend on unavailable labels. The current internal synthesis
   is `docs/False_Positive_Technosignature_Case_Studies.md` and its bibliography.

Version 1.2.16 removes the residual executable label-dataset summary and
score-against-labels commands that mapped project-generated legacy cadence
outcomes to pathway accuracy. The frozen artifact remains diagnostic-only;
there is no replacement label path.

Version 1.2.17 completes that boundary for the old synthetic human-review
subsystem by deleting its queue, consensus-label, consensus-export, and label-
completeness entry points and fixtures. `human_review_queue` remains only a
conservative local routing value, not a labeling workflow.

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

**Cadence-triage handoff regression fixed, 2026-07-14:** the version 1.2.11
rename from project-label review fields to unlabeled triage fields left the
compact `gbt-cadence-abacab-review` formatter reading the retired
`review_summary` key. JSON contained the two-rule agreement evidence, but the
default operator surface silently omitted it. Version 1.2.13 reads
`triage_summary`, prints independent-rule agreement/disagreement, and has a
compact-output regression assertion.

**Production-run picker count regression fixed, 2026-07-16:** a real workflow
replay found that `prod-runs` labeled the latest run's 39 loaded outcome
records as “Candidates,” while `prod-target-status` correctly reported 34
unique targets and zero follow-up candidates. Version 1.2.14 carries the
manifest's unique-target count into the run summary and prints distinct
`Targets` and `Records` columns, so zero-hit observations and repeated
artifacts cannot inflate the operator's apparent candidate count.

**Production-scope terminology fixed, 2026-07-16:** the same real operator
replay showed that machine-readable production disclaimers and two CLI help
strings still called this a citizen-science workflow, contradicting the active
publication-grade automated-triage mission. Version 1.2.15 changes new outcome
scope to `local_production_triage_only` while retaining every conservative
no-claim and no-external-submission guardrail.

Remaining Step 2 work must continue from a workflow audit of the other current
UI surfaces (especially any operator handoff views outside the candidate
packet path) against real operator workflows: reviewing a candidate, reviewing
a non-detection ledger, and approving/rejecting a follow-up. Do not guess that
a UI is hardened because it has a command; verify the operator can answer the
next review question without paging through raw machine output.

**Candidate extraction handoff view fixed, 2026-07-16:** the workflow audit
this section calls for found exactly the operator handoff view outside the
candidate packet path it names: `candidate-extraction-handoff-summary` had no
`--json` flag at all and always printed raw indented JSON for a ~20-key
aggregate (per-track/per-extraction-status breakdowns, several count fields).
Version 1.2.26 gives it the same compact-default/`--json`-opt-in treatment as
its siblings.

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

   **Archive-wide namespace expansion, 2026-07-19:** the official backend
   documents `api/list-targets` as the distinct target names currently present
   in its files database. A real serial request returned 12,087 rows (one blank,
   12,086 unique nonempty labels). The committed
   `data_selection/bl_archive_candidate_catalog.csv` assigns stable IDs and
   resolves only exact aliases already documented by the priority queue:
   1,184 resolved, one ambiguous, and 10,901 unresolved. Only 358 resolved rows
   inherit existing ranking eligibility. Suffixes such as `_R`, `_S`, and
   `_B1` are preserved as unresolved archive labels rather than guessed to be
   distinct objects or silently collapsed. File-level coordinate/type/URL
   enrichment remains required before an unresolved row can become viable.
   `Create-New-Search` binds this catalog and the separate priority queue into
   `hunter_search_manifest_v3` with independent hashes/counts, so the universe
   is no longer conflated with or manually bridged to the eligibility stage.
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
   entry for the full root cause and regression test. At that two-round
   checkpoint, the queue reported 29 targets in
   `raw_download_approval_required`, consolidated in
   `data_selection/batch_manifests/local_coverage_raw_download_approval_manifest.json`
   (~7.41 GB combined) as the review input for explicit bounded raw-download
   approval. Later rounds supersede those counts. This same discover →
   preflight → promote pattern is the
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
   **Superseded execution status, 2026-07-14:** `batch3` through `batch13` and
   the 1,358-target `batch14_bulk` discovery/size-preflight round are complete;
   see `data_selection/batch_manifests/README.md` for measured per-round counts.
   A live URL-encoded retry also closed the ambiguous pre-fix
   `DENIS-P J1048.0-3956` result: the request succeeded and found no current
   GBT HDF5 product. No raw payload was downloaded.
4. Wire the computed `novelty_score` into `target_priority_score()`'s
   existing weighting, don't reinvent the scoring formula. **Done in queue
   schema v2:** rows retain the policy-required additive `total_priority` for
   audit, record the base `background_target_priority_score`, and use the
   existing config-versioned `target_selection_score()` (including real
   production-scan review history) as the queue/manifest ranking key.
   Manifests sort independently instead of trusting incoming CSV order.

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
Step 0 (complete corrected extended corpus)
  -> do not repeat the bootstrap; use its real outputs for deterministic validation
Step 1 (permanently fail-closed learned calibration)
  -> never acquire labels; keep the anomaly score ranking-only and dependent gates closed
Step 2 (UI hardening)
  -> precedes Step 3 per explicit user sequencing direction
Step 3a (novel-target selection: real metadata-first queue exists)
  -> future raw acquisition remains explicit-approval and storage-policy gated
Step 3b (follow-up-target selection)
  -> design only; implementation waits on a real qualifying candidate existing —
     do not build/merge scoring code against a backlog that doesn't exist yet
```

Steps 0 and 1 are terminal states, not active work. Step 2 is substantively
underway and Step 3a has a real metadata-first queue; neither status authorizes
raw downloads. Step 3b stays design-only until a real candidate exists to
validate it against.
