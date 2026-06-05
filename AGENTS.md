# AGENTS.md

## Purpose

Instructions for AI coding agents working on the Technosignature Search repository.

This is scientific software. Prioritize correctness, reproducibility, conservative scientific language, careful false-positive handling, and test coverage over speed.

---

## MANDATORY SESSION-START PROTOCOL

At the start of every session, before planning or executing any steps, you must:

1. Call `Read` on `AGENTS.md` — do not rely on memory or prior context.
2. Call `Read` on `docs/PRODUCTION_READINESS.md` — do not rely on memory or prior context.

These reads are non-negotiable. If you have not called `Read` on both files in this session, you are not permitted to plan or execute anything.

After reading, your plan must:
- Name the highest-priority unresolved Tier 1 gap from `docs/PRODUCTION_READINESS.md`
- Show how each proposed step closes or directly unblocks that gap
- Include outside blockers (real data, expert labeling, peer review) as explicit named steps
- Never propose log modules, schemas, or scaffolding unless they directly unblock a named Tier 1 or Tier 2 gap
- Never repeat work listed under "What Is Complete" in `docs/PRODUCTION_READINESS.md`

If your plan does not reference specific gaps from `docs/PRODUCTION_READINESS.md` by name, it is non-compliant and must be rewritten before execution.

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

---

## Environment Rules

- Always assume a local `.venv` environment
- Never commit `.venv/`
- Do not rely on system Python packages
- Install dependencies via project configuration (`requirements.txt` or `pyproject.toml`)
- All tests must run inside the virtual environment
- Use `docs/LOCAL_SYSTEM_PROFILE.md` for local performance defaults, while keeping worker counts, memory budgets, cache paths, and hardware acceleration configurable

If dependencies are missing:
- install them locally inside `.venv`
- document additions in dependency files

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
3. **Outside blockers belong in the plan.** If the next step requires real data, expert labeling, telescope access, or peer review, say so explicitly and include it as a named step — do not skip it or work around it.
4. **Never manufacture busywork.** Do not add log modules, schemas, fixtures, or scaffolding unless it directly unblocks a Tier 1 or Tier 2 gap. If there are only 5 meaningful steps, plan 5 and ask what to do next.
5. **Never repeat work already done.** Check `docs/PRODUCTION_READINESS.md` "What Is Complete" before proposing any step.
6. **If the roadmap is exhausted, say so.** Ask the user what the next goal is rather than inventing more steps.

### Tier 1 blockers (nothing ships without these):

- Real observation data ingested
- Real labeled dataset approved
- Calibrated scoring thresholds derived from real noise distributions
- Real site-specific RFI database approved
- External peer review of pipeline logic and candidate reports

Progress is only real if it closes one of these gaps or directly enables closing one.
