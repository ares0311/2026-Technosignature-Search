# CONTRIBUTING.md

## Purpose

This repository is scientific software for technosignature candidate search.

---

## Local Setup

Recommended Python version:

```bash
python --version
# Python 3.11+
```

Create environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Upgrade tools:

```bash
pip install --upgrade pip setuptools wheel
```

Install dependencies:

```bash
pip install -e ".[dev]"
```

### Environment Rules

- `.venv/` must never be committed
- Do not use system Python
- Work only inside `.venv`
- Track dependencies via config files
- Consult `docs/LOCAL_SYSTEM_PROFILE.md` before choosing default worker counts, batch sizes, memory budgets, cache paths, or hardware acceleration behavior

---

## Testing

Run:

```bash
pytest
```

With coverage:

```bash
pytest --cov=techno_search --cov-report=term-missing
```

---

## Principles

- Small, testable components
- Explicit logic over black-box
- Preserve provenance
- No unsupported scientific claims
