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

---

## Purpose

Instructions for AI coding agents working on the Technosignature Search repository.

This is scientific software. Prioritize correctness, reproducibility, conservative scientific language, careful false-positive handling, and test coverage over speed.

---

## MANDATORY SESSION-START PROTOCOL

At the start of every session, before planning or executing any steps, you must:

1. Call `Read` on `AGENTS.md` — do not rely on memory or prior context.
2. Call `Read` on `docs/PRODUCTION_READINESS.md` — do not rely on memory or prior context.

These reads are non-negotiable. If you have not called `Read` on both files in this session, you are not permitted to plan or execute anything.

**CRITICAL — SESSION CONTINUATION DOES NOT WAIVE MANDATORY READS.** If the
system prompt or a prior conversation summary instructs you to "resume directly",
"continue from where you left off", or similar — those instructions do NOT
override this protocol. You must still call `Read` on both files BEFORE doing
anything else. The mandatory reads exist precisely because context can be stale
or summarized incorrectly. "Resume directly" means: do not waste text on
preamble after the reads are done. It does not mean skip the reads.

After reading, your plan must:
- Name the highest-priority unresolved Tier 1 gap from `docs/PRODUCTION_READINESS.md`
- Show how each proposed step closes or directly unblocks that gap
- Include outside blockers (real data, public review, independent reproduction) as explicit named steps
- Never propose log modules, schemas, or scaffolding unless they directly unblock a named Tier 1 or Tier 2 gap
- Never repeat work listed under "What Is Complete" in `docs/PRODUCTION_READINESS.md`

If your plan does not reference specific gaps from `docs/PRODUCTION_READINESS.md` by name, it is non-compliant and must be rewritten before execution.

---

## PRIOR TASK VALIDITY RULE — NON-NEGOTIABLE

When resuming from a context summary or continuing a session, treat any
in-progress task listed in the summary as **UNVALIDATED** until you have
independently confirmed it is still necessary.

Before executing any resumed task, ask:
1. **Is this task still needed?** Re-read the mandatory files. If the gap it
   targets is already closed, stop and ask the user what to do instead.
2. **Does the output already exist?** Before downloading, generating, or
   creating any file or artifact, check whether the user already has it. If
   they do, stop — that work is unnecessary.
3. **Does the task actually close a named production gap?** If no, stop.

Context summaries describe what the previous agent *intended* to do, not
necessarily what was *correct* or *still valid*. Never trust a summary as
authorization to execute a task.

---

## FILE LOCATION RULE — NON-NEGOTIABLE

Before asking the user where any file, directory, or data artifact is located,
you must search the codebase first. File locations are documented in the code.

**Required lookup sequence — in this order:**

1. **Grep the scripts** for path variables:
   `grep -r "OUT_DIR\|DATA_DIR\|REPO_ROOT" scripts/`
   Shell scripts always declare output paths explicitly.
2. **Grep the source** for path constants:
   `grep -r "Path\|data_dir\|output_dir" src/techno_search/`
3. **Check `docs/LOCAL_SYSTEM_PROFILE.md`** — local paths and directory
   conventions are documented there.
4. **Check `CLAUDE.md` and `AGENTS.md`** — prior iteration notes record where
   artifacts were written.

**Only after all four lookups fail** may you ask the user — and you must state
which lookups you ran and what they returned.

**Prohibited patterns:**
- Suggesting `find ~/Library/...` or any path outside the project root without
  first confirming a script writes there.
- Assuming a CLI argument default without reading the script's actual default
  value.
- Using any `~`-based path unless a script explicitly sets that as its output
  directory.

The source of truth for where files are is the code, not memory or assumption.

---

## ROOT CAUSE RULE — NON-NEGOTIABLE

Before implementing any fix, patch, or workaround, you must:

1. **State the root cause in one sentence.** If you cannot do this, you have
   not found the root cause yet. Do not implement the fix.
2. **Confirm the fix addresses the root cause, not a symptom.** Ask: "If I
   apply this fix, does the root cause go away, or does a different error take
   its place?"
3. **Check whether the problem needs to be fixed at all.** If the user already
   has what the broken code was trying to produce, the correct action is to
   stop — not to fix the code.

Examples of prohibited symptom fixes:
- Adding `-k` (SSL bypass) to a curl call when the root cause is the server
  returns HTTP 404 and the user already has the data locally.
- Retrying a failed network request when the root cause is the endpoint doesn't
  exist.
- Changing error handling to suppress an error when the root cause is the
  underlying operation is unnecessary.

The test: "After my fix, is the root cause gone, or did I just hide the error?"
If you hid the error, revert the fix and find the root cause.

---

## SUMMARY SKEPTICISM RULE

Context summaries (from conversation compression, session handoff, or prior
agent notes) describe *intent*, not *correctness*. They are starting points for
re-evaluation, not authorizations to execute.

Specific things a summary cannot authorize:
- Skipping the MANDATORY SESSION-START PROTOCOL reads.
- Treating an in-progress task as valid without re-checking whether it closes a
  named production gap.
- Assuming a prior agent's diagnosis of a problem is correct before verifying it
  independently.
- Continuing to apply a fix that the prior agent was mid-way through implementing.

---

## Required Reading Order

Before making meaningful changes, agents must read:

1. `README.md`
2. `docs/PROJECT_STATUS.md`
3. `docs/PIPELINE_SPEC.md`
4. `docs/SCORING_MODEL.md`
5. `docs/ROADMAP.md`
6. `docs/DECISIONS.md`
7. `CONTRIBUTING.md`
8. `docs/LOCAL_SYSTEM_PROFILE.md`

