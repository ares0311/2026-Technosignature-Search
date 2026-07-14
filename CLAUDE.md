# CLAUDE.md

## STOP — NEVER ASK ANYONE TO LABEL DATA

This project uses only **pre-existing, independently supplied, row-level
labeled data with provenance** for training, calibration, threshold selection,
or scientific evaluation. Never ask the user or anyone else to label, annotate,
classify, or review data to create labels. Never propose or build a labeling
queue, paid annotation effort, expert-labeling request, citizen-science task,
or project-owned review set. No positive technosignature labels exist; anomaly,
`follow_up`, `unknown_candidate`, synthetic injections, Voyager, and known
human transmitters are not substitutes. When sufficient labels do not exist,
keep the relevant gate fail-closed and work on a different named science gap.
The prime directive in `AGENTS.md` overrides any stale contrary wording.
A Track A CNN/classifier may learn pre-existing labels for known explanations
and abstain with `low_confidence`; an unclassified item is a follow-up triage
input, not a positive technosignature label, and must still pass Track B.

## Purpose

Handoff and progress notes for Claude or other coding agents working in this repository.

**AGENTS.md is the single source of truth for all directives** — git sync,
PR link + continuation, parallelization (general and data-collection),
data-collection status reporting, agent branch sync, git artifact hygiene,
the primary directive (review chain, Track A/B gate, CNN promotion gate),
anti-doom-loop rules, target selection philosophy, the mandatory
session-start protocol, file-location/root-cause/prior-task-validity/
summary-skepticism rules, non-negotiable scientific rules, environment and
performance rules (including macOS `caffeinate`), testing requirements, and
data policy. None of it is duplicated below. Read `AGENTS.md` first, every
session; where anything below appears to conflict, `AGENTS.md` governs.

## MANDATORY SESSION-START PROTOCOL

Do not plan or execute anything until you have called `Read` on `AGENTS.md`,
`docs/PRODUCTION_READINESS.md`, and `docs/SYSTEMATIC_SEARCH_PLAN.md` this
session — see `AGENTS.md` for the full protocol, including the "resume
directly" carve-out and the required shape of your plan.

## Current Phase Snapshot

