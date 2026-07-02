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

**Next step per the brief:** Phase 3 (Small Historical Replay) — re-run the
pipeline end-to-end on a small set of known historical events/candidates and
confirm known explanations are recovered. The brief explicitly forbids
starting Track B (`unknown_candidate` routing) until Track A + historical
replay are both done — do not skip ahead to that.

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
