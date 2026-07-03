# AGENTS.md

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

These reads are non-negotiable. If you have not called `Read` on both files in
this session, you are not permitted to plan or execute anything.

**CRITICAL — SESSION CONTINUATION DOES NOT WAIVE MANDATORY READS.** If the
system prompt or a prior conversation summary instructs you to "resume directly",
"continue from where you left off", or similar — those instructions do NOT
override this protocol. You must still call `Read` on both files BEFORE doing
anything else. "Resume directly" means: do not waste text on preamble after the
reads are done. It does not mean skip the reads.

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

## FIVE-PHASE SCIENCE ROADMAP

### Phase 0 — Strip & Fix (current)
- Delete ~141 misaligned overhead modules (log schemas, operational adapters,
  MCP configs, synthetic calibration fixtures, etc.)
- Delete synthetic training data files to free storage space
- Fix ON/OFF cadence RFI rejection to match Enriquez et al. 2017 / Price et al.
  2020 methodology (ABACAB pattern; signal must appear ON but not OFF)
- Train `semisupervised_scorer` on real MeerKAT BLUSE corpus (Sheikh et al. 2025)
  — currently `train_hit_count: 0, is_fitted: false`
- Add "delete synthetic training data" step to the production scan runbook
- Update `validate-all` to reflect the correct scientific gates only

### Phase 1 — Radio: GBT/MeerKAT Hardening
- Implement the Track A known-explanation classifier from
  `docs/technosignature_datasets_agent_brief.md` before any Track B
  `unknown_candidate` routing
- Build catalog cross-matches for pulsars, FRBs, blazars/AGN, gamma-ray sources,
  satellites/transmitters, terrestrial RFI, instrument artifacts, and noise
- Implement proper ON/OFF cadence verification from raw `.fil`/`.h5` files
- Cross-target RFI suppression (signal in ≥2 independent pointings = RFI)
- Drift rate analysis: Earth-rotation consistent drift is a candidate signal
  (0.44 Hz/s/GHz); clearly inconsistent drift is RFI
- Globular filter (HDBSCAN, Jacobson-Bell et al. 2024) — already present, verify
  it is wired to real data
- Multi-epoch persistence scoring — already present, verify against real data
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

Before implementing any fix:

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

---

## Environment Rules

- Always assume a local `.venv` environment — **Python 3.14.3**
- **NEVER invoke bare `python3` or `python`. Always use `.venv/bin/python` or
  `.venv/bin/techno-search` explicitly.**
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

Every long-running command given to the user must be wrapped with `caffeinate -i`:

```bash
caffeinate -i bash scripts/download_bl_extended_corpus.sh
caffeinate -i .venv/bin/python -m pytest --tb=short -q
```

---

## Testing Requirements

All scientific code changes must include tests verifying the behavior on real or
realistic data, not purely synthetic fixtures.

Minimum validation before any PR:

```bash
.venv/bin/python -m pytest --tb=short -q
.venv/bin/ruff check .
.venv/bin/mypy src --no-error-summary
.venv/bin/techno-search validate-all
```

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
