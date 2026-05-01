# PIPELINE SPECIFICATION

## Project
Technosignature Search

## Purpose

Define a deterministic, reproducible, multi-modal pipeline for technosignature-interest candidate search.

The system must support radio, infrared, and archival/catalog anomaly search tracks while sharing common scoring, provenance, reporting, and pathway logic.

---

# 1. High-Level Flow

```text
Ingest → Normalize → Search → Vet → Score → Classify → Report
```

Each stage must:

- produce outputs to disk where appropriate
- be independently testable
- preserve provenance
- expose uncertainty
- avoid unsupported claims

---

# 2. Track A — Radio SETI Pipeline

## Goal

Search radio datasets for narrowband, drifting, structured, or otherwise unusual signals while rejecting RFI and instrumental artifacts.

## Flow

```text
Radio file or hit table
→ ingest
→ normalize metadata
→ search or parse hits
→ RFI vetting
→ ON/OFF cadence checks
→ score
→ classify
→ report
```

## Inputs

- filterbank files
- HDF5 files
- precomputed hit tables
- synthetic radio candidate fixtures

## Outputs

- candidate hit table
- RFI metrics
- waterfall plot path where available
- posterior-style scores
- review packet

---

# 3. Track B — Infrared Waste-Heat Pipeline

## Goal

Search catalog data for unusual infrared excess or SED behavior that may deserve follow-up.

## Flow

```text
Source catalog row
→ cross-match
→ photometric validation
→ SED features
→ IR excess detection
→ natural-explanation vetting
→ score
→ classify
→ report
```

## Inputs

- Gaia-like stellar metadata
- 2MASS-like near-infrared photometry
- WISE/CatWISE-like mid-infrared photometry
- synthetic infrared fixtures

## Outputs

- IR excess metrics
- confusion/blending flags
- natural explanation flags
- posterior-style scores
- review packet

---

# 4. Track C — Archival / Catalog Anomaly Pipeline

## Goal

Search historical and modern catalogs for unusual missing, appearing, or inconsistent sources.

## Flow

```text
Historical source
→ modern cross-match
→ proper-motion checks
→ survey-depth checks
→ artifact checks
→ score
→ classify
→ report
```

## Inputs

- historical catalog entries
- modern catalog entries
- cross-match tables
- synthetic anomaly fixtures

## Outputs

- cross-match confidence
- disappearance/appearance features
- artifact probability
- posterior-style scores
- review packet

---

# 5. Shared Pipeline Stages

## Ingest

Responsibilities:

- load input data
- validate schema
- record source metadata
- assign candidate IDs
- avoid destructive transformations

## Normalize

Responsibilities:

- convert units
- standardize column names
- validate missing values
- attach provenance metadata

## Search

Responsibilities:

- identify candidate events or anomalies
- keep detection logic separate from interpretation
- produce machine-readable candidate features

## Vet

Responsibilities:

- evaluate natural and instrumental explanations
- expose negative evidence
- produce track-specific false-positive features

## Score

Responsibilities:

- compute posterior-style probabilities
- compute false-positive probability
- compute candidate-interest score
- compute submission/readiness score

## Classify

Responsibilities:

- route candidates to conservative pathways
- suppress external submission for weak or known false positives
- label known objects appropriately

## Report

Responsibilities:

- generate Markdown/JSON candidate packets
- include positive evidence
- include negative evidence
- include blocking issues
- include provenance
- avoid confirmation language

---

# 6. Shared Candidate Outputs

Every scored candidate should include:

```json
{
  "schema_version": "string",
  "candidate_id": "string",
  "track": "radio | infrared | anomaly",
  "source_ids": [],
  "features": {},
  "posterior": {},
  "scores": {},
  "recommended_pathway": "string",
  "positive_evidence": [],
  "negative_evidence": [],
  "blocking_issues": [],
  "provenance": {}
}
```

Machine-readable schema:

```text
schemas/candidate_packet.schema.json
```

Per-candidate report manifests should follow:

```text
schemas/report_manifest.schema.json
```

Batch report manifests should follow:

```text
schemas/batch_manifest.schema.json
```

Current schema version policy:

```text
docs/SCHEMA_VERSIONING.md
```

---

# 7. Recommended Package Layout

```text
src/techno_search/
  __init__.py
  cli.py
  schemas.py
  provenance.py
  scoring.py
  pathway.py
  reporting.py

  radio/
    ingest.py
    search.py
    rfi.py
    injection.py
    waterfall.py

  infrared/
    catalogs.py
    sed.py
    excess.py
    confusion.py
    filters.py

  anomalies/
    crossmatch.py
    vanish.py
    photometric.py
    astrometric.py

  vetting/
    known_objects.py
    natural_explanations.py
    artifacts.py
```

---

# 8. Non-Goals for v1

- No claim of confirmed technosignatures.
- No fully automated discovery announcements.
- No dependence on live network services in default tests.
- No large raw-data files committed to Git.
- No ML-first black-box ranking before baseline interpretability exists.
- No forced single schema that ignores track-specific evidence.

---

# 9. Design Principles

- Reproducibility first.
- Conservative classification.
- Track-specific false-positive handling.
- Shared scoring and reporting.
- Human-in-the-loop review.
- Synthetic tests before live data.
- Configurable thresholds.
- Typed public interfaces.
