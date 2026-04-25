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

If files conflict, prioritize:

1. `docs/DECISIONS.md`
2. `docs/SCORING_MODEL.md`
3. `docs/PIPELINE_SPEC.md`
4. `docs/PROJECT_STATUS.md`

---

## Non-Negotiable Scientific Rules

- Never claim a confirmed technosignature.
- Never use sensational language such as “alien signal” unless quoting and clearly rejecting unsupported framing.
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

## Non-Negotiable Engineering Rule

Do not mark a task complete if tests are failing or missing.

If implementation cannot be fully tested yet:

- add a pending test stub where appropriate
- document the blocker in `docs/PROJECT_STATUS.md`
- explain what evidence is required to complete testing

---

## Testing Requirements

All code changes must include appropriate tests.

### Unit Tests

Every new function, class, or module must include unit tests covering:

- expected behavior
- edge cases
- invalid inputs
- numerical stability where applicable
- deterministic output where applicable

Unit tests must be fast, isolated, and free of live network access.

### Integration Tests

Pipeline-facing code must include integration tests showing that components work together.

Examples:

- synthetic radio hit → RFI checks → scoring → pathway classification
- mock infrared catalog row → IR-excess features → scoring
- mock archival cross-match → artifact checks → anomaly classification
- known object match → known-object annotation pathway

Use synthetic data or small fixtures.

### Regression Tests

Every bug fix must include a regression test that fails before the fix and passes after the fix.

### Scientific Sanity Tests

Technosignature modules must include scientific sanity checks.

Examples:

- radio hit present in ON scans but absent in OFF scans should score better than a hit present everywhere
- RFI-band overlap should increase false-positive probability
- high frequency persistence across unrelated targets should increase RFI probability
- clean infrared excess with stellar Gaia solution should score better than blended/confused sources
- galaxy/AGN indicators should reduce waste-heat candidate probability
- vanishing-source candidates with plausible proper-motion explanations should be downgraded
- known object matches should suppress new-candidate routing

---

## Minimum Local Validation

Before reporting work as complete, run:

```bash
pytest
```

When available, also run:

```bash
pytest --cov=techno_search --cov-report=term-missing
ruff check .
mypy src
```

If a command fails, fix the issue or document the failure and reason.

---

## Coverage Expectations

Target coverage:

- scoring and pathway logic: 90%+
- track-specific feature extraction modules: 80%+
- CLI and reporting: smoke tests required
- live external integrations: mocked by default

Coverage is not a substitute for meaningful tests.

---

## External Service Policy

Default tests must not require live access to:

- Breakthrough Listen Open Data
- MAST
- NASA/IPAC IRSA
- Gaia Archive
- VizieR
- SIMBAD
- remote catalogs or image services

Live-data tests must be explicitly marked:

```python
@pytest.mark.integration_live
```

Slow tests must be explicitly marked:

```python
@pytest.mark.slow
```

---

## Data Policy

Do not commit:

- large radio data files
- raw FITS, filterbank, HDF5, or image survey files
- downloaded catalog caches
- private credentials
- API tokens
- generated cache directories
- large intermediate products

Small synthetic fixtures are allowed in `tests/fixtures/`.

---

## Documentation Update Rules

Update documentation when changing:

- pipeline architecture
- scoring logic
- thresholds
- submission pathway logic
- testing requirements
- data assumptions
- external dependencies
- search-track scope

Use:

- `docs/DECISIONS.md` for architecture and rationale
- `docs/PROJECT_STATUS.md` for active state and blockers
- `docs/SCORING_MODEL.md` for scoring changes
- `docs/PIPELINE_SPEC.md` for pipeline changes
- `docs/ROADMAP.md` for milestone changes
- track-specific specs for track-specific changes

---

## Definition of Done

A change is complete only when:

- code is implemented
- unit tests are added or updated
- integration tests are added or updated where relevant
- all standard tests pass
- public interfaces are typed
- scientific assumptions are documented
- provenance behavior is preserved
- relevant docs are updated
- no confirmation claims are made

---

## Preferred Development Style

- Keep functions small and testable.
- Prefer pure functions for scoring and decision logic.
- Separate data acquisition from analysis.
- Separate detection from interpretation.
- Separate scoring from pathway classification.
- Use typed data models for candidate signals and outputs.
- Use configuration files for thresholds rather than hardcoding.
- Make intermediate artifacts inspectable.
- Build multi-modal abstractions without forcing all tracks into one brittle schema.
