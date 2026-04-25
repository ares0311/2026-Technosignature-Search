# CONTRIBUTING.md

## Purpose

This repository is scientific software for multi-modal technosignature candidate search. Contributions must prioritize correctness, reproducibility, testing, provenance, and conservative scientific interpretation.

---

## Development Principles

- Build small, testable components.
- Prefer explicit, interpretable logic over black-box behavior.
- Preserve provenance for every generated result.
- Avoid hardcoded scientific thresholds where configuration is appropriate.
- Use synthetic fixtures for tests whenever possible.
- Do not commit large raw data.
- Do not label internally detected signals as confirmed technosignatures.
- Separate signal detection from interpretation.

---

## Local Setup

Recommended Python version:

```bash
python --version
# Python 3.11+
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install editable package with development dependencies:

```bash
pip install -e ".[dev]"
```

---

## Quality and Testing Policy

This project follows a test-first or test-alongside development model.

Every meaningful code change must include tests. Untested code is incomplete.

### Required Test Types

| Change Type | Required Tests |
|---|---|
| Pure function | Unit tests |
| Scoring logic | Unit tests + scientific sanity tests |
| Pathway classifier | Unit tests + decision-tree tests |
| Pipeline stage | Unit tests + integration tests |
| Bug fix | Regression test |
| CLI command | Smoke test |
| External API logic | Mocked integration test |
| Report generation | Snapshot or smoke test |

---

## Standard Test Commands

Run default tests:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=techno_search --cov-report=term-missing
```

Run linting:

```bash
ruff check .
```

Run type checks:

```bash
mypy src
```

Recommended full local check:

```bash
pytest --cov=techno_search --cov-report=term-missing
ruff check .
mypy src
```

---

## Testing Principles

Tests should be:

- deterministic
- small and fast
- isolated from live network services
- based on synthetic examples or small fixtures
- specific enough to catch real bugs
- clear about scientific expectations

Any stochastic test must use a fixed random seed.

---

## Scientific Testing Examples

The test suite should verify that:

- ON-target-only radio hits score better than hits appearing in OFF scans
- RFI-band overlap increases RFI probability
- persistent sky-wide radio hits are downgraded
- synthetic injected signals are recoverable under expected conditions
- infrared excess with clean stellar context scores better than blended/confused sources
- AGN, galaxy, dust, or YSO indicators reduce waste-heat interest
- vanishing-source candidates with proper-motion explanations are downgraded
- known-object matches route to `known_object_annotation`
- low-confidence candidates route to `github_only_reproducibility`

---

## External Service Tests

Tests must not require live network access by default.

Live integration tests should be marked:

```python
@pytest.mark.integration_live
```

Slow tests should be marked:

```python
@pytest.mark.slow
```

Standard test runs should exclude live external tests unless explicitly requested.

---

## Code Style

Use:

- `ruff` for linting
- `mypy` for type checking
- Python type hints for public interfaces
- clear docstrings for scientific assumptions
- small, composable functions

Avoid:

- hidden global state
- hardcoded thresholds without config support
- silent failure modes
- untracked randomness
- network calls inside unit tests
- unsupported claims in generated reports

---

## Documentation Requirements

Update documentation when changing:

- scoring logic
- pathway classification
- pipeline architecture
- search-track scope
- thresholds
- data assumptions
- testing policy
- dependencies

Relevant files:

- `docs/SCORING_MODEL.md`
- `docs/PIPELINE_SPEC.md`
- `docs/RADIO_SEARCH_SPEC.md`
- `docs/INFRARED_SEARCH_SPEC.md`
- `docs/ANOMALY_SEARCH_SPEC.md`
- `docs/ROADMAP.md`
- `docs/PROJECT_STATUS.md`
- `docs/DECISIONS.md`
- `AGENTS.md`

---

## Commit Guidance

Use clear, focused commits.

Good examples:

```bash
git commit -m "Add radio candidate scoring tests"
git commit -m "Implement multimodal pathway classifier"
git commit -m "Document data policy for technosignature search"
```

Avoid vague commits:

```bash
git commit -m "updates"
git commit -m "stuff"
```

---

## Review Checklist

Before a change is ready:

- [ ] Code is typed where appropriate
- [ ] Unit tests are included
- [ ] Integration tests are included where relevant
- [ ] Regression tests are included for bug fixes
- [ ] `pytest` passes
- [ ] `ruff check .` passes
- [ ] `mypy src` passes or documented exceptions exist
- [ ] Documentation is updated
- [ ] Scientific claims remain conservative
- [ ] Provenance behavior is preserved

---

## Scientific Language Policy

Use:

- candidate signal
- anomaly
- possible technosignature-interest candidate
- follow-up target
- candidate explanation

Avoid unsupported phrases:

- confirmed technosignature
- alien signal
- extraterrestrial beacon
- proof of intelligence
- discovery of extraterrestrial intelligence
