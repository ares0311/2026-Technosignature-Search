# AGENTS.md

## Purpose

Instructions for AI coding agents working on the Technosignature Search repository.

This is scientific software. Prioritize correctness, reproducibility, conservative scientific language, careful false-positive handling, and test coverage over speed.

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
