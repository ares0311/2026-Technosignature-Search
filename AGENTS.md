# AGENTS.md

## STOP — PRE-EXISTING LABELED DATA ONLY — PRIME DIRECTIVE

**Never ask the user—or any other person, expert, collaborator, contractor,
crowd, or research agent—to label, annotate, classify, or review data for the
purpose of creating training, calibration, threshold-selection, or scientific
evaluation labels. Never propose, build, or operate a labeling queue or review
campaign. This project uses labeled data only when the labels already exist as
independent, row-level ground truth with documented provenance.**

There are no confirmed positive technosignature labels. Do not search for,
invent, infer, synthesize, or substitute a positive technosignature class.
`follow_up`, `unknown_candidate`, anomaly, unexplained, synthetic injection,
Voyager, and human-made transmitters are not positive technosignature labels.
Unlabeled observations may be searched, ranked, and analyzed, but must remain
unlabeled and must never be converted into ground truth.

If adequate pre-existing labels do not exist, the affected learned calibration
or promotion gate remains honestly blocked and fail-closed. The correct next
step is deterministic scientific analysis, false-positive rejection, or another
named roadmap gap—not asking anyone to create labels. This prohibition applies
even if another document contains an older suggestion to assemble a human
review set; this section overrides that suggestion. The best current internal
false-positive synthesis is
`docs/False_Positive_Technosignature_Case_Studies.md` and its bibliography.

A valid learned-model path is a Track A classifier—including a CNN if it passes
the CNN promotion gate—trained only on pre-existing labels for known objects,
known phenomena, RFI, and artifacts. It must be allowed to abstain or emit
`low_confidence` when no known class is reliable. Such an unresolved output may
enter deterministic follow-up triage, but it is not a positive label,
`unknown_candidate`, detection, or discovery. Track B's independent evidence
gates still apply.

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

### APP VERSION TRACKING — NON-NEGOTIABLE

Every release-relevant change must advance the semantic app version relative to
`origin/main`. This includes application/science code, scripts, configs,
schemas, and authoritative agent/production directives. Keep `pyproject.toml`,
`src/techno_search/__init__.py`, and `docs/PRODUCTION_READINESS.md` on the same
version. `scripts/check_app_version.py` is the enforced source/base comparison;
it runs inside `scripts/run_parallel_validation.py`. Do not replace it with a
fixed minimum-version assertion—the old test only checked `>= 1.1.0` and could
not detect skipped bumps.

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
   data-collection parallelization rule below — always verify (not guess)
   the target archive's documented concurrent-request/rate-limit policy
   before parallelizing, since unchecked concurrency risks throttling or a
   soft ban that costs more time than it saves.

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

### REPO-NATIVE SHARD LAUNCHERS — NON-NEGOTIABLE

When parallel execution would materially shorten a safe task, use the checked-in
repo-native launcher instead of asking the operator to open multiple terminals
or composing ad hoc background commands. This is the standing default for all
future downloads, tests, and other bounded batch workloads where scopes can be
made non-overlapping and concurrency is verified safe:

- Approved six-manifest `stream_process_evict` acquisition uses
  `scripts/run_six_shard_downloads.py`. It launches exactly six disjoint shard
  manifests from one terminal, defaults to six pipeline workers per shard,
  bounds simultaneous post-processing to at most 12 aggregate pipeline workers,
  preflights the worst-case concurrent raw chunks against the hard 100GB cap,
  refuses completed shard manifests unless repetition is explicit, and preserves
  per-shard logs/status entries. Large raw downloads still require the existing
  metadata, size-preflight, manifest, and explicit-approval gates.
- Full local validation uses `scripts/run_parallel_validation.py`. Its default
  is six pytest-xdist workers operating as six non-overlapping `loadfile` test
  shards with aggregated package coverage; after pytest passes, Ruff, mypy, and
  `validate-all` run concurrently.
  Use this launcher whenever the full suite or a large test selection would
  benefit. Small focused tests may still run directly when launcher startup
  would cost more than it saves.

Do not interpret "six workers and six shards" as 36 simultaneous test workers.
For tests, each xdist worker is one active non-overlapping shard. For downloads,
the launcher may keep six network shards active while its processing-slot gate
prevents CPU oversubscription. Verify manifest/test scopes are non-overlapping
and estimate aggregate storage before starting either launcher.

### DATA COLLECTION STATUS REPORTING DIRECTIVE — NON-NEGOTIABLE

Every real data-acquisition script or CLI command (BL extended-corpus
downloads, JWST/MAST searches, photometry light-curve searches,
satellite/catalog acquisitions, and any future sharded ones) must update
the tracked `docs/data_collection_status.json` manifest after a real
successful run, via
`techno-search record-data-collection-status --script NAME --summary-json
'{...}'` (`src/techno_search/data_collection_status.py`). This replaces
pasting console output for review: progress is reviewed via `git pull`
against this one small tracked file instead, the same way a PR merge is
a compact, poll-free signal.

