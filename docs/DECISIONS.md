# DECISIONS

## Purpose

This file records durable architectural, scientific, and engineering decisions for the Technosignature Search project.

This file should be append-only in spirit. If a decision changes, add a new decision that supersedes the earlier one rather than silently rewriting history.

---

## DECISION-001: Build a Multi-Modal Technosignature Search Platform

**Date:** 2026-04-25  
**Status:** Accepted

### Context

Technosignatures can take multiple possible forms, including radio signals, infrared waste heat, and unusual archival or catalog behavior. A single-track project would be easier to build but less aligned with the breadth of the field.

### Options Considered

1. Radio-only SETI search
2. Infrared-only waste-heat search
3. Archival anomaly search
4. Multi-modal platform

### Decision

Build the project as a multi-modal platform from day one.

Initial tracks:

- radio technosignatures
- infrared waste heat / Dyson-style candidates
- archival and catalog anomalies

### Rationale

- Reflects the diversity of technosignature concepts.
- Allows multiple citizen-science contribution modes.
- Avoids overcommitting to one narrow hypothesis.
- Encourages shared scoring, reporting, and provenance infrastructure.

### Consequences

- More design complexity.
- Requires disciplined modular architecture.
- Requires track-specific false-positive models.

---

## DECISION-002: Use `techno_search` as the Python Package Name

**Date:** 2026-04-25  
**Status:** Accepted

### Decision

Use `techno_search` as the package name.

### Rationale

- Short and readable.
- Suitable for imports.
- Broad enough for multi-modal technosignature work.
- Avoids overly long package names.

---

## DECISION-003: Mirror the Exoplanet Project Documentation Architecture

**Date:** 2026-04-25  
**Status:** Accepted

### Context

The exoplanet project established a useful documentation system for agent continuity and scientific planning.

### Decision

Mirror the same documentation pattern:

- `README.md`
- `AGENTS.md`
- `CONTRIBUTING.md`
- `docs/PROJECT_STATUS.md`
- `docs/ROADMAP.md`
- `docs/DECISIONS.md`
- `docs/PIPELINE_SPEC.md`
- `docs/SCORING_MODEL.md`
- track-specific specs
- `docs/DATA_POLICY.md`

### Rationale

- Reuses a proven workflow.
- Helps future agents orient quickly.
- Separates public project face, active work, durable decisions, and detailed specs.
- Reduces repeated planning work.

---

## DECISION-004: Use Conservative Scientific Language

**Date:** 2026-04-25  
**Status:** Accepted

### Decision

The project must not claim confirmed technosignatures.

Use:

- candidate signal
- anomaly
- follow-up target
- technosignature-interest candidate

Avoid unsupported claims:

- confirmed technosignature
- alien signal
- proof of extraterrestrial intelligence
- discovery of extraterrestrial intelligence

### Rationale

Technosignature searches are highly vulnerable to false positives and sensational interpretation. Conservative language protects scientific credibility.

---

## DECISION-005: Treat False Positives as the Default Hypothesis

**Date:** 2026-04-25  
**Status:** Accepted

### Decision

All candidate scoring and reporting should assume false-positive explanations are more likely than true technosignatures until evidence survives structured vetting.

### Rationale

Likely false-positive sources include:

- radio frequency interference
- satellites and aircraft
- instrumental artifacts
- catalog errors
- dust and astrophysical infrared excess
- galaxies and AGN
- stellar variability
- survey-depth differences
- moving objects
- image artifacts

---

## DECISION-006: Build Shared Scoring Before Large Data Ingestion

**Date:** 2026-04-25  
**Status:** Accepted

### Decision

The first implementation milestone should be the multi-modal scoring and pathway core using synthetic inputs.

### Rationale

- Avoids dependency on large external datasets too early.
- Makes testing easier.
- Establishes scientific guardrails first.
- Creates a stable interface for all search tracks.

---

## DECISION-007: Use Test-First or Test-Alongside Development

**Date:** 2026-04-25  
**Status:** Accepted

### Decision

Every meaningful code change must include unit tests, relevant integration tests, and scientific sanity tests.

### Rationale

The project involves scientific inference and anomaly detection. Untested code risks producing misleading candidates.

---

## DECISION-008: Mock External Services in Default Tests

**Date:** 2026-04-25  
**Status:** Accepted

### Decision

Default tests must not require live network access.

Live tests must be marked:

```python
@pytest.mark.integration_live
```

### Rationale

- Avoids flaky tests.
- Supports reproducible development.
- Makes agent work more reliable.

---

## DECISION-009: Use Config Files for Thresholds

**Date:** 2026-04-25  
**Status:** Proposed

### Proposed Decision

Store thresholds in versioned config files:

```text
configs/radio_search_v0.yaml
configs/infrared_search_v0.yaml
configs/anomaly_search_v0.yaml
configs/scoring_v0.yaml
```

### Rationale

- Makes scientific choices auditable.
- Supports reproducibility.
- Avoids hardcoded threshold drift.