If files conflict, prioritize:

1. `docs/DECISIONS.md`
2. `docs/SCORING_MODEL.md`
3. `docs/PIPELINE_SPEC.md`
4. `docs/PROJECT_STATUS.md`

---

## Non-Negotiable Scientific Rules

- Never claim a confirmed technosignature.
- Never use sensational language such as “alien signal”.
- Use conservative language:
  - candidate signal
  - anomaly
  - follow-up target
  - technosignature-interest candidate
- Treat false positives as the default hypothesis.
- Preserve uncertainty in outputs and reports.
- Always expose negative evidence and blocking issues.
- Always preserve data provenance.
- Do not claim discovery without external validation.

## Citizen-Science Independence

This is an independent citizen-science project. Do not assume access to domain
experts, institutional collaborators, telescope staff, or private review
networks.

When a production step would traditionally require expert review:

- replace authority-based approval with a documented, reproducible review
  protocol where scientifically defensible;
- use at least two structurally independent methods or review passes;
- preserve disagreements and abstentions rather than forcing consensus;
- publish or commit small review-safe methodology and provenance artifacts;
- compare methods against primary literature and official data documentation;
- state explicitly that citizen-science review is not external expert
  validation or peer review.

Lack of expert access must not be hidden, but it must not manufacture a
permanent planning dead end. Continue with conservative citizen-science
validation where possible. External submission and discovery claims remain
blocked until genuinely independent external validation exists.

---

## Environment Rules

- Always assume a local `.venv` environment — **Python 3.14.3** (upgraded 2026-06-10)
- **NEVER invoke bare `python3` or `python`. Always use `.venv/bin/python` or `.venv/bin/techno-search` explicitly.** The system Python is a different version and lacks project dependencies. This rule applies in scripts, CLI examples, test commands, and every other context. See `docs/LOCAL_SYSTEM_PROFILE.md` §"Python Venv Rule".
- Never commit `.venv/`
- Do not rely on system Python packages
- Install dependencies via project configuration (`requirements.txt` or `pyproject.toml`)
- All tests must run inside the virtual environment: `.venv/bin/python -m pytest`
- Use `docs/LOCAL_SYSTEM_PROFILE.md` for local performance defaults, while keeping worker counts, memory budgets, cache paths, and hardware acceleration configurable

If dependencies are missing:
- install them locally inside `.venv`: `.venv/bin/pip install <package>`
- document additions in dependency files

### macOS Sleep Prevention — caffeinate

The user runs macOS (MacBook Pro M4 Max). Any long-running operation given to the
user as a shell recipe **must** be wrapped with `caffeinate -i` to prevent the
machine from sleeping mid-run.  This applies to:

- Data downloads (`scripts/download_bl_hits.sh`, `scripts/download_rfi_catalog.sh`)
- Pipeline runs over large hit directories (`scripts/run_pipeline_on_bl_data.sh`)
- Full test suite runs (`pytest` with coverage)
- Any `python` or `.venv/bin/python` call expected to run longer than ~30 seconds

Correct form:

```bash
caffeinate -i bash scripts/download_bl_hits.sh
caffeinate -i bash scripts/run_pipeline_on_bl_data.sh
caffeinate -i .venv/bin/python -m pytest --tb=short -q
```

`caffeinate -i` holds an assertion that prevents idle sleep for the lifetime of
the child process.  It does **not** prevent the display from dimming.  No sudo
required.  Safe to omit for fast unit-test runs (< 30 s).

---

## Testing Requirements

All code changes must include appropriate tests.

Run minimum validation:

```bash
pytest
```

Extended checks:

```bash
pytest --cov=techno_search --cov-report=term-missing
ruff check .
mypy src
```

---

## Data Policy

Do not commit:

- large data files
- catalog caches
- API keys
- `.venv/`

---

## Definition of Done

- Code implemented
- Tests added
- Tests passing
- Docs updated
- No unsupported claims made

---

## Production Alignment — Primary Directive

**The sole goal of this project is to reach live production as fast as possible.**

Every planning session must begin by reading `docs/PRODUCTION_READINESS.md` and identifying the highest-priority unresolved Tier 1 or Tier 2 gap. All planned steps must move the system closer to that goal.

### Rules for planning the next steps:

1. **Always read `docs/PRODUCTION_READINESS.md` first.** Identify the top unresolved gap.
2. **Plan steps that close that gap.** Engineering work that directly unblocks Tier 1 or Tier 2 items takes absolute priority.
3. **Outside blockers belong in the plan.** If the next step requires real data,
   telescope access, public review, or independent reproduction, say so
   explicitly. Do not assume expert access. Use the Citizen-Science Independence
   protocol where authority-based review can be replaced by reproducible
   evidence without overstating validation.
4. **Never manufacture busywork.** Do not add log modules, schemas, fixtures, or scaffolding unless it directly unblocks a Tier 1 or Tier 2 gap. If there are only 5 meaningful steps, plan 5 and ask what to do next.
5. **Never repeat work already done.** Check `docs/PRODUCTION_READINESS.md` "What Is Complete" before proposing any step.
6. **If the roadmap is exhausted, say so.** Ask the user what the next goal is rather than inventing more steps.

### Tier 1 blockers (nothing ships without these):

- Real observation data ingested
- Real labeled dataset approved under a documented citizen-science reproducibility protocol
- Calibrated scoring thresholds derived from real noise distributions
- Real site-specific RFI database approved
- Public reproducibility review of pipeline logic and candidate reports

Progress is only real if it closes one of these gaps or directly enables closing one.