By default this also runs `git add`/`git commit`/`git push` for just that
one file, directly to `main` (the user's own machine, the user's own git
identity — not the agent's branch/PR flow). This auto-commit **only fires when the
current branch is `main`** — `commit_and_push_status()` checks `git branch
--show-current` and no-ops otherwise. Do not remove or weaken this guard:
this project's own test suite runs a real acquisition script end-to-end
(`test_download_bl_extended_corpus_script.py`), and without the guard,
running the test suite alone silently auto-committed and pushed a fake
status entry to whatever branch was checked out (caught and fixed
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

### ASTROMETRICS CROSS-REPO POLICY DOCS — NON-NEGOTIABLE

The following repo-local policy files are now active directives for work that
touches models, datasets, scoring, evaluation, target selection, acquisition,
storage, candidate ledgers, candidate reports, or detection-pipeline behavior:

- `docs/astrometrics_coding_agents_master_guide.md`
- `docs/astrometrics_data_selection_policy.md`
- `docs/astrometrics_external_and_cloud_storage_policy.md`

Before modifying those areas, read the relevant policy file(s) in this session
and apply them. In particular:

1. Do not promote a model without manifest provenance, grouped/leakage-safe
   evaluation, calibration context, and injection-recovery evidence where the
   policy requires it.
2. Keep training, validation, calibration, frozen-eval, live-search, and
   follow-up live-search data roles separate; never train on live-search data
   and later claim a blind search on that same data.
3. Use metadata-first target queues and batch manifests before raw downloads;
   raw public archive files are cache unless promoted by policy.
4. Treat the 4TB external SSD as the normal local workspace when mounted, but
   keep the 500GB reserve and do not mirror broad public archives.
5. Prefer archive URIs, product IDs, checksums, manifests, ledgers, derived
   features, and candidate evidence packages over permanent raw-data hoarding.
6. Do not use Dropbox-style sync as the authoritative scientific data layer for
   raw archives, batch caches, model artifacts, or candidate evidence ledgers.

If these cross-repo policies conflict with a more specific, current
Technosignatures directive in this file or `docs/SYSTEMATIC_SEARCH_PLAN.md`,
follow the more specific Technosignatures directive and document the reason in
the PR.

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
2. `.gitignore` covers the artifact classes produced by the changed scripts or
   CLIs.
3. Existing tiny test fixtures remain explicitly allowed when broad patterns are
   added.
4. Other agents can still understand the local artifact topology from files on
   GitHub.

The continuity rule is: **ignore the payloads, commit the map.** Raw or
generated data belongs in ignored paths such as `data/` (large files),
`data_cache/`, `tmp_training/`, `tmp_features/`, `results/` outside the
review-safe subtree, `logs/`, `cache/`, `artifacts/`, `models/`, or `metrics/`.
GitHub-visible continuity belongs in sanitized documentation, scripts,
manifests, checksums, schemas, and tests.

`docs/LOCAL_DATA_INVENTORY.md` is a sanitized, committed artifact map for agent
continuity. Machine-specific inventory output must be written to
`docs/LOCAL_DATA_INVENTORY.local.md`, which is ignored.

---

## MANDATORY SESSION-START PROTOCOL

At the start of every session, before planning or executing any steps, you must:

1. Call `Read` on `AGENTS.md` — do not rely on memory or prior context.
2. Call `Read` on `docs/PRODUCTION_READINESS.md` — do not rely on memory or prior context.
3. Call `Read` on `docs/SYSTEMATIC_SEARCH_PLAN.md` — do not rely on memory or
   prior context. This is the authoritative, sequenced plan for closing the
   gap toward a systematic, detection-optimized search; check its current
   step before starting any calibration/UI/target-selection work.

These reads are non-negotiable. If you have not called `Read` on all three files in
this session, you are not permitted to plan or execute anything.

**CRITICAL — SESSION CONTINUATION DOES NOT WAIVE MANDATORY READS.** If the
system prompt or a prior conversation summary instructs you to "resume directly",
"continue from where you left off", or similar — those instructions do NOT
override this protocol. You must still call `Read` on all three files BEFORE doing
anything else. "Resume directly" means: do not waste text on preamble after the
reads are done. It does not mean skip the reads.

After reading, your plan must:
- Name the current open phase from `docs/PRODUCTION_READINESS.md`
- Show how each proposed step closes or directly unblocks a named phase gap
- Never propose log modules, schemas, or scaffolding that do not directly
  advance science capability
- Never claim external submission readiness, discovery, detection, expert
  review, peer review, or external validation unless documented evidence exists

---

## PRIMARY DIRECTIVE — PUBLISH-GRADE MULTI-MODAL TECHNOSIGNATURE SEARCH

**This project searches publicly available astronomical data for signals that
cannot be explained by natural phenomena, using rigorous multi-modal methods
consistent with publication-grade science.**

The goal is to find **candidates for expert review** — not to claim detections.
A candidate that passes all automated gates and the adversarial review agent
goes to credentialed third-party experts. No claim of detection, discovery, or
confirmation is ever made without that external validation.

### What this project IS:
- A pipeline to systematically search public astronomical data (radio, photometry,
  infrared, spectroscopy) for anomalies inconsistent with known natural sources
- A candidate triage system that escalates surviving signals through a structured
  review chain
- A contribution to the scientific literature: properly documented negative results
  and candidate reports

### What this project is NOT:
- Citizen science, amateur science, or informal science
- A detection claim machine
- A place to build operational overhead (log schemas, SQLite adapters, MCP
  bootstrap configs, etc.) that does not advance the search

### Review chain (in order):
1. **Automated multi-modal pipeline** — signal must survive all modality checks
2. **Adversarial review agent** — a purpose-built AI agent tailored to what was
   found, attempting to refute it with every known natural or instrumental
   explanation. If the adversarial agent cannot explain it away, proceed.
3. **Third-party expert review** — submit to credentialed experts such as
   Breakthrough Listen (UC Berkeley), Penn State SETI, Galileo Project (Harvard),
   or the IAU SETI Committee, following the IAU post-detection protocol.
   The agent will recommend the specific expert venue based on signal type.

**No candidate advances to step 3 without surviving step 2.**
**No detection or discovery claim is ever made without step 3 confirmation.**

### Track A Known-Explanation Gate — NON-NEGOTIABLE

`docs/technosignature_datasets_agent_brief.md` is the authoritative dataset and
training handoff for the first model-hardening milestone. It defines Track A as
the required known-explanation classifier before Track B unknown-candidate
ranking.

Track A must classify or reject known explanations first: pulsars, FRBs,
blazars/AGN, known gamma-ray sources, satellites/transmitters, terrestrial RFI,
instrument artifacts, and noise. Track A may emit `low_confidence` when no known
class is reliable. It must not emit `unknown_candidate`.

Track B may emit `unknown_candidate` only after a tested, reproducible Track A
baseline exists and the specific event has failed known-source, satellite,
RFI, cadence, and instrument-artifact checks. `unknown_candidate` is a local
triage queue state, not a detection or discovery claim.

Never train a binary "technosignature versus non-technosignature" classifier.
There are no confirmed positive technosignature labels. Do not use pretrained
models, Kaggle SETI, Setigen, or any synthetic training set for the first Track A
milestone unless the user explicitly approves a later synthetic benchmark.

### CNN / Learned-Model Promotion Gate — NON-NEGOTIABLE

`docs/astrometrics_coding_agents_master_guide.md` changes the formal roadmap
for any CNN, waterfall morphology model, embedding model, or other learned
model in this repo. Future agents must treat this as a production gate, not a
nice-to-have benchmark note.

Current local status: this repo has only CNN scaffold/stub records for radio
waterfall morphology, with no trained promotable CNN weights. If a future agent
finds or builds a CNN-like model, it must be frozen as `benchmark_cnn_v1` before
any promotion discussion.

Rules:

1. Keep the CNN as a reproducible benchmark; do not make it the main scientific
   thesis and do not let it make final detection decisions.
2. Freeze architecture, preprocessing, random seeds, split definitions, metrics,
   and model-card documentation before comparing future models against it.
3. Do not casually tune a frozen CNN benchmark after results are recorded.
4. Do not promote any learned model without dataset manifest IDs,
   candidate-ledger provenance, grouped/leakage-safe evaluation, calibration
   context, and injection-recovery evidence in real backgrounds.
5. Required grouped holdouts for Technosignatures are by target, cadence,
   frequency band, and telescope/session. Random-only splits are forbidden as
   promotion evidence.
6. Do not treat unlabeled data as negative data.
7. Do not use accuracy as the primary metric for rare-event discovery. Report
   top-k review yield, AUPRC, FDR, calibration, and injection-recovery context.
8. Do not use synthetic-only performance as evidence of real-world performance.
9. Model output is local triage evidence only; it is never a detection,
   discovery, expert review, external validation, or external-submission
   authorization.

---

## TARGET SELECTION PHILOSOPHY — NON-NEGOTIABLE

**This project optimizes target selection for search/detection probability,
not statistical representativeness.** We are looking for a specific rare
signal, not estimating a population parameter — stratified random sampling
(distance × spectral class × exoplanet-host status) is a population-inference
tool, and importing it as the *primary* target-selection mechanism was a
mismatch identified and corrected 2026-07-05.

**Stratified sampling's real, narrower role**: defending a *null result*
against the charge of cherry-picking (this is what DECISION-143 actually
fixed — the prior 5-target list had no stated rationale at all). It is not,
and must not be treated as, a detection-probability-maximizing strategy.
Do not let stratification quota force inclusion of strata with no physical
reason to expect a technosignature (e.g. distance/spectral-type cells
"included for completeness") at the expense of targets a real
detection-maximizing strategy would prioritize.

**Primary target selection must be priority-ranked, algorithmic, and
detection-probability-driven**, using the project's existing
`target_priority_score`/`target_selection_score` mechanism
(`background_search.py`) as the correct tool for this job, not the
stratified-sampling manifest.

### Roadmap after Track B calibration closes

**`docs/SYSTEMATIC_SEARCH_PLAN.md` is the authoritative, sequenced execution
plan for this roadmap — read it before starting any work on calibration,
UI hardening, or target selection.** It records the current honest status
of each step and which steps can run in parallel vs. must be sequenced.

Once both the AI (semisupervised anomaly scorer) and non-AI (deterministic
Track A/B rule-based gates) components are well-calibrated on real evidence:

1. **Harden the UI** — the operator-facing surface for reviewing candidates
   and non-detections must be solid before scaling the search algorithm
   that feeds it.
2. **Build the search-target algorithm**, with two distinct, algorithmically
   chosen selection modes (not manual/hand-picked, not stratified-random):
   - **Novel-target selection**: algorithmically identify and prioritize
     targets with little or no prior observational coverage — i.e. places
     nobody has looked yet — rather than re-covering already-well-observed
     stars.
   - **Follow-up target selection**: algorithmically identify and prioritize
     the optimal next observation for existing candidates that need further
     checks (e.g. more ON/OFF cadence epochs, a different band, a repeat
     visit), distinct from novel-target selection above.

Both selection modes must be evidence-driven (real prior-coverage data,
real candidate evidence gaps) and must not fabricate or guess a priority
score without a stated, citable basis — same standard as every other real
data/methodology decision in this project.

---

## ANTI-DOOM-LOOP DIRECTIVES — NON-NEGOTIABLE

The project suffered 17 consecutive PRs (#103–#119) that only updated CLAUDE.md
with operational status, with zero scientific progress. This must never recur.

**Hard rules:**

1. **No new log schemas, SQLite adapters, MCP configs, or operational overhead**
   unless they directly enable finding or evaluating a new candidate. If you are
   about to add a new log type, schema, or fixture — stop and ask: does this help
   find a technosignature? If not, do not build it.

2. **No pure bookkeeping commits.** A commit must either (a) implement scientific
   capability, (b) fix a real bug blocking science, or (c) delete misaligned code.
   Recording "validate-all passed again" as a commit is forbidden.

3. **No synthetic training data.** It is pointless. Never train a model on
   synthetic data. Real corpora only: MeerKAT BLUSE (Sheikh et al. 2025),
   real GBT hits, real turboSETI output from public BL data.

4. **Before asking the user a question, look it up.** Best practices, API
   signatures, paper methodologies, catalog schemas — search the codebase and
   literature first. Only ask the user when the question requires their personal
   judgment or authorization.

5. **Delete misaligned code.** The ~141 operational overhead modules (log types,
   operational log adapters, MCP bootstrap, etc.) are dead weight. Delete them as
   Phase 0 work unless a module has a proven scientific use.

6. **Every PR must advance a named phase below.** If a PR does not close a gap
   in Phases 0–4, it should not be merged.

---

## LLM MAINTENANCE DIRECTIVES — NON-NEGOTIABLE (added 2026-07-16)

Standing rules for any agent touching this codebase, prompted by a real
2026-07-16 finding: the `operations-blocker-*` CLI family was silently
stubbed (`_StubDict` returning fabricated zero-value keys) while dispatch
code built on top of those stubs still assumed the old real return shape,
causing 7 of 16 commands to crash outright with zero test coverage catching
it — and the crashing commands were listed as literal steps in the canonical
`docs/templates/ci.yml` CI template.

1. **Fail loudly, never silently.** A stub, fallback, or default must never
   return a value that lets calling code proceed as if real data were
   present. If a dependency is missing, unimplemented, or deleted, raise or
   return an explicit "not implemented"/"not available" error — do not
   return a placeholder zero/empty value that downstream code can silently
   consume as if it were real.
2. **No stubbing that hides absence.** Do not create a stand-in function
   that mimics a deleted or unimplemented module's return shape with fake
   data. If a module is deleted, delete its CLI surface (dispatch, parser,
   docs, schemas, fixtures) too — do not leave a command registered that
   returns fabricated content or, worse, crashes.
3. **Fidelity tests are required, not optional.** Every CLI command must
   have at least one test that actually invokes it through the real
   dispatch path (`main([...])` or equivalent), not just a unit test of its
   underlying function. A function-level or fixture-level test can pass
   while the actual command crashes — this happened here, and it must not
   happen again silently.
4. **Spec/provenance conformance.** When an agent or prior session claims a
   capability exists or a command works, that claim must be verifiable by
   actually running the command, not inferred from adjacent test coverage,
   documentation, or a prior agent's summary. Do not treat "described as
   working" as equivalent to "verified working."
5. **Lint/fail on divergence.** Prefer an automated check (test, lint rule,
   or CI step) that fails when implementation diverges from documented
   behavior over relying on manual review to catch it later.
6. **Keep this document itself scannable.** Favor structure that lets an
   agent re-read and re-derive the current rule set accurately in one pass
   (clear section boundaries, no information duplicated across
   contradicting places) over prose density.

---

## FIVE-PHASE SCIENCE ROADMAP

This section describes each phase's scope and methodology — it is not a
status tracker and must not be read as one. **For current phase status, read
`docs/PRODUCTION_READINESS.md`.** This section was written at the 2026-06-26
mission redirect and does not get updated as phase work completes; treat any
status-sounding language below ("currently X", "already present") as
unreliable and verify against `PRODUCTION_READINESS.md` or the real repo
state instead.

### Phase 0 — Strip & Fix
- Delete misaligned overhead modules (log schemas, operational adapters,
  MCP configs, synthetic calibration fixtures, etc.)
- Delete synthetic training data files to free storage space
- Fix ON/OFF cadence RFI rejection to match Enriquez et al. 2017 / Price et al.
  2020 methodology (ABACAB pattern; signal must appear ON but not OFF)
- Train `semisupervised_scorer` on a real MeerKAT BLUSE corpus (Sheikh et al. 2025)
- Add "delete synthetic training data" step to the production scan runbook
- Update `validate-all` to reflect the correct scientific gates only

### Phase 1 — Radio: GBT/MeerKAT Hardening
- Implement the Track A known-explanation classifier from
  `docs/technosignature_datasets_agent_brief.md` before any Track B
  `unknown_candidate` routing
- Freeze any discovered or future CNN/waterfall model as `benchmark_cnn_v1`
  before promotion discussion; promotion remains blocked until the CNN /
  learned-model gate above is satisfied with real-background evidence
- Build catalog cross-matches for pulsars, FRBs, blazars/AGN, gamma-ray sources,
  satellites/transmitters, terrestrial RFI, instrument artifacts, and noise
- Implement proper ON/OFF cadence verification from raw `.fil`/`.h5` files
- Cross-target RFI suppression (signal in ≥2 independent pointings = RFI)
- Drift rate analysis: Earth-rotation consistent drift is a candidate signal
  (0.44 Hz/s/GHz); clearly inconsistent drift is RFI
- Globular filter (HDBSCAN, Jacobson-Bell et al. 2024)
- Multi-epoch persistence scoring
- Output: ranked candidate list with provenance, ready for Phase 5 cross-modal

### Phase 2 — Transit Photometry: Kepler/TESS
- Ingest Kepler/TESS light curves via `lightkurve` from NASA MAST
- Box Least Squares (BLS) for transit detection
- Megastructure / artificial transit signatures:
  - Non-circular transit shape (flat-bottomed vs. rounded)
  - Non-achromatic transits (wavelength-dependent depth = artificial structure)
  - Asymmetric ingress/egress
  - Reference: Boyajian's Star (KIC 8462852) methodology
- Tabby's Star and similar long-cadence anomalies
- Output: candidate transit anomaly list with phase-folded light curves

### Phase 3 — Infrared: WISE Dyson Sphere Candidates
- Ingest WISE W1/W2/W3/W4 photometry for target stars
- SED fitting: compare observed to stellar model (Kurucz/BT-Settl)
- Excess emission at W3/W4 (12μm / 22μm) beyond stellar photosphere
- Methodology: Griffith et al. 2015, Wright et al. 2014
- Flag excess that is inconsistent with dust shells, debris disks, or AGN
- Cross-reference with SIMBAD/Gaia for known contaminants
- Output: IR excess candidates with SED residual plots

### Phase 4 — Spectroscopy: JWST Disequilibrium Gases
- Query MAST for JWST NIRSpec/NIRISS transmission spectra of known exoplanet hosts
- Search for disequilibrium gases that imply industrial chemistry:
  - NO₂ (nitrogen dioxide, combustion byproduct)
  - CFCs / HFCs (chlorofluorocarbons, no natural source)
  - N₂O (nitrous oxide, enhanced by agriculture)
  - SF₆ (sulfur hexafluoride, electrical insulation)
  - Reference: Lin et al. 2014; Schwieterman et al. 2018
- Compare to photochemical equilibrium models
- Output: spectral anomaly candidates with detection significance
- Real band-center provenance, HITRAN dataset IDs, C3F8 derivation, N2O
  secondary-band findings, and verified MAST `instrument_name` query values
  for this phase are recorded in
  `docs/technosignature_detection_research_answers.md` — read it before
  changing `spectroscopy/technosignature_gases.py` or building MAST query
  code for this phase.

### Phase 5 — Multi-Modal Cross-Correlation
- Cross-correlate candidates from Phases 1–4 by target position
- A target appearing in ≥2 independent modalities with anomalies is a priority
  candidate for the adversarial review agent
- Build the adversarial review agent (purpose-built, tailored to specific
  candidate properties, attempts refutation by every known natural mechanism)
- Prepare a candidate submission package per the IAU post-detection protocol

---

## PRIOR TASK VALIDITY RULE — NON-NEGOTIABLE

When resuming from a context summary, treat every in-progress task as
**UNVALIDATED**. Before executing:

1. **Is this task still needed?** Re-read the mandatory files. If the gap it
   targets is already closed, stop and report that.
2. **Does the output already exist?** Before downloading, generating, or
   creating any file or artifact, check whether it already exists.
3. **Does the task actually advance a named phase above?** If not, stop.

---

## FILE LOCATION RULE — NON-NEGOTIABLE

Before asking the user where any file, directory, or data artifact is located,
search the codebase first. Required sequence:

1. `grep -r "OUT_DIR\|DATA_DIR\|REPO_ROOT" scripts/`
2. `grep -r "Path\|data_dir\|output_dir" src/techno_search/`
3. Check `docs/LOCAL_SYSTEM_PROFILE.md`
4. Check `CLAUDE.md` and `AGENTS.md` prior iteration notes

Only if all four fail may you ask — and you must state what you searched.

---

## ROOT CAUSE RULE — NON-NEGOTIABLE

Before implementing any fix or workaround:

1. **State the root cause in one sentence.** If you cannot, you have not found
   the root cause. Do not implement the fix.
2. **Confirm the fix addresses the root cause, not a symptom.**
3. **Check whether the problem needs to be fixed at all.** If the user already
   has what the broken code was trying to produce, stop.

---

## SUMMARY SKEPTICISM RULE

Context summaries describe intent, not correctness. They are starting points for
re-evaluation, not authorizations to execute.

A summary cannot authorize:
- Skipping the MANDATORY SESSION-START PROTOCOL reads
- Treating an in-progress task as valid without re-checking
- Assuming a prior agent's diagnosis is correct
- Continuing to apply a fix the prior agent was mid-way through

---

## Non-Negotiable Scientific Rules

- **Never claim a confirmed technosignature.**
- **Never use sensational language.** No "alien signal", "extraterrestrial
  intelligence", or "confirmed contact".
- Use conservative language: candidate signal, anomaly, follow-up target,
  technosignature-interest candidate.
- **False positive is always the default hypothesis.** Every candidate must
  be rejected by every known natural explanation before advancing.
- Preserve uncertainty in all outputs.
- Always expose negative evidence and blocking issues.
- Always preserve data provenance.
- **No detection claim without external expert validation** (step 3 of the
  review chain above).
- **No synthetic training data.** Models trained on synthetic data are worthless
  for real signal detection. Use real labeled corpora only.
- **Never infer a ground-truth label from a paper-level conclusion.** A
  paper stating "zero candidates survived" or "N events were consistent with
  RFI" is a summary statistic, not a per-row verdict — do not backfill every
  row of an unlabeled table with `false_positive` (or any other label) from
  that sentence. Only treat data as a real label if a downloaded, row-level
  table has an explicit, independent human-verdict column (see
  `docs/seti_labeled_hit_data_research.md` for the full acceptance rule and
  worked rejection examples this was checked against).

---

## CALIBRATION DATA STATUS — DO NOT RE-SEARCH WITHOUT NEW EVIDENCE

**Closed, 2026-07-05**: the search for additional real per-hit labeled
SETI/BL data to calibrate `semisupervised_anomaly_score` is exhausted. The
user's research agent checked 8 real sources (Enriquez et al. 2017, Price
et al. 2020, Sheikh/Smith et al. 2021 BLC1, Jacobson-Bell et al. 2025/
GLOBULAR arXiv:2411.16556, Lacki et al. 2021 Exotica Catalog, Ma et al.
2023, Choza et al. 2024) against a strict acceptance rule (real
downloadable table, one row per hit/candidate, independent human verdict
column, mappable label categories) — none qualified. Full findings:
`docs/seti_labeled_hit_data_research.md`; project-record summary:
`docs/PRODUCTION_READINESS.md` Phase 1.

**The 124-row HIP99427 citizen-science set (2 `follow_up` rows) remains the
only real per-hit labeled ground truth this project has.** Do not re-run
this literature search on the same question without a genuinely new lead
(e.g. a newly published paper) — re-checking the same 8 already-rejected
sources wastes the user's research-agent budget for no new information.

### LABELED-DATA-ONLY RULE — PRIME DIRECTIVE

Training, calibration, threshold selection, and scientific performance
evaluation may use only **pre-existing, independently supplied, row-level
labeled data with documented provenance**.

- Never ask the user, an external expert, a collaborator, a contractor, a
  citizen-science participant, or any other person or institution to label
  data for this project.
- Never build or operate a queue whose purpose is to obtain new labels.
- Never infer labels from automated filters, anomaly scores, clusters,
  paper-level conclusions, target categories, or unlabeled observations.
- Unlabeled observations may be searched, ranked, or used for distributional
  diagnostics, but they may not serve as training targets, calibration truth,
  threshold truth, negatives, positives, or scientific evaluation truth.
- A newly published dataset may be admitted only if it already contains an
  explicit independent row-level label column and passes the provenance and
  acceptance rules in `docs/seti_labeled_hit_data_research.md`.

The 124-row HIP99427 set (2 `follow_up` rows) remains the only verified real
per-hit labeled ground truth available for this radio anomaly calibration
question. It is suitable only for bounded sanity checks, not a global anomaly
threshold. Therefore `semisupervised_anomaly_score` remains an uncalibrated
ranking diagnostic and Track B must fail closed wherever calibrated anomaly
evidence is required. Do not create a workaround, solicit labels, or reopen the
exhausted literature search without a genuinely new already-labeled source.

---

## Environment Rules

- Always assume a local `.venv` environment — **Python 3.14.3**
- **NEVER invoke bare `python3` or `python`. Always use `.venv/bin/python` or
  `.venv/bin/techno-search` explicitly.**
- **A bare `pip install -e .` only installs `techno_search`'s core
  `install_requires`** (numpy/pandas/astropy/scipy/rich/pyyaml/etc.) — not
  even `pytest`/`ruff`/`mypy`, let alone `turbo_seti`/`blimpy`/`h5py`/
  `lightkurve`/`scikit-learn`/`astroquery`. Found 2026-07-11 when a fresh
  sandboxed session's `.venv` (site-packages modified 2026-07-10, ~36
  packages total) turned out to be missing the entire science stack every
  prior session's real work in this file depended on. **The venv this
  project actually needs is every extras group in `pyproject.toml`:**
  ```bash
  .venv/bin/python -m pip install -e ".[dev,radio,science,ml,track_a,photometry]"
  ```
  After installing the `radio` extra, also run
  `bash scripts/patch_turbo_seti_numpy2_compat.sh` (see below) — required
  every time `radio` is (re)installed, since the fix lives in site-packages
  and does not survive a reinstall.
- **`turbo_seti==2.3.2`** (the exact pin in the `radio` extra, and the
  newest release on PyPI as of 2026-07-11 — there is no newer upstream
  version to bump to) **has a real off-by-one bug that crashes every run**
  under numpy>=2.0 (which pip resolves to by default, since turbo_seti
  declares no numpy upper bound, and pinning `numpy<2` project-wide risks
  real resolver conflicts with `astropy==8.0.1`/`pandas==3.0.3`, both very
  recent releases likely requiring numpy 2.x). Root cause:
  `find_doppler.py`'s final per-coarse-channel debug-log line formats
  `max_val.total_n_hits` (a length-1 numpy array by design — three other
  call sites in the same file correctly index it as `total_n_hits[0]`)
  directly with `%i`, omitting the `[0]` index used everywhere else in the
  file. Older numpy silently coerced the length-1 array for `%` string
  formatting; numpy 2.x no longer does, so an otherwise-successful run
  (hits already found and written to the `.dat` file) crashes on this
  trailing log statement. Fix: `scripts/patch_turbo_seti_numpy2_compat.sh`
  applies the same one-line `[0]` index turbo_seti's own authors used
  elsewhere in the file, directly to the installed site-packages copy
  (idempotent, safe to re-run; never touches this repo's own tracked
  code). Run it once after any `radio`-extra install, before running
  turboSETI.
- **This sandbox's PyPI installs require `--trusted-host pypi.org
  --trusted-host files.pythonhosted.org`** (confirmed with the user
  2026-07-11): the sandbox routes all outbound HTTPS through a local
  proxy that TLS-terminates with its own certificate. `curl` trusts it
  via the system CA bundle at `/etc/ssl/cert.pem`, but this session's
  sandbox denies any command that references an absolute path outside the
  repo root — including reading `/etc/ssl/cert.pem` itself, via any tool
  (Bash or Read) — so Python/pip can never be pointed at that already-
  trusted system bundle from inside this sandbox. `--trusted-host` for
  just these two already network-allow-listed hosts is the only working
  mechanism found; the user confirmed this is acceptable (it does not
  expose new attack surface beyond what the network allowlist already
  permits). This is not a credential to store anywhere — it is a per-pip-
  invocation flag.
- **Install packages with `.venv/bin/python -m pip install ...`, never
  `.venv/bin/pip install ...`.** If the venv's Python was ever upgraded in
  place, the `.venv/bin/pip` script can keep pointing at the old
  interpreter's site-packages (confirmed on the local machine: `.venv/bin/pip
  --version` reported `python 3.13` while `.venv/bin/python --version`
  reported `3.14.3`), so packages "successfully installed" via `pip` silently
  never become importable from the interpreter `techno-search` actually runs
  under. `python -m pip` ties installation to `sys.executable` and sidesteps
  this class of bug entirely.
- Never commit `.venv/`
- All tests must run inside the virtual environment: `.venv/bin/python -m pytest`
- Use `docs/LOCAL_SYSTEM_PROFILE.md` for local performance defaults

---

## SANDBOX NETWORK RESTRICTION RULE — NON-NEGOTIABLE

This agent's sandbox proxy blocks most scholarly/data hosts: confirmed via
direct `curl` (2026-07-04) that `arxiv.org`, `export.arxiv.org`,
`iopscience.iop.org`, `zenodo.org`, `ui.adsabs.harvard.edu`,
`researchgate.net`, `seti.berkeley.edu`, `vizier.cds.unistra.fr`/
`cdsarc.cds.unistra.fr`, and `mast.stsci.edu` all return 403. Only
`github.com`/`raw.githubusercontent.com` are reachable.

**Before reporting that a real dataset "doesn't exist" or a literature
question is unanswerable, this agent must first check whether the answer
depends on one of these blocked hosts.** If so, that is not a genuine
negative result — hand it to the user's research agent instead, using the
established pattern (`docs/bl_hprc_full_catalog_source_request.md`,
`docs/bl_hit_calibration_labels_source_request.md`): a detailed,
self-contained research-question doc with explicit "do not guess" rules,
given to the user "in a code box" to paste to their research agent. See
`docs/PRODUCTION_READINESS.md`'s "Sandbox network restrictions" section for
the current open item (real per-hit labeled BL/SETI calibration data).

---

## MCP SERVER USAGE

When these MCP servers are configured/available in the current session, prefer
them over guessing, memory, or ad hoc shell calls:

- **GitHub MCP** — issues, PRs, remote branches, repo metadata, PR review
  notes, commit/PR review, and PR links. Prefer this over recalling PR state
  from memory when reporting the PR LINK + CONTINUATION DIRECTIVE above.
- **Context7 MCP** — current library/framework/SDK/API/CLI documentation.
  Use even for well-known libraries; training data may be stale on recent
  API/version changes.
- **arXiv MCP** — preprint lookup, paper search, and research context for
  citations used in `docs/*_research.md` / `docs/*_brief.md` files. Useful
  precisely because the SANDBOX NETWORK RESTRICTION RULE above blocks direct
  `arxiv.org`/`export.arxiv.org` access from this sandbox.
- **NASA ADS MCP** — astronomy/astrophysics literature: bibcodes, citations,
  references, author metrics, BibTeX export. Useful for the same reason —
  direct `ui.adsabs.harvard.edu` access is blocked from this sandbox.

Using these servers does not change any scientific rule in this file: fetched
literature/documentation is research input only, still subject to the
Non-Negotiable Scientific Rules (no discovery claims, provenance preserved,
false positive remains the default hypothesis). See
`docs/Technosignatures_MCP_BOOTSTRAP.md` for the original conservative MCP
rollout policy (project-file/git-read/`techno_guard` scope) that these
additional servers extend.

**Do not offload routine command execution to the user.** If the agent has a
working tool for a task (GitHub MCP, `gh`/`curl` via Bash, WebFetch, etc.),
use it directly instead of asking the user to run a command and paste back
the result — this generalizes the DATA COLLECTION STATUS REPORTING
DIRECTIVE's "the user should not need to act as a copy-paste intermediary"
rule beyond acquisition scripts to GitHub API lookups, diagnostic
`curl`/`jq` checks, and other routine reads. Only ask the user to run
something themselves when there is a genuine, confirmed tool/sandbox
blocker (e.g. this session's sandbox hard-denies file access outside the
repository's git root, so files like `~/.claude.json` truly require the
user's own shell) — and say so explicitly rather than defaulting to it out
of convenience. (User correction, 2026-07-11.)

---

## Local Performance Optimization

Read `docs/LOCAL_SYSTEM_PROFILE.md` for local performance defaults and
`docs/SYSTEM_PROFILE.md` when it exists locally for the detailed current
machine profile.

Default local target:
- MacBook Pro M4 Max, 16 CPU cores (12P + 4E), 40-core Apple GPU, 64 GB unified memory

Rules:
1. **AI training** must prefer GPU acceleration when a tested backend is
   available: **Apple Metal/MPS**, MLX, or another project-approved accelerator.
   If unavailable, document the fallback and keep runs reproducible on CPU.
2. CPU-bound batch work should use bounded multiprocessing: **up to 12 workers**
   by default, leaving headroom for macOS and interactive tools.
3. I/O-bound live-provider or catalog work should use conservative concurrency:
   usually **4 to 6 workers**.
4. **Avoid oversubscription.** When using process pools with NumPy/SciPy/sklearn,
   set native thread counts to 1 per process unless profiling shows otherwise.
5. Keep routine peak memory below 48 GB unless the user explicitly approves more.
6. Performance-sensitive code must expose worker counts, batch sizes, and
   accelerator choices through config or CLI options.
7. **Do not hard-code this workstation into** scientific thresholds, candidate
   scores, or any logic that affects scientific outputs.

### macOS Sleep Prevention — caffeinate

Every long-running command given to the user must be wrapped with `caffeinate -i`
to prevent sleep mid-run. Required for: any `bash scripts/download_*.sh` call,
any `bash scripts/run_pipeline*.sh` call, full test-suite runs, and any `python`
invocation expected to run longer than ~30 seconds.

```bash
caffeinate -i bash scripts/download_bl_extended_corpus.sh
caffeinate -i bash scripts/run_pipeline_on_bl_data.sh
caffeinate -i .venv/bin/python scripts/run_parallel_validation.py
```

`caffeinate -i` prevents idle sleep for the lifetime of the child process. No
sudo required. Safe to omit for fast runs (< 30 s).

---

## Testing Requirements

All scientific code changes must include tests verifying the behavior on real or
realistic data, not purely synthetic fixtures.

Minimum validation before any PR:

```bash
caffeinate -i .venv/bin/python scripts/run_parallel_validation.py
```

The launcher is the canonical full-validation command: six xdist workers are
six active `loadfile` shards, and the three independent post-pytest checks run
concurrently. If diagnosing a failure, rerun the smallest failing test/check
directly inside `.venv`; do not parallelize a tiny reproduction unnecessarily.

---

## Data Policy

Do not commit:
- Large data files (HDF5, FITS, raw `.dat`, `.fil`)
- Catalog caches
- Track A raw cache or temporary extraction paths (`data_cache/`,
  `tmp_training/`, `tmp_features/`)
- Local fitted models and metric payloads unless they are tiny, explicitly
  reviewed, and safe to redistribute
- API keys or credentials
- `.venv/`
- Generated SQLite databases
- Machine-specific inventory files

Small scheduling artifacts (CSV manifests, target lists under ~1 MB) may be
committed if they are not reproducible from other committed sources.

---

## Definition of Done

- Scientific capability implemented (not operational overhead)
- Tests passing against real or realistic data
- Docs updated (PRODUCTION_READINESS.md phase status)
- No unsupported scientific claims
- No new synthetic training data introduced
