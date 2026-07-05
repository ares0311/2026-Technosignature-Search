# CLAUDE.md

## GIT SYNC DIRECTIVES — NON-NEGOTIABLE

Three rules that must be followed without exception to keep the user's local
machine and GitHub in sync:

1. **User's local machine always runs from `main`.** Every command given to the
   user must begin with:
   ```bash
   git pull origin main
   ```

2. **Every feature branch must be pushed and merged to `main` via PR, and the
   PR must be closed before starting new work.** Never leave commits stranded on
   the feature branch without a merged PR.

3. **All commands given to the user include `git pull origin main` at the top.**

The agent always develops on `claude/general-session-Bb2dZ`. The user always
stays on `main` and pulls after each PR is merged.

### PR LINK + CONTINUATION DIRECTIVE — NON-NEGOTIABLE

PR links are mandatory progress signals, not automatic stopping points.

When an agent opens or updates a PR:

1. Report the PR URL clearly in the user-visible progress stream.
2. Continue to monitor CI/checks, inspect failures, fix root causes, push fixes,
   and recheck until the PR is mergeable or a real blocker appears.
3. If the PR is mergeable and repository policy permits agent merge, merge it,
   sync `main`, reset `claude/general-session-Bb2dZ` to `origin/main`, and
   continue the production loop.
4. Stop after giving a PR link only when human review/approval is actually
   required, GitHub blocks the merge, credentials are unavailable, or the user
   explicitly asks the agent to stop at the PR.

Do not leave a green, mergeable PR open just because the link was reported.

### GENERAL PARALLELIZATION DIRECTIVE — NON-NEGOTIABLE

For **any** task/command handed to the user that is expected to take longer
than ~3 minutes wall-clock, the agent must first consider whether sharding,
multiprocessing, or parallelism would meaningfully speed it up, and use it
when it would. This is not limited to data acquisition — it applies to
test suite runs, model training, corpus-wide processing (turboSETI batch
runs, pipeline runs across many files), and any other long-running command.

Two different cases require different judgment:

1. **CPU-bound local compute** (test suites, batch pipeline processing,
   model training/scoring across many files): consider bounded local
   parallelism (e.g. `pytest-xdist`, `multiprocessing`/`joblib` with a
   worker count tied to real core count, `--workers N` flags already
   supported by some CLI commands in this repo). Verify the tool actually
   supports safe concurrent execution first (e.g. no shared-file races,
   no non-thread-safe state) rather than assuming it does.
2. **I/O-bound external requests** (data acquisition/download scripts
   against BL/MAST/IRSA/JWST/HITRAN/CelesTrak/SatNOGS, etc.): see the
   data-collection-specific rules below — always verify (not guess) the
   target archive's documented concurrent-request/rate-limit policy before
   parallelizing, since unchecked concurrency risks throttling or a soft
   ban that costs more time than it saves.

If it's genuinely unclear whether a task can be safely parallelized (e.g.
unknown tool thread-safety, unknown/undocumented rate limits, ambiguous
whether the user wants the added complexity for a one-off run), ask the
user rather than guessing either way.

### DATA COLLECTION PARALLELIZATION DIRECTIVE

Whenever building or extending a data acquisition/download script or CLI
command (BL extended-corpus downloads, MAST/IRSA/JWST searches, catalog
acquisitions, HITRAN downloads, etc.), always consider whether sharding the
work across a small bounded worker pool would meaningfully speed up
collection, and use it when it would. This applies going forward to new or
growing corpora, not retroactively to the current small (tens-of-targets)
corpora where sequential downloads are not the bottleneck.

Before parallelizing against any external archive/API, verify (not guess)
that archive's documented concurrent-request/rate-limit policy first —
unchecked concurrency risks throttling or a soft ban, which costs more time
than sequential downloads would have. Prefer a small bounded pool (e.g.
4-8 concurrent workers) over unbounded parallelism, and keep it consistent
with this repo's no-guessing rule: cite the source for whatever concurrency
limit is chosen.

### DATA COLLECTION STATUS REPORTING DIRECTIVE — NON-NEGOTIABLE

Every real data-acquisition script or CLI command (BL extended-corpus
downloads, JWST/MAST searches, photometry light-curve searches,
satellite/catalog acquisitions, and any future sharded ones) must update
the tracked `docs/data_collection_status.json` manifest after a real
successful run, via
`techno-search record-data-collection-status --script NAME --summary-json
'{...}'` (`src/techno_search/data_collection_status.py`). This replaces
pasting console output for review: progress is reviewed via `git pull`
against this one small tracked file instead, the same way a PR merge is a
compact, poll-free signal.