Current phase: Phase 0 is complete. Phase 1's anomaly/OOD calibration is a
documented fail-closed limitation because no adequate pre-existing labeled
dataset exists (`docs/PRODUCTION_READINESS.md`). New labeling is prohibited.
Every commit must advance a named science phase or directly unblock its safe
execution; see `AGENTS.md`'s ANTI-DOOM-LOOP DIRECTIVES for the full hard-rule
list (PRs #103–#119 precedent).

Current execution status:
 - The corrected 215-target radio corpus is complete at the valid 10 Hz/s drift
   ceiling. Corrected ingestion removes 3,134 exact normalized duplicates from
   8,988 raw rows across 39 files, leaving 5,854 unique rows; 4,895 carry
   cross-target RFI flags and no follow-up or escalation-ready candidates
   survived automated triage. One GJ412A observation contains a two-member
   100-MHz harmonic-family match (13th/17th harmonics, 191-Hz residual), which
   is deterministic RFI-forensics evidence, not a label. Version 1.2.5 wires
   those family flags into triage; the union of cross-target and family checks
   rejects 4,896 unique rows while leaving zero survivors. Version 1.2.6 also
   runs this diagnostic on normalized hit-NDJSON rows grouped strictly by their
   supplied `source_artifact`, never by an inferred observation identity.
 - Version 1.2.7 corrects a provenance bug in combined-corpus review:
   paper-level public-null context is retained as metadata but no longer acts as
   a per-row rejection or label. The full read-only 205,857-row review leaves
   1,072 unlabeled automated triage survivors; 1,069 are blocked by target/source
   context and the remaining 3 share a source artifact, so 0 are independently
   escalation-ready. These are follow-up triage items, not positive labels or
   detection claims.
 - Version 1.2.8 streams the complete local 2,028,537-row MeerKAT JSON source
   for explicit candidate-frequency neighbors without creating another corpus.
   At ±500 Hz, each of the three source-context survivors occurs exactly once.
   Their two complete observation artifacts contain harmonic-family RFI, but
   none of the three rows belongs to those families. They remain unresolved,
   unlabeled triage items; no deterministic rejection or escalation is claimed.
 - Training, calibration, threshold selection, and scientific evaluation use
   pre-existing independently labeled row-level data only. Never ask the user
   or anyone else to label data, and never build a label-acquisition queue.
 - The retired 1,000-row unlabeled radio sample is not calibration or evaluation
   evidence. The anomaly scorer remains ranking-only and Track B fails closed
   wherever calibrated anomaly evidence is required.
 - Future approved six-manifest data batches use
   `scripts/run_six_shard_downloads.py`, not six manual terminal tabs.
 - Full validation uses `scripts/run_parallel_validation.py` (six xdist
   workers/six non-overlapping test shards, then concurrent app-version,
   static, and science checks). `scripts/check_app_version.py` requires every
   release-relevant branch change to advance the version beyond `origin/main`
   and requires package/readiness version surfaces to agree. `AGENTS.md`
   remains the directive source of truth.

---

## VISIBLE PROGRESS + COMPACT OUTPUT DIRECTIVE — NON-NEGOTIABLE

Long-running commands must prove they are alive without flooding the terminal.
The current production operator preference is compact progress, not verbose
logs that require paging.

Mandatory requirements:

1. `prod-scan` and `scripts/run_production_scan.sh` are the canonical local
   production scan entry points. They must keep Rich spinner/fallback progress,
   compact per-target completion rows, target-status JSON, follow-up and
   non-detection ledgers, clean Ctrl+C handling, and `--resume-run-dir` support.
   They must fail closed when no candidate manifests are loaded from `results/`;
   a zero-candidate run is diagnostic-only and requires explicit `--allow-empty`.
2. Full JSON, provenance, diagnostic detail, and ledgers belong in
   `results/scans/RUN-*` artifacts, not streamed continuously to the console.
3. Download scripts may use progress bars and concise `[INFO]`/`[OK]` lines.
   Production scan scripts should not use `set -x` by default.
4. Commands given to the user must start with `git pull origin main`. Long runs
   must wrap the child process with `caffeinate -i`.
5. `prod-file-scan` and `tui.py` are lower-level file-oriented diagnostics.
   Do not present them as the main overnight production-ledger workflow.

---

## SHARDED EXECUTION DIRECTIVE — NON-NEGOTIABLE

`AGENTS.md` is authoritative. From this point forward, all agents must default
to the repo-native optimized sharded/multiprocess path whenever bounded
parallelism materially reduces wall time and scopes/concurrency are verified
safe:

- `scripts/run_six_shard_downloads.py` replaces six manual download terminals
  for explicitly approved, committed six-manifest `stream_process_evict`
  batches. It validates non-overlap, the 100GB peak-chunk budget, completion
  state, per-shard logs, and aggregate CPU slots before launching anything.
- `scripts/run_parallel_validation.py` is the canonical full validation entry
  point: six pytest-xdist workers are six non-overlapping `loadfile` shards
  with aggregated package coverage; Ruff, mypy, and `validate-all` then run
  concurrently.

Do not reconstruct either workflow with ad hoc background shell commands. Do
not ask the operator to open extra tabs when the repo-native launcher applies.
Small focused test reproductions may run directly when sharding would not save
time. Download approval, metadata-first selection, and the 100GB cap remain
unchanged.

---

## Current Live Handoff — 2026-06-27

### First `stream_process_evict` Batch Complete — 198/198 Targets, 2026-07-12

The first bounded `stream_process_evict` batch (`local_coverage_first_bounded_batch_manifest.json`,
198 targets / ~49.9GB from the `raw_download_approval_required` queue) is
fully complete: **198/198 targets downloaded, processed, and evicted; 0
failures.** Executed via `scripts/run_stream_process_evict_batch.sh`
(new script this session) sharded across 6 manifests
(`local_coverage_first_bounded_batch_shard{1-6}_manifest.json`, ~33 targets
each) run in parallel across 6 terminal tabs on the user's own machine —
this sandbox's own outbound network is capped at a confirmed ~200KB/s
aggregate (verified empirically: 2 concurrent connections got the same
combined throughput as 1), so the actual bulk download had to run outside
the sandbox. Real local storage stayed at ~9GB throughout (never
accumulated), confirming the stream_process_evict eviction design (raw
HDF5 deleted immediately after each target's candidate report is
confirmed) holds up under sustained real multi-hour, multi-shard load.

Corpus now has 215 `.dat` files and 237 candidate report manifests
(cumulative, includes prior corpus). This is real negative/candidate
triage evidence only — not a detection, discovery, or external-submission
claim.

**Two real bugs found and fixed live during this run:**
1. `turbo_seti==2.3.2` (newest PyPI release, no upper numpy bound) crashes
   on a real off-by-one bug in its own trailing debug-log line
   (`find_doppler.py`, formats a length-1 array with `%i` instead of
   indexing `[0]`, as the same file does correctly three other times) once
   numpy>=2.0 is resolved. Fixed via a one-line site-packages patch
   (`scripts/patch_turbo_seti_numpy2_compat.sh`, idempotent, required again
   after any fresh `radio`-extra install) — documented in `AGENTS.md`'s
   Environment Rules.
2. The batch script's own console-visibility bug: `log()` only wrote via
   plain `echo`, so a caller redirecting output with `> file 2>&1` (rather
   than `| tee file`) got zero visible terminal output for the
   many-minutes-long gaps between progress lines — looked hung even though
   it was working (confirmed via the log file). Fixed: `log()` now always
   writes to both console and an auto-derived (or `--log-file`-specified)
   log file; no caller-side `tee` needed.

**Two real operational incidents, both caught and corrected:**
1. Editing `run_stream_process_evict_batch.sh` while a background instance
   of it was still executing (to add the resume-check/progress-polling/
   interrupt-trap fixes) corrupted one in-flight download (`GJ273`,
   became an oversized/corrupted file that a naive size-only resume-check
   would have treated as "complete" forever). Root cause: bash reads a
   running script's file incrementally from disk: modifying it mid-execution
   is undefined behavior. Fixed by deleting the corrupted file (forcing a
   clean re-download) and adopting a hard rule: never edit a script while
   any instance of it is executing. GJ273 backfilled successfully on retry.
2. Two throwaway test runs (against a scratch `data_cache/test_slice_manifest.json`,
   not a real batch manifest) auto-committed and pushed fabricated
   `stream_process_evict_batch` status entries to the canonical, tracked
   `docs/data_collection_status.json` on `main` — the same incident class
   already documented below under "Git-Add-Safe Label Regeneration" and
   `AGENTS.md`'s DATA COLLECTION STATUS REPORTING DIRECTIVE, now hit a
   second way (real canonical path, fake/test manifest data, rather than a
   redirected path). Both commits reverted (`git revert`, pushed). Fixed at
   the root: the script now only calls `record-data-collection-status` when
   the manifest path is under the canonical `data_selection/batch_manifests/`
   directory; scratch/test manifests are silently skipped.

**Resolved in v1.2.2:** parallel status updates are serialized by the existing
ignored-path process lock in `data_collection_status.py`, and the stream runner
now invokes turboSETI and the pipeline only on each shard's current target
directory. The one-terminal launcher additionally validates cross-shard target
non-overlap and gates simultaneous post-processing, so future six-shard runs do
not recreate the earlier shared-corpus scan or status-publication races.

**Not yet done:** the remaining ~949-target / ~239GB balance of the
1,147-target `raw_download_approval_required` queue is still queued; this
batch was explicitly sized to ~50GB to leave a wide safety margin, not the
whole queue. Next bounded batch needs the same discover→preflight→promote
→ size-cap pattern before download.

### HARD LOCAL STORAGE CONSTRAINT — NON-NEGOTIABLE — 2026-07-11

**This project has no external SSD and no cloud storage available for
testing.** The user, verbatim: "we can't use more that 100G of local store
ever. We can't use external storage to test. Work within these
constraints." This overrides the 4TB-external-SSD assumption baked into
`docs/astrometrics_data_selection_policy.md` and
`docs/astrometrics_external_and_cloud_storage_policy.md` (both now carry a
"Current Reality Override" section at the top — read those, not the 4TB
tables below them, for this project). Enforced in code:
`TECHNO_LOCAL_STORAGE_CAP_GB` in `scripts/download_bl_extended_corpus.sh`
(default 100GB), checked against the sum of `data/` + `models/` +
`artifacts/` before every payload download. Real usage as of 2026-07-11:
~9GB, leaving ~91GB of headroom.

Practical consequence: the `raw_download_approval_required` queue
(1,147 targets, ~289GB as of `batch14_bulk`) can never be bulk-downloaded —
it's ~3x the cap. Discovery/size-preflight (free, metadata-only) can keep
running against the full queue, but any actual raw download must be a
small `stream_process_evict` batch (download → turboSETI/pipeline →
evict raw payload → repeat), sized to fit real remaining headroom, not the
old 250GB-per-batch defaults in the data-selection policy doc.

**Root cause found and fixed while implementing this:** the download
script's existing `content_length_kb()` used gawk's `IGNORECASE`, which
macOS's real `/usr/bin/awk` (BWK awk) doesn't support — it silently never
matched a real `Content-Length:` header and always returned 0, making the
pre-existing free-space-reserve check (and the new cap check) a no-op on
macOS. Fixed with a portable `tolower()` comparison, PR includes a
regression test that caught it via a real fake-curl HEAD response.

**Also found and fixed, same session:** manually testing this by pointing
`TECHNO_DATA_COLLECTION_STATUS_PATH` at a repo-local scratch path
auto-committed and pushed that scratch file to `main` three times for
real — `commit_and_push_status()` only guarded against running off the
`main` branch, not against `status_path` being redirected away from the
canonical `docs/data_collection_status.json`. This is the second time this
exact class of incident happened (see `docs/PRODUCTION_SCAN_RUNBOOK.md`'s
earlier note on the same function). Added a canonical-path guard plus a
regression test so it can't recur a third time.

### Step 3a Bulk Discovery Round (`batch14_bulk`) Complete — 2026-07-11

After 13 sequential 25-target rounds (`top25` through `batch13`, 211 targets
promoted, ~53.15 GB), the user flagged the per-round pace as unsustainable
for the remaining 1,358 queued targets. Consolidated all of them into one
manifest, `local_coverage_batch14_bulk_manifest.json` (zero overlap with
prior rounds, confirmed), and hardened
`scripts/download_bl_extended_corpus.sh` first: added bounded-parallel
discovery workers (`TECHNO_EXTENDED_CORPUS_DISCOVERY_WORKERS`, default 4)
and compact `[PROGRESS] X/Y checked (elapsed Xm, ETA ~Ym remaining)` output,
per the VISIBLE PROGRESS DIRECTIVE (the sequential-only version had neither).

**Real live run result:** 1,358/1,358 targets checked in 13m53s wall-clock
(vs. the ~50-60 min sequential estimate) — 936 URL-available, 422 skipped
(no HDF5 URL). All 936 then passed HEAD-only size preflight cleanly
(`all_targets_ok: true`, `all_targets_sized: true`), totaling 235.825276 GB.
Target-priority queue rebuilt (auto-glob merge of every
`*_discovery_result.json`/`*_size_preflight_report.json`, per the
already-fixed merge mechanism) and the consolidated approval manifest
regenerated: **`local_coverage_raw_download_approval_manifest.json` now
covers 1,147 targets, ~288.97 GB combined**, across all rounds so far.
Committed as `00a8c3a` and pushed to `origin/main`.

None of this authorizes a raw download — `raw_download_authorized: false`
in every preflight report, same as every prior round. The 1,147-target,
~289 GB queue is still awaiting the user's own bounded-download approval
decision, not yet requested this round.

**Git-LFS push note:** `git push` still prints a spurious
`fatal: failed to store: 100001` line (the sandbox-proxy TLS issue on
git-lfs's unused locking-API sub-call, `lfs.locksverify` global fix already
applied) but the push itself succeeds — verified via
`git rev-parse origin/main HEAD` matching after every push this round. Don't
treat that error text alone as a failed push; always verify with
`git log origin/main..HEAD` or `git rev-parse origin/main HEAD` before
retrying or asking the user to intervene.

### Calibration-Data Literature Search Closed — 2026-07-05

PRs #226-#227 merged. The open question "does any published BL/SETI paper
have real per-hit labeled data to calibrate `semisupervised_anomaly_score`"
is answered: **no**. The user's research agent checked 8 real sources
(Enriquez 2017, Price 2020, Sheikh/Smith 2021 BLC1, Jacobson-Bell 2025/
GLOBULAR, Lacki 2021 Exotica Catalog, Ma 2023, Choza 2024) against a strict
acceptance rule and none qualified — full findings in
`docs/seti_labeled_hit_data_research.md`, project record in
`docs/PRODUCTION_READINESS.md` Phase 1 and `AGENTS.md`'s "CALIBRATION DATA
STATUS" section. **Do not re-run this search on the same question.** The
124-row HIP99427 set (2 `follow_up` rows) remains the only real labeled
data in hand and is insufficient for a global threshold. The project uses
pre-existing independently labeled data only: do not ask anyone to create
labels, build a label-acquisition queue, infer labels, or re-run the exhausted
search without a genuinely new already-labeled source.

### Track A Real Baseline Results — 2026-07-02

PRs #170-#176 merged (Track A implementation + fixes). `main` is at commit
`f94e403`. The user ran the full Track A acquisition/training sequence
locally against real hosts (this sandbox cannot reach any of them) and it
now has a real, executed, tested baseline — closing the brief's
"tested, reproducible baseline" gate for Phase 0-2.

**HTRU2 (Phase 1 baseline):** 17,898 rows acquired (`ucimlrepo`, exact match
to the documented dataset size). Trained 3 candidate models, held out 20%
(3,580 rows):
- `logistic_regression`: F1=0.883, precision=0.948, recall=0.826
- `hist_gradient_boosting`: F1=0.895, precision=0.920, recall=0.872
- `random_forest`: F1=0.896, precision=0.925, recall=0.869 — **best model,
  selected automatically**, saved to `models/track_a/htru2_random_forest.joblib`
  (local, gitignored, not redistributed)

**Catalog acquisition (Phase 2):** all four fixed-sky-position catalogs
acquired from live hosts:
- ATNF pulsars via `psrqpy`: 4,393 rows
- CHIME/FRB Catalog 1 via VizieR: 600 rows (exceeds the brief's 536-burst
  snapshot — catalog has grown)
- Roma-BZCAT blazars/AGN via VizieR: 3,561 rows (exact match)
- Fermi 4FGL-DR4 gamma-ray sources via FSSC FITS: 7,195 rows (one more than
  the brief's 7,194-row snapshot — real catalog drift, not a bug)

**Two real bugs found and fixed live (PR #176):**
1. Roma-BZCAT's VizieR `RAJ2000`/`DEJ2000` columns are sexagesimal text
   (`'00 00 20.39'`), not decimal degrees like CHIME/FRB's identically-named
   columns — `normalize_romabzcat`/`normalize_chime_frb` now try decimal
   float first and fall back to `astropy.coordinates.Angle` sexagesimal
   parsing.
2. Fermi 4FGL-DR4's FITS table has multidimensional per-energy-band flux
   columns (`Flux_Band`, `Sqrt_TS_Band`, etc.) that crash
   `astropy.Table.to_pandas()` directly — `fits_table_to_pandas()` now drops
   non-scalar columns before conversion.

Also fixed live: a stale `.venv/bin/pip` shim bound to a leftover
`python3.13` site-packages directory from before this venv's Python was
upgraded to 3.14.3 (packages "successfully installed" were never importable
from the actual interpreter `techno-search` runs under) — use
`.venv/bin/python -m pip install` going forward, documented in `AGENTS.md`.
An `SSL_CERT_FILE` macOS python.org-installer certificate issue was also
resolved by pointing at the already-installed `certifi` bundle (not a TLS
verification bypass).

**Not done:** CelesTrak/SatNOGS satellite-transmitter matching (needs SGP4
orbital propagation against an observation timestamp, not a static sky
position — deliberately deferred, documented in `PRODUCTION_READINESS.md`).

### Phase 3 Historical Replay — Real Results, 2026-07-02

PR #178 merged (`track-a-historical-replay` CLI + `track_a_replay.py`). The
user ran `techno-search track-a-historical-replay --sample-size 3` against
their real locally-acquired catalogs. **Result: 13/13 recovered,
`all_recovered: true`:**
- 3 real ATNF pulsars (J0002+6216, J0006+1834, J0007+7303) — all
  `known_pulsar`
- 3 real CHIME/FRB bursts (FRB20180725A, FRB20180727A, FRB20180729A) — all
  `known_frb`
- 3 real Roma-BZCAT blazars (5BZQ J0000-3221, 5BZQ J0001-1551,
  5BZQ J0001+1914) — all `known_blazar_agn`
- 3 real Fermi 4FGL gamma-ray sources (4FGL J0000.3-7355, 4FGL J0000.5+0743,
  4FGL J0000.7+2530) — all `known_gamma_ray_source`
- negative control (RA=180.0, Dec=-89.5) correctly reported `no_known_match`
  with all 4 catalogs loaded (not a false positive)

**This satisfies the brief's explicit gate.** Both conditions the brief
requires before Track B can start are now genuinely met with real data:
"Track A has a tested, reproducible baseline" (Phase 1/2, PR #171-177) and
"historical replay work" (Phase 3, this result).

**Track B (`unknown_candidate` routing) itself is still not started.**
Before implementing it:
1. CelesTrak/SatNOGS satellite-transmitter matching is still the one missing
   Phase 2 catalog (needs SGP4 propagation against an observation timestamp).
2. The brief's Phase 4 gate requires 9 conditions, most of which already
   exist as separate, unwired radio-pipeline features from earlier Phase 0/1
   work: RFI database overlap (`rfi_database.py`), instrumental artifact
   score, ABACAB cadence score (PR #125), semisupervised anomaly scorer
   (trained on 200k real MeerKAT rows). These need to be combined into one
   gate function alongside the Track A catalog cross-match.
3. How `unknown_candidate` integrates with the existing `Pathway` enum /
   `score_candidate()` routing in `schemas.py`/`scoring.py`/`pathway.py` is
   an architecturally significant decision — get explicit user direction
   before touching that shared, already-tested code path.

### Track B Real End-to-End Run — 2026-07-02

PRs #180-#184 merged (all by another concurrent session, discovered when
this session's own local, unpushed CLI-wiring commit turned out to duplicate
already-merged, better-designed work — discarded rather than pushed, per the
SUMMARY SKEPTICISM / PRIOR TASK VALIDITY rules):
- #180: CelesTrak/SatNOGS satellite-transmitter matching
  (`track_a_satellites.py`, SGP4 propagation via `skyfield.EarthSatellite.
  from_omm()`)
- #181: Track B Phase 4 gate (`track_b_gate.py`,
  `track_b_unknown_candidate_gate()`) as a separate, additive function — not
  wired into the shared `Pathway` enum/`score_candidate()` — plus a real
  CelesTrak SATCAT URL bug fix (`records.php?FORMAT=CSV` is rejected by the
  live API; fixed to the verified working `https://celestrak.org/pub/
  satcat.csv`)
- #182: `techno-search track-b-unknown-candidate-gate` CLI (explicit
  `--crossmatch-json`/`--satellite-json` evidence files, no inline network
  lookups)
- #183: `techno-search track-b-candidate-readiness` — fail-closed audit of
  packet metadata/evidence completeness; also fixed radio candidate packets
  to preserve real RA/Dec/provenance (closing a gap this session had
  flagged as needing bigger architectural work)
- #184: fixed real turboSETI tabbed-sexagesimal RA/Dec header parsing bug,
  added `observation_time_utc` derived from MJD to candidate packets

**First real end-to-end Track B run, 2026-07-02:** `data/bl_hits/
voyager1_hits.dat` (real Voyager 1 X-band downlink hit, 8.419 GHz,
2016-09-19T18:46:13Z) run through the full pipeline → real Track A
crossmatch → real satellite match (using NRAO's own published GBT reference
point: 38.4331211, -79.8398350, 807.43m — verified via GBT Proposer's Guide
+ National Radio Quiet Zone reference point page, not memory) →
`track-b-candidate-readiness`. Result: **7 of 9 conditions satisfied**, 2
correctly left unresolved (`abacab_cadence_score=0.5` — single file,
insufficient cadence evidence; `semisupervised_anomaly_score=0.058` — low,
but no calibrated "high" threshold exists yet), `eligible_for_unknown_
candidate: false`. No false claim was made either way — the gate correctly
did not label a known human spacecraft signal `unknown_candidate`.

**Real scope gap surfaced by this test, not a bug:** Voyager 1 is a
deep-space probe, not an Earth-orbiting satellite, so SatNOGS/CelesTrak
(Earth-orbit catalogs) correctly report no match. None of the 9 Phase 4
conditions currently has a "known human deep-space spacecraft" category, so
Voyager-class signals fall through to "unresolved" rather than being
confidently attributed. Worth a small dedicated check in future work, not
urgent — the gate's conservative-by-construction design means this doesn't
cause any wrong claim, just an unresolved condition.

**Two blockers remain before Track B eligibility can ever resolve true:**
1. Calibrate the semisupervised anomaly/OOD threshold from real held-out
   evidence — no invented cutoff.
2. Get real ABACAB 6-scan cadence evidence (this Voyager file is a single
   observation, not a full ON/OFF cadence).

### Second Track B Blocker Closed — Real Cadence Bug, 2026-07-02

Blocker 2 above turned out to already have real evidence sitting unused: the
committed `examples/real_labeled/hip99427_citizen_science_labels_v1.json`
(124 real HIP99427 evidence groups, 2 labeled `follow_up`) was generated
before PR #125 added `abacab_cadence_score`, so it predated the feature
entirely. Re-running the existing `scripts/build_citizen_science_labels.py`
against the real local cadence CSV surfaced a real bug (PR #186, not a data
gap): `_candidate_mapping()` in `citizen_science_labels.py` built row dicts
for `build_radio_candidate()` without a `source_artifact` key, so
`_abacab_cadence_score()` saw every hit's source collapse to `""` (falsy)
and reported the neutral `0.5` instead of `1.0` for both real 3-distinct-ON/
0-OFF follow-up candidates. Fixed by adding the missing field.

**User re-ran the regeneration script after the fix — confirmed real:**
both follow-up candidates now report `abacab_cadence_score: 1.0,
on_scan_distinct_source_count: 3, off_scan_distinct_source_count: 0`.
Blocker 2 is closed with real data.

`track-b-candidate-readiness` on the fixed
`GBT_HIP99427_2016-12-30_ABACAD-group-021-...` candidate now reports only
`missing_track_b_candidate_features: [semisupervised_anomaly_score]` plus
missing `ra_deg`/`dec_deg` (needed for crossmatch/satellite match) as
remaining blockers — `citizen_science_labels.py`'s candidate-building path
never wired in the semisupervised scorer or HIP99427's real sky position,
unlike `pipeline_runner.py`'s path (fixed by PR #183/184 for the general
radio pipeline). Next candidate steps: (a) wire the semisupervised anomaly
score into `_candidate_mapping()` the same way `pipeline_runner.py` does,
(b) add HIP99427's real, catalog-verified RA/Dec (not memory-guessed) so
crossmatch/satellite conditions can resolve. Blocker 1 (calibrated anomaly
threshold) remains fully open — needs a real calibration study, not
progress from this fix.

### Real 8/9 Track B Result on a Real GBT Candidate — 2026-07-02

Rather than guess or externally look up HIP99427's sky position, the user
grepped the real raw `.dat` file header directly
(`~/technosignature-data/bl_hits/spliced_..._HIP99427_0033.gpuspec.0002.dat`):
`MJD: 57752.960949074077  RA: 20h10m52.584s  DEC: 77d14m28.005s`. Converted
using this project's own tested functions
(`hit_table_reader._coordinate_deg_or_none`,
`pipeline_runner._mjd_to_utc_iso`) rather than hand-computed trig — ra_deg =
302.7191, dec_deg = 77.2411125, observation_time_utc =
2016-12-30T23:03:46Z (matches the existing manifest's independently recorded
`utc_start: 2016-12-30T23:03:45Z` to within 1s, an internal consistency
check that passed). Injected into the fixed follow-up candidate's features,
then ran the real crossmatch (`no_known_match` — not a pulsar/FRB/blazar/
gamma source) and real satellite match (`no_known_match`, using the same
verified GBT reference-point coordinates as the Voyager run).

**Result: `techno-search track-b-candidate-readiness` reports 8 of 9
conditions satisfied** — every implemented known-source, RFI,
instrument-artifact, cadence, and satellite-transmitter check found no
explanation for this real candidate. `eligible_for_unknown_candidate:
false`, correctly, because condition 8 (calibrated anomaly/OOD threshold)
remains the sole unresolved condition. **This is not a signal of interest
or a step toward a detection claim** — it means the deterministic
rule-based checks this project has implemented so far have nothing further
to say about this candidate; the one blocking condition is a calibration
gap in the tooling, not evidence about the candidate itself. Precise
language matters here per AGENTS.md's Non-Negotiable Scientific Rules:
false positive remains the default hypothesis, and this candidate has not
been evaluated against any anomaly/OOD threshold at all yet, calibrated or
otherwise.

**Only one Track B blocker remains: calibrate the semisupervised
anomaly/OOD threshold from real held-out evidence.** This requires a real
calibration study (e.g. score distributions from a real labeled corpus with
known explanations vs. known artifacts/RFI), not an invented cutoff. No
shortcut exists for this — it is genuine unstarted scientific work, not an
implementation gap.

### Real Anomaly-Score Distribution — Calibration Attempt, 2026-07-02

Wired `semisupervised_anomaly_score` into `citizen_science_labels.py`'s
candidate path (PR #189, reusing `pipeline_runner.py`'s existing injection
pattern) and ran the user's real fitted MeerKAT-trained scorer against all
124 real HIP99427 evidence groups. Real distribution by label:

| Label | n | min | mean | max |
|---|---|---|---|---|
| `false_positive` | 81 | 0.0227 | 0.0755 | 0.0979 |
| `follow_up` | 2 | 0.0238 | 0.0456 | 0.0673 |
| `insufficient_evidence` | 41 | 0.0657 | 0.0907 | 0.0973 |

**This real evidence rules out a naive threshold, and confirms the earlier
caution against inventing one was correct.** The two real `follow_up`
candidates score *lower* on average (0.0456) than the confirmed
`false_positive` population (0.0755) — the opposite of what a
"high score = interesting" threshold would assume. A percentile-of-
false_positive threshold applied to this data would filter out the very
candidates it should flag. Two real, non-implementation reasons, not a
coding gap:
1. `follow_up` sample size is 2 — far too small to estimate any percentile
   or cutoff from.
2. The scorer was trained on real **MeerKAT** BLUSE data; this corpus is
   real **GBT** L-band data from a different telescope/instrument/frequency
   range. The feature distributions likely don't transfer well
   cross-instrument, which would explain why the model doesn't discriminate
   meaningfully between these labels here.

**Blocker 1 remains open, now with a documented reason why the obvious
first approach doesn't work on available real data.** A real calibration
either needs (a) a same-instrument (GBT) semisupervised scorer trained on
GBT-native data, or (b) a substantially larger real `follow_up`-equivalent
positive sample than n=2 before any threshold estimate would be
statistically meaningful. Neither exists yet.

### Dataset Brief Integration — 2026-07-01

`docs/technosignature_datasets_agent_brief.md` is a required project input, not
an optional note. It formalizes the next model-hardening milestone as Track A:
an auditable known-explanation classifier for pulsars, FRBs, blazars/AGN,
known gamma-ray sources, satellite/transmitter matches, terrestrial RFI,
instrument artifacts, and noise.

Do not advance Track B `unknown_candidate` routing until Track A has a tested,
reproducible baseline and source-specific catalog/provenance manifests. Track A
may emit `low_confidence`; only Track B may emit `unknown_candidate`, and that
label is a local triage queue state only. There are no positive
technosignature labels, so do not train a binary "technosignature versus not"
classifier. Do not use Kaggle SETI, Setigen, pretrained models, or synthetic
training data for the first Track A milestone.

Track A raw downloads and temporary extraction products belong in ignored local
paths (`data_cache/`, `tmp_training/`, `tmp_features/`, `artifacts/`, `models/`,
and `metrics/`). Preserve GitHub-visible continuity in sanitized docs,
manifests, schemas, checksums, tests, and source-acquisition code.

### RESULT RECORDING RULE — NON-NEGOTIABLE

**When the user pastes terminal output (validate-all, prod-scan, turboSETI, pipeline),
you MUST record the key results in this handoff section before responding.
Do NOT ask the user to run a command again if they have already run it and
pasted the results — even across sessions. This file is the memory between sessions.**

### Git-Add-Safe Label Regeneration — 2026-07-02

The user reminded agents that their standard cadence is `git add .`; scripts
must work around that design feature. Root cause found: the normal
`scripts/build_citizen_science_labels.py` default overwrote the tracked
`examples/real_labeled/hip99427_citizen_science_labels_v1.json` fixture, so
routine local diagnostic regeneration made `git add .` stage a generated diff.
Fix: normal runs now default to ignored
`tmp_training/real_labeled/hip99427_citizen_science_labels_v1.local.json`.
Refreshing the committed fixture requires explicit `--update-committed-fixture`
or an explicit `--output` path. Keep this pattern for any future scripts that
produce both local diagnostics and committed reference fixtures.

### Extended-Corpus Download Result — 2026-07-02

The user pasted a completed run of:

```bash
git pull origin main
caffeinate -i bash scripts/download_bl_extended_corpus.sh --manifest data/target_sample_manifest.json 2>&1 | tee /tmp/bl_extended_corpus_download.log
```

Measured result: 31 manifest targets checked, 11 new URL-available HDF5
downloads completed, 6 existing HDF5 targets reused, 17 URL-available HDF5
targets processed, and 14 unavailable/skipped targets. New ignored local HDF5
payload targets included `HIP113421`, `HIP26779`, `HIP67275`, `HIP74981`,
`HIP16852`, `HIP99427`, `HIP66704`, `HIP39826`, `HIP23311`, `HIP82860`, and
`HIP17147`. These payloads are ignored under `data/extended_corpus/`; commit the
map and method, never the HDF5 payloads.

### Extended-Corpus Production Processing Result — 2026-07-02

Local ignored evidence processing completed after PR #192:

```bash
caffeinate -i bash scripts/run_turboseti_on_extended_corpus.sh
caffeinate -i bash scripts/run_pipeline_on_bl_data.sh --dat-dir data/extended_corpus
caffeinate -i bash scripts/run_production_scan.sh --dat-dir data/extended_corpus
.venv/bin/techno-search ai-hardening-gate-summary
caffeinate -i .venv/bin/techno-search radio-real-corpus-summary --dat-dir data/extended_corpus --dat-dir data/bl_hits --hit-ndjson data/meerkat_hits/meerkat_normalised_200000.ndjson --max-hit-rows 5000 --candidate-sample-limit 5
```

Measured results:
- turboSETI processed 8 newly downloaded HDF5 files, skipped 9 already-converted
  targets, and failed 0 targets.
- Candidate-report generation completed 17/17 extended-corpus `.dat` files with
  0 failures.
- Production scan `RUN-2026-07-02_130330Z-3ZNT-prod-scan` scanned 11 pending
  targets, failed 0, flagged 0 escalations, and left 0 pending targets.
- Follow-up ledger entry count was 0; non-detection/no-follow-up ledger entry
  count was 39 across the current local result set.
- `ai-hardening-gate-summary`: `status: closed`, `issue_count: 0`,
  `production_promotion_allowed: true`, populated evidence paths
  `data/extended_corpus`, `data/meerkat_hits`, and `data/injection_grid`, total
  evidence file count 285.
- `radio-real-corpus-summary`: 18 `.dat` files counted across `data/bl_hits` and
  `data/extended_corpus`, 17 zero-hit `.dat` files, 1 hit-bearing `.dat` file
  (Voyager control), 5,000 bounded MeerKAT hit rows admitted, 65 unique targets,
  and `phase1_radio_validation_ready: true`.

No result is a detection, discovery, expert review, external validation, or
external-submission authorization. The durable conclusion is narrower: the newly
downloaded extended corpus produced negative evidence, and the current local
radio validation evidence is cleanly processed and queue-drained.

### Phase 2 Transit Photometry — Real BLS + Aperiodic-Dip Detection, 2026-07-02

With Phase 1 radio hardening blocked on real data availability (the
semisupervised anomaly-threshold calibration and cross-target RFI blockers
both require more real corpus than currently exists locally — see above),
this session opened Phase 2 (`docs/PRODUCTION_READINESS.md`), which was
entirely unstarted. New `src/techno_search/photometry/` package:

- `lightcurve_io.py`: loads a real local Kepler/K2/TESS FITS light curve via
  `lightkurve.read()`.
- `bls_detection.py`: real Box Least Squares transit search via
  `lightkurve.LightCurve.to_periodogram(method="bls")` /
  `astropy.timeseries.BoxLeastSquares`. Every field name and return type
  (`period_at_max_power`, `transit_time_at_max_power` as an `astropy.time.Time`,
  `compute_stats()`'s `depth`/`depth_odd`/`depth_even`/`depth_half`/
  `harmonic_delta_log_likelihood`/`per_transit_log_likelihood` dict) was
  confirmed via direct `inspect.getsource()`/`inspect.getdoc()` on the
  installed packages and a real constructed-light-curve smoke test — none of
  it came from memory or documentation guesswork.
- `aperiodic_dip.py`: a from-scratch statistical dip detector (median/MAD
  robust baseline and significance, no invented thresholds) that fits real
  ingress/egress slopes per event. This directly implements the general
  diagnostic Boyajian et al. 2016 applied to KIC 8462852's irregular dimming
  events (symmetric vs. asymmetric ingress/egress), independent of BLS's
  periodicity assumption.
- `prototype.py`: `build_transit_photometry_candidate()` turns real BLS +
  dip-detector output into a `Candidate` on a new `Track.TRANSIT_PHOTOMETRY`
  (`schemas.py`), scored by a new `_transit_photometry_scores()`
  (`scoring.py`) using the same interpretable v0/v1 posterior-softmax
  approach as the existing radio/infrared/anomaly tracks — no synthetic
  training data, no invented detection thresholds.
- `lightcurve_search.py` + `techno-search photometry-lightcurve-search` CLI
  command: wraps real `lightkurve.search_lightcurve()`/`download_all()`.
  **This sandbox cannot reach NASA MAST** (verified live:
  `https://mast.stsci.edu` returns a 403 through the sandbox's outbound
  proxy, same restriction already documented for Track A catalog sources),
  so this command must be run on a machine with real network access — same
  pattern as the BL extended-corpus downloads.
- `pipeline_runner.py`/`data_quality.py`/`cli.py` wired end-to-end:
  `techno-search run-pipeline <file>.fits --track photometry` and
  `prod-file-scan` (auto-detects `.fits`/`.fit` → photometry) both work.

**Verified end-to-end on a real, locally-generated FITS light curve** with an
injected 2.2-day/2%-depth transit (`tests/fixtures/photometry/
sample_lightcurve.fits`, built with `lightkurve.LightCurve.to_fits()` — a
real, code-exercising test fixture per the same "constructed input, not
training data" pattern as the existing Fermi FITS regression test, not
random/synthetic training data): `run_pipeline()` recovered period
2.1978 days (injected 2.2), depth SNR 94.3, correctly scored low on the
blended-eclipsing-binary and sinusoidal-preferred indicators, and routed to
`candidate_review_packet`. 1453 tests pass (up from 1434), ruff/mypy clean,
`validate-all` ok, `git add --dry-run .` staged only the intended files
(added `!tests/fixtures/**/*.fits`/`*.fit` to `.gitignore`, mirroring the
existing `*.dat` exception).

**Not done — needs live MAST access from the user's machine:**
`techno-search photometry-lightcurve-search <target> --mission TESS` to pull
a real downloaded Kepler/TESS light curve (e.g. KIC 8462852 / Boyajian's
Star, or a target from the existing stratified sample) through this new
pipeline for a first real (not self-constructed) result.

**PR #194 merged, then PR #195 merged same session** (2026-07-02): wired the
already-existing `catalog_crossmatch()` (SIMBAD+Gaia, opt-in via
`TECHNO_SEARCH_ENABLE_LIVE_DATA=1`) into `_build_photometry_candidate()`,
closing the hardcoded `known_object_score=0.0` gap the same way radio/
infrared already handle it.

### First Real Downloaded Photometry Result — KIC 8462852, 2026-07-02

The user ran the full real pipeline for the first time against a live MAST
download (not the self-constructed test fixture):

```bash
.venv/bin/python -m pip install -e '.[photometry]'
techno-search photometry-lightcurve-search "KIC 8462852" --mission Kepler --limit 1
techno-search run-pipeline "data/photometry_lightcurves/mastDownload/Kepler/kplr008462852_lc_Q111111111111111111/kplr008462852-2009131105131_llc.fits" --track photometry --output-dir artifacts/pipeline_smoke
```

**Real result:** `photometry-lightcurve-search` found 18 real Kepler quarters
available for KIC 8462852 (Boyajian's Star) and downloaded 1 (Q0,
`kplr008462852-2009131105131_llc.fits`). `run-pipeline` processed it cleanly:
`ok: true`, 473 real cadences, `track: transit_photometry`,
`reader_type: lightkurve_fits`, `pathway: human_review_queue` (a plausible
middle-tier result — not `do_not_submit_false_positive`, not the top-tier
`candidate_review_packet`). Full BLS/dip feature values not yet pasted back
by the user (only the top-level `run-pipeline` summary was pasted); the
detailed features live in `artifacts/pipeline_smoke/
kplr008462852-2009131105131_llc.json` on the user's machine.

**Real environment note surfaced by this run, not a bug:** the user's
machine is on Python 3.14 with `.venv` under `python3.14/site-packages`
(matching prior session notes about this venv's interpreter), and the
`.[photometry]` install upgraded `pandas` 3.0.3→2.3.3 (a `lightkurve`
transitive dependency ceiling) and `fsspec`, consistent with the same
downgrade already observed and accepted in this sandbox earlier the same
day (still satisfies `pandas>=2.2`).

**Real feature interpretation (user pasted the full candidate JSON,
2026-07-02):** BLS recovered a 0.8986-day period, 0.0123% depth signal
(`bls_depth_snr: 21.09`, 12 recovered transits across the Q0 baseline).
Critically, `harmonic_delta_log_likelihood: +10.71` →
`sinusoidal_variable_preferred_score: 1.0` — the real vetting statistic
correctly determined a sinusoidal (pulsating/rotating star) model fits this
signal better than a discrete-transit model, and the packet's own
`negative_evidence` says so explicitly ("A sinusoidal ... model is
preferred over the transit model."). This is the physically expected
outcome for an ultra-shallow, sub-day-period periodic signal in raw Kepler
SAP flux (more consistent with stellar variability or unremoved spacecraft
systematics than a real transiting body) and is exactly the kind of
real-data case this vetting statistic exists to catch.
`aperiodic_dip_count: 0` — the Boyajian's Star-style dip detector correctly
found no significant events in this quarter; Q0 predates the star's
well-documented deep dimming events (which occurred in later quarters, e.g.
~Q8 and ~Q16), so this is expected, not a detector miss. Net posterior:
`natural_source` 0.513 > `technosignature_interest` 0.261,
`false_positive_probability: 0.7394`, `pathway: human_review_queue` — the
conservative middle tier, neither dismissed nor escalated. `known_object_score:
0.0` because `TECHNO_SEARCH_ENABLE_LIVE_DATA` was not set for this run
(live SIMBAD/Gaia cross-match, wired in PR #195, was not exercised).

**Not yet done:** downloading and running additional real quarters
(`--limit` >1 or a specific `--quarter`) to reach the quarters containing
Boyajian's Star's actual known dip events, to give the aperiodic-dip
detector a real positive case to exercise against (still requires the
user's live MAST access).

### All 18 Real Kepler Quarters Processed — KIC 8462852, 2026-07-02

The user downloaded and ran all 18 real Kepler long-cadence quarters
available for KIC 8462852 (`--limit 20`, 17 new + the existing Q0 file) —
`ok: true` on every quarter, 0 pipeline failures. Pathways split
`candidate_review_packet` (7 quarters) vs. `human_review_queue` (11
quarters); none hit `do_not_submit_false_positive`.

A compact cross-quarter summary (`bls_period_days`, `bls_depth_snr`,
`aperiodic_dip_count` per quarter) surfaced two real, independently
significant findings:

1. **12 of 18 quarters independently recovered a period clustered at
   0.88-0.95 days**, every one of them correctly flagged
   `sinusoidal_variable_preferred_score: 1.0` (harmonic model preferred over
   transit). Verified via live web search (not memory) that this is a real,
   previously published feature of KIC 8462852's actual Kepler photometry —
   the well-documented ~0.88-day periodicity, generally attributed to
   starspot rotational modulation (though Makarov & Goldin 2016 argued for
   field-star contamination instead; the *existence* of the real signal in
   the data is not in dispute, only its physical origin). **This pipeline
   independently rediscovered a real, previously known feature of this
   star's actual light curve on its first real corpus run, and correctly
   classified it as non-transit every time.** This is a real, meaningful
   validation of the harmonic-vs-transit vetting statistic on genuine data —
   not a detection claim of anything new.
2. **Three quarters show physically implausible `bls_depth_snr` values in
   the thousands** (3981.1, 7373.3, 2151.6) at longer recovered periods
   (19.79, 20.80, 7.67 days). SNR that high for a shallow dip is not
   consistent with a real transiting companion at Kepler's precision (an
   object that obvious would already be a known giant transiting companion,
   which does not exist for this star) — almost certainly a data artifact
   (e.g. a safe-mode gap, momentum-dump discontinuity, or `flatten()`
   behaving badly across a large data gap). **Root cause not yet
   determined** — flagged as an open real-data investigation, not asserted
   without checking the actual Kepler quality flags/gap structure for those
   three quarters.

A real, unrelated bug was root-caused and fixed live during this session
via direct code inspection (not assumption): the user's first attempt at a
cross-quarter summary script used `glob.glob('kplr008462852-*.json')`,
which also matched each candidate's own `<id>.manifest.json` file (a
different, smaller schema from `reporting.py`'s `report_manifest()` with no
`features` key) — `.manifest.json` also ends in `.json`, so the wildcard
swallowed it. Confirmed by reading `reporting.py` directly. Fixed by
narrowing the glob to `kplr008462852-*_llc.json`, which manifest files
(ending `.manifest.json`, not `_llc.json`) don't match.

**Root cause of the three anomalous high-SNR quarters — found, 2026-07-02:**
the user ran three further real diagnostics directly against the already-
downloaded FITS files and the saved candidate JSON reports (no new
downloads needed), each ruling out a hypothesis in turn:
1. Large data gaps: ruled out — `big_gaps=0` for all three quarters
   (checked via real `TIME` array diffs against 3x median cadence).
2. Elevated Kepler `SAP_QUALITY` flagged-cadence fraction: ruled out —
   compared across all 18 quarters directly; two completely normal-SNR
   quarters (`2010078095331` frac=0.270, `2009259160929` frac=0.261) have
   *higher* flagged fractions than the three anomalous ones (0.188, 0.247,
   0.248), so flagged-fraction does not correlate with the extreme SNR
   values.
3. Degenerate/underestimated `bls_depth_err`: ruled out — `depth_err` is
   comparable (~0.9-1.2e-5) across all 5 long-period quarters checked, both
   anomalous and normal.

**Real distinguishing factor, confirmed:** the three anomalous quarters
have genuinely large BLS-fitted depths (3.7%, 7.15%, 2.43%) vs. tiny depths
(0.084%, 0.142%) for two comparison long-period quarters with normal SNR —
`depth_err` is behaving correctly; the underlying fitted signal really is
that large. **The real methodological catch:** all 5 long-period quarters
independently recovered `bls_transit_count=3` — a structural limit of
running BLS on a single ~90-day Kepler quarter in isolation, since periods
near 20-30 days can only ever show ~3 cycles within one quarter's baseline
regardless of which period is found. With only 3 cycles, a BLS "periodic"
fit cannot distinguish a genuinely periodic signal from 3 real,
non-recurring dips that happen to be spaced coincidentally. This matters
specifically for KIC 8462852 because it is real-world documented to have
large (up to ~20%), non-periodic, one-off dimming events — exactly the
kind of signal a single-quarter BLS search could misidentify as "3
significant periodic transits." All three anomalous quarters also have
nonzero `aperiodic_dip_count` (1, 2, 2) from this pipeline's own separate,
non-periodicity-assuming dip detector, which is the methodologically
correct tool to characterize these events rather than the BLS periodic
fit. Per-dip detail (depth/duration/asymmetry) for these three quarters has
not yet been pulled and reviewed.

### Phase 3 Infrared — Real WISE Photospheric Blackbody Excess Check, 2026-07-02

With both remaining Phase 1 blockers (anomaly-threshold calibration,
cross-target RFI corpus) and the Phase 2 real-corpus run all requiring the
user's machine, this session opened Phase 3 (WISE Dyson-sphere candidates),
also entirely unstarted. New `src/techno_search/infrared_wise/
photosphere_excess.py`:

- Real, verified WISE zero-point flux densities and effective wavelengths
  (Wright et al. 2010 WISE mission paper Table 1: 309.54/171.79/31.676/
  8.3635 Jy at 3.4/4.6/12/22 um for W1-W4) — cross-checked 2026-07-02 via
  live web search against the WISE explanatory supplement and multiple
  independent citing arXiv papers converging on the same four numbers, not
  from memory.
- Fits a single-temperature blackbody (Planck's law via
  `astropy.modeling.physical_models.BlackBody`, real API verified via
  `inspect.signature`/a live forward-model smoke test in this session, not
  memory) to the real W1/W2 color to estimate the star's photospheric
  continuum temperature, then predicts W3/W4 flux from that temperature and
  reports the observed-vs-predicted significance in real per-source
  uncertainty units.
- `infrared/catalog_reader.py` now also parses the real AllWISE
  `w3sigmpro`/`w4sigmpro` profile-fit magnitude-uncertainty columns (verified
  column names via live web search against the AllWISE Explanatory
  Supplement, not guessed) for real per-source uncertainty; falls back to a
  documented 10% relative uncertainty when absent.
- **This is explicitly a single-temperature blackbody approximation, not a
  full Kurucz/BT-Settl stellar-atmosphere grid fit** (which would require
  downloading external model grids, unavailable from this sandbox) — the
  same first-pass simplification used in the IR-excess literature (e.g.
  Wright et al. 2014, already cited in `PRODUCTION_READINESS.md`'s Phase 3
  references) before deeper SED follow-up. Documented as a partial/honest
  gap, not claimed as the eventual full grid-fit target.
- Wired into `pipeline_runner._build_infrared_candidate()`: overrides the
  prior color-heuristic `ir_excess_score`/`sed_fit_residual_score` fallback
  in `infrared/prototype.py` when real W1-W4 photometry is present, and
  attaches `wise_photosphere_temperature_k`/`wise_w3_excess_significance`/
  `wise_w4_excess_significance` features plus a `wise_excess_method`
  provenance tag.

**Verified with a real forward-modeled-blackbody test fixture** (not
training data — a code-correctness fixture, same category as the existing
Fermi FITS regression test): a pure 5778 K blackbody photosphere recovers
its own temperature exactly and reports ~0 excess significance at both W3
and W4; injecting a 5x W4 flux excess recovers exactly 8.0-sigma
significance (matches the hand-computed expected value); real per-source
magnitude uncertainty correctly narrows/widens the reported significance.
1462 tests pass (up from 1456), ruff/mypy clean (added `scipy.*` to the
mypy ignore-missing-imports overrides, matching the existing pattern for
other optional/typed-stub-less dependencies), `validate-all` ok,
`git add --dry-run .` staged only the intended files. Also verified clean
in a from-scratch venv with only `.[dev,science]` installed (scipy is a
core dependency, so all new tests ran rather than skipped: 1438 passed, 30
skipped, 0 failed).

**Not done:** a real downloaded IRSA Gaia+AllWISE cross-match corpus has not
been run through this — same live-network restriction as Track A catalogs
and Phase 2 photometry. Natural-contaminant rejection (dust/debris-disk/AGN)
remains entirely caller-supplied, not computed from real data.

### Mission Realignment — 2026-06-26

The project was redirected in session on 2026-06-26. Key changes:
- **Mission:** Publish-grade multi-modal technosignature search (radio, TESS/Kepler,
  WISE, JWST) — not citizen-science, not operational logging, not synthetic training.
- **Review chain:** (1) Automated multi-modal pipeline → (2) Adversarial AI agent
  tailored per specific candidate → (3) Third-party experts (BL, Penn State SETI,
  Galileo Project, IAU) only if adversarial agent cannot refute.
- **No synthetic training data.** Models trained on synthetic data are worthless for
  real signal detection. MeerKAT BLUSE corpus (Sheikh et al. 2025) is the real training
  corpus for semisupervised_scorer.
- **AGENTS.md and PRODUCTION_READINESS.md** completely rewritten (PR #121, merged).
- **~141 operational overhead modules** identified for deletion in Phase 0.
- **Pre-commit hook updated** to phase-based validation (Phase 0–4) instead of
  outdated Tier 1/2 language.
- **PRODUCTION_SCAN_RUNBOOK.md** updated with storage cleanup section.
- **CLAUDE.md and PROJECT_STATUS.md** updated to reflect multi-modal mission.

### Historical snapshot (2026-06-26 through 2026-06-29; do not execute)

The status and next-step language below is retained only as project history.
It is not authoritative and must not be used to resume downloads, calibration,
label creation, or Phase 0 work. Use the Current Phase Snapshot above,
`docs/PRODUCTION_READINESS.md`, and `docs/SYSTEMATIC_SEARCH_PLAN.md` instead.

- User stays on `main`; agents develop on `claude/general-session-Bb2dZ`.
- **PR #121 merged to `main`** (2026-06-26): DOOM LOOP BROKEN. Fixed
  `discover_dat_files` non-recursive `iterdir()` → `rglob("*.dat")`. Also rewrote
  AGENTS.md and PRODUCTION_READINESS.md for multi-modal science mission. 2471 passed.
- **PR #122 merged to `main`** (2026-06-26): STRATIFIED RANDOM SAMPLING (DECISION-143).
  31 targets across 18 strata from BL HPRC list (Isaacson et al. 2017).
  `data/bl_hprc_seed_targets.csv`, `data/target_sample_manifest.json`, `docs/SAMPLING_DESIGN.md`.
- **PR #123 merged to `main`** (2026-06-26): Pre-commit hook phase-based, runbook storage
  cleanup, PROJECT_STATUS.md, CLAUDE.md updates.
- **PR #124 merged to `main`** (2026-06-27): Phase 0 module deletion — 74 overhead modules
  deleted, 41 overhead test files deleted, stubs in cli.py/__init__.py.
- **PR #125 merged to `main`** (2026-06-27): ABACAB ON/OFF cadence rejection score (Enriquez et al. 2017).
  source_artifact tracking through RadioHit, _abacab_cadence_score(), 3 new tests.
- **PR #126 merged to `main`** (2026-06-27): zero-hit turboSETI `.dat` files become
  negative-evidence manifests and production non-detection ledger entries;
  `docs/fermi_paradox_technosignatures_brief.md` is tracked on GitHub.
- **PR #127 merged to `main`** (2026-06-27): synthetic training/calibration
  fixtures removed and the runbook storage cleanup is tracked.
- **PR #148 merged to `main`** (2026-06-29): BL extended-corpus downloader now
  has verified no-payload `--discover-only` / `--availability-report` mode and
  `TECHNO_EXTENDED_CORPUS_MAX_TARGETS` counts URL-available HDF5 targets rather
  than raw manifest rows. CI passed after fixing the executable test to use an
  explicit interpreter override in GitHub Actions.
- **Current PR in progress:** none after PR #148 merge. Before new work, reset
  `claude/general-session-Bb2dZ` to `origin/main`.
- **Phase 0 status:** Module deletion ✅ (PR #124). ABACAB ✅ (PR #125).
  Zero-hit evidence ✅ (PR #126). Synthetic fixture deletion ✅ (PR #127).
  Verified MeerKAT BLUSE/SETICORE source ingest ✅ (PR #142). Remaining
  production work is Phase 1 radio hardening and broader real-corpus expansion
  beyond the small local GBT/turboSETI sample.
- **semisupervised_scorer:** local training path verified. Use
  `techno-search semisupervised-corpus-build --dat-dir data --output data/meerkat_hits/real_turboseti_training.ndjson`
  and then `techno-search semisupervised-scorer-train --corpus data/meerkat_hits/real_turboseti_training.ndjson --workers 12`.
  This fit an ignored local model on 259 real GBT/turboSETI hits. `run-pipeline`
  now injects fitted local scorer anomaly-score features into radio candidate
  packets when `data/meerkat_hits/semisupervised_scorer.joblib` exists, or when
  `--semisupervised-model` is provided. The public MeerKAT BLUSE hit-table
  source remains unverified/blocked.
- DECISION-134/139: AI hardening gate closed for local operations only.
- DECISION-140: `prod-scan` and `scripts/run_production_scan.sh` are canonical UX.
- DECISION-141: prod-target-queue, continuous loop, SIGINT trap active.
- DECISION-142: non-deterministic `.dat` discovery fixed.
- DECISION-143: stratified random sampling active.
- External submission, discovery/detection, expert review remain unclaimed and blocked.

### Phase 0 progress (2026-06-27):

**PR #124 merged.** Deleted 74 overhead modules.
**PR #125 merged.** ABACAB cadence rejection score implemented.
**PR #126 merged.** Zero-hit `.dat` observations are preserved as negative evidence.
**PR #127 merged.** Synthetic training/calibration fixtures removed.
**PR #128 merged.** Public `validate-all` is now Phase 0 science-only and the
legacy validate-all payload was deleted.
Next Phase 0 items:
1. Expand the real stratified GBT corpus with URL-available HDF5 targets from
   `data/target_sample_manifest.json`; use `--discover-only` first and never
   assume manifest-order targets have live archive URLs.
2. Run turboSETI and `radio-real-corpus-summary --dat-dir data/extended_corpus
   --dat-dir data/bl_hits`; Phase 1 cross-target RFI validation remains blocked
   until at least 2 independent hit-bearing targets exist.
3. Calibrate how `semisupervised_anomaly_score` should affect pathway routing
   after a larger independent real corpus exists. It is currently recorded as
   local triage evidence in candidate packets, not used as an external-claim
   trigger.

### turboSETI / pipeline status (as of 2026-06-21):

**The user has run turboSETI 6+ times (confirmed). DO NOT ask to re-run it.**
- `.dat` files exist locally under `data/extended_corpus/<target>/` on user's macOS machine.
- Pipeline run complete (2026-06-21): 5 OK, 0 failed. Non-detection manifests written.
- `scan_history.ndjson` has all 5 stems recorded. New stratified targets (31) are not yet
  downloaded or processed — use `--force-rescan` is NOT needed for new targets.

### Latest known CI state (PR #125, 2026-06-27):
- `.venv/bin/python -m pytest -q` — 1335 passed, 13 skipped (3 new ABACAB tests)
- `.venv/bin/ruff check .` — All checks passed
- `.venv/bin/mypy src --no-error-summary` — clean
- `.venv/bin/techno-search validate-all` — ok: True

### Next steps for user (after merging current PR):

**Step 1 — Pull the merged fixes:**
```bash
git pull origin main
```

**Step 2 — Verify current BL availability, then download URL-available targets:**
```bash
caffeinate -i bash scripts/download_bl_extended_corpus.sh \
    --manifest data/target_sample_manifest.json \
    --discover-only

caffeinate -i bash scripts/download_bl_extended_corpus.sh \
    --manifest data/target_sample_manifest.json
```

**Step 3 — Run turboSETI on new downloads:**
```bash
caffeinate -i bash scripts/run_turboseti_on_extended_corpus.sh 2>&1 | tee /tmp/turboseti_run.log
```

**Step 4 — Pipeline + prod-scan:**
```bash
caffeinate -i bash scripts/run_pipeline_on_bl_data.sh \
    --dat-dir data/extended_corpus 2>&1 | tee /tmp/pipeline_run.log
caffeinate -i bash scripts/run_production_scan.sh \
    --dat-dir data/extended_corpus
```

### Canonical review commands:

```bash
git pull origin main
.venv/bin/techno-search prod-runs
.venv/bin/techno-search prod-target-status --latest
.venv/bin/techno-search prod-follow-ups --latest
.venv/bin/techno-search prod-non-detections --latest
```