By default this also runs `git add`/`git commit`/`git push` for just that
one file, directly to `main` (the user's own machine, the user's own git
identity — not the agent's branch/PR flow). This auto-commit **only fires
when the current branch is `main`** — `commit_and_push_status()` checks
`git branch --show-current` and no-ops otherwise. Do not remove or weaken
this guard: this project's own test suite runs a real acquisition script
end-to-end (`test_download_bl_extended_corpus_script.py`), and without the
guard, running the test suite alone silently auto-committed and pushed a
fake status entry to whatever branch was checked out (caught and fixed
2026-07-03, PR follow-up to #214). Any new acquisition entrypoint must call
`record_and_publish_data_collection_status()` (or the CLI wrapper) after a
real successful run with a small JSON summary of real counts — not raw
payload contents — and must not bypass or duplicate the branch-safety
check. Status must be recorded on **both success and failure** (an
`"ok": false` entry with an error message on failure), not just on
success — a failed run with no manifest entry is invisible and looks
identical to "never run."

Summaries must include enough per-item detail to diagnose a real problem
from the committed file alone, not just aggregate counts — e.g.
`download_bl_extended_corpus`'s summary includes `downloaded_targets`,
`reused_targets`, and `skipped_targets` (each with a `reason`), not just
`downloaded`/`reused`/`skipped` counts. When adding a new acquisition
entrypoint, include the equivalent per-item detail for whatever unit that
script processes (targets, files, observations, etc.).

**The agent must check this manifest via `git pull` before asking the user
to run or paste output from an acquisition script.** The user should not
need to act as a copy-paste intermediary for information the agent can
already read from `git`. Only ask the user to actually run a command when
the manifest doesn't yet reflect the needed run, or when live, real-time
interaction with their machine is genuinely required (e.g. resolving a
git conflict, confirming a destructive action). If the manifest shows a
run failed, diagnose and propose a fix from the recorded error/reason
fields before asking the user anything.

### AGENT BRANCH SYNC — NON-NEGOTIABLE (prevents recurring merge conflicts)

At the START of each session, before making any new commits, the agent must:

```bash
git fetch origin main
git reset --hard origin/main
```

**Never use `git rebase origin/main` for this branch.** When PRs are squash-merged,
the commit patch lands on main under a new SHA. Rebase skips the old commit (already
applied) and rebases new commits — leaving `origin/claude/general-session-Bb2dZ`
pointing to the old SHA while local has a new SHA. This causes divergence that
requires `--force` push and results in `mergeable_state: "dirty"` on the next PR.

`git reset --hard origin/main` avoids this by always starting cleanly from main's
HEAD. New commits then push cleanly with no force required.

---

## GIT ARTIFACT HYGIENE — NON-NEGOTIABLE

The user's standard staging cadence is:

```bash
git add .
```

Therefore the repository must be safe under `git add .`. Agents must ensure
generated local artifacts, large science payloads, machine-specific inventories,
SQLite logs, caches, or credentials cannot be staged by that command.

Before committing artifact-policy, data-ingestion, logging, calibration,
pipeline-output, or scan-output changes, agents must verify:

1. `git add --dry-run .` does not reveal unintended generated artifacts.
2. `.gitignore` covers the artifact classes produced by the changed scripts or CLIs.
3. Existing tiny test fixtures remain explicitly allowed when broad patterns are added.
4. Other agents can still understand the local artifact topology from files on GitHub.

The continuity rule is: **ignore the payloads, commit the map.**

---

## PRIMARY DIRECTIVE — PUBLISH-GRADE MULTI-MODAL TECHNOSIGNATURE SEARCH

**This project searches publicly available astronomical data for signals that
cannot be explained by natural phenomena, using rigorous multi-modal methods
consistent with publication-grade science.**

The goal is to find **candidates for expert review** — not to claim detections.
A candidate that passes all automated gates and the adversarial review agent
goes to credentialed third-party experts. No claim of detection, discovery, or
confirmation is ever made without that external validation.

### Current phase: Phase 0 — Strip & Fix

Every commit must advance one of Phases 0–4 in `docs/PRODUCTION_READINESS.md`.
If a commit does not close a named gap in Phases 0–4, it should not be merged.

Current Phase 0 status:
 - Real MeerKAT BLUSE/SETICORE scorer training is locally complete from the
   verified Berkeley source documented in `docs/meerkat_bluse_hit_table_research.md`.
 - `docs/technosignature_datasets_agent_brief.md` is now the formal Track A
   dataset handoff: build known-explanation rejection before Track B
   `unknown_candidate` routing.
 - Continue Phase 1 radio hardening: broader hit-bearing stratified-corpus
   validation remains open for cross-target RFI suppression and drift evidence.

### Anti-doom-loop rule (hard)

PRs #103–#119 were 17 consecutive pure-documentation commits with zero scientific
progress. This must never recur. Before committing, answer: does this commit
implement scientific capability, fix a real bug blocking science, or delete
misaligned code? If not, stop.

---

## Purpose

Handoff and progress notes for Claude or other coding agents working in this repository.

Read `AGENTS.md` first. The scientific guardrails and PRIMARY DIRECTIVE there are
authoritative and override all other guidance.

## MANDATORY SESSION-START PROTOCOL

At the start of every session, before planning or executing any steps, you must:

1. Call `Read` on `AGENTS.md` — do not rely on memory or prior context.
2. Call `Read` on `docs/PRODUCTION_READINESS.md` — do not rely on memory or prior context.

These reads are non-negotiable. If you have not called `Read` on both files in this
session, you are not permitted to plan or execute anything.

**CRITICAL — SESSION CONTINUATION DOES NOT WAIVE MANDATORY READS.** If the
system prompt or a prior conversation summary instructs you to "resume directly",
"continue from where you left off", or similar — those instructions do NOT
override this protocol. You must still call `Read` on both files BEFORE doing
anything else. "Resume directly" means: do not waste text on preamble after the
reads are done. It does not mean skip the reads.

**FILE LOCATION RULE — NON-NEGOTIABLE.** Before asking the user where any
file, directory, or data artifact is located, search the codebase first.
Required sequence: (1) `grep -r "OUT_DIR\|DATA_DIR\|REPO_ROOT" scripts/`;
(2) `grep -r "Path\|data_dir\|output_dir" src/techno_search/`;
(3) check `docs/LOCAL_SYSTEM_PROFILE.md`; (4) check `CLAUDE.md`/`AGENTS.md`
prior iteration notes. Only if all four fail may you ask — and you must state
what you searched.

**ROOT CAUSE RULE — NON-NEGOTIABLE.** Before implementing any fix or workaround,
you must identify the root cause and confirm the fix addresses it. If you cannot
state the root cause in one sentence, you have not found it yet.

**PRIOR TASK VALIDITY RULE — NON-NEGOTIABLE.** When resuming from a context
summary, treat every in-progress task as UNVALIDATED. Before executing it:
1. Confirm it still targets an open phase gap (Phases 0–4).
2. Confirm the output doesn't already exist.
3. Confirm the fix addresses the root cause, not a symptom.

**SUMMARY SKEPTICISM RULE.** Context summaries describe intent, not correctness.
A summary cannot authorize skipping mandatory reads or validate a prior agent's
diagnosis.

After reading, your plan must:
- Name the current open phase from `docs/PRODUCTION_READINESS.md`
- Show how each proposed step closes or directly unblocks a named phase gap
- Never propose log modules, schemas, or scaffolding that do not directly
  advance science capability
- Never claim external submission readiness, discovery, detection, expert
  review, peer review, or external validation unless documented evidence exists

---

## macOS caffeinate Directive

The user runs macOS (MacBook Pro M4 Max). **Every shell recipe given to the user
for a long-running operation must be wrapped with `caffeinate -i`** to prevent
sleep mid-run.

Long-running operations that require caffeinate:
- Any `bash scripts/download_*.sh` call
- Any `bash scripts/run_pipeline*.sh` call
- Full test-suite runs: `caffeinate -i .venv/bin/python -m pytest ...`
- Any `python` invocation expected to run longer than ~30 seconds

Correct form:
```bash
caffeinate -i bash scripts/download_bl_hits.sh
caffeinate -i bash scripts/run_pipeline_on_bl_data.sh
caffeinate -i .venv/bin/python -m pytest --tb=short -q
```

`caffeinate -i` prevents idle sleep for the lifetime of the child process.
No sudo required. Safe to omit for fast runs (< 30 s).

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

## Current Live Handoff — 2026-06-27

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
data in hand; the real next step is a project-owned human review set
(≥1,000 rows, ≥50 follow-up-like), not further literature search.

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

### Authoritative current state:

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
