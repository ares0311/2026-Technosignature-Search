# Technosignature Search

![Status](https://img.shields.io/badge/status-planning%20%2F%20foundation-blue)
![License](https://img.shields.io/badge/license-Apache%202.0-green)
![Focus](https://img.shields.io/badge/focus-technosignatures-purple)
![Mode](https://img.shields.io/badge/search-multimodal-orange)

---

## Overview

This project builds a **reproducible, multi-modal citizen-science platform** for searching existing astronomical datasets for possible technosignature candidates.

The system is designed to support three major search tracks from day one:

```text
Radio SETI → Infrared Waste Heat → Archival / Catalog Anomalies
```

The goal is not to claim discovery. The goal is to produce:

> scientifically defensible candidate signals, anomalies, and follow-up targets.

---

## Core Philosophy

Most apparent technosignature-like signals are expected to be false positives.

This project therefore emphasizes:

- conservative scientific language
- explicit false-positive modeling
- reproducible candidate reports
- human-in-the-loop triage
- synthetic signal injection and recovery
- multi-hypothesis scoring rather than single-number hype

---

## Search Tracks

### Track A — Radio Technosignatures

Search existing radio SETI data for narrowband or structured signals.

Initial focus:

- Breakthrough Listen-style filterbank / HDF5 data
- narrowband Doppler-drift searches
- RFI rejection
- ON/OFF cadence filtering
- waterfall plots
- synthetic radio signal injection

---

### Track B — Infrared Waste Heat / Dyson-Style Candidates

Search stellar catalogs for anomalous infrared excess that may deserve follow-up.

Initial focus:

- Gaia
- 2MASS
- WISE / AllWISE / CatWISE
- SED fitting
- mid-infrared excess detection
- dust, galaxy, AGN, and blending rejection

---

### Track C — Archival and Catalog Anomaly Search

Search historical and modern datasets for unusual cross-survey behavior.

Initial focus:

- vanishing or appearing sources
- extreme photometric anomalies
- unusual astrometric behavior
- cross-match failures
- survey artifact rejection
- human-review packets

---

## High-Level Pipeline

```text
Ingest → Normalize → Search → Vet → Score → Classify → Report
```

Every stage should:

- produce reproducible outputs
- preserve provenance
- expose uncertainty
- separate signal detection from interpretation

---

## Current Status

**Phase:** Foundation / Planning

Completed:

- repository initialized
- documentation architecture defined
- multi-modal project scope selected
- package name selected: `techno_search`
- testing and agent standards established
- initial Python package scaffold
- v0 synthetic scoring and pathway core
- Markdown and JSON candidate review packets
- report file writers
- synthetic radio hit-table prototype
- synthetic radio injection helpers
- synthetic infrared catalog prototype
- synthetic archival anomaly prototype
- track-specific v0 configs
- example candidate review packets
- CLI scoring entry point
- calibration false-positive fixtures
- report persistence manifests

Next major milestone:

> Expand from synthetic scoring into the first track-specific prototypes.

See [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md).

---

## Quickstart

Create and install the local development environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Score one synthetic candidate and print the JSON packet:

```bash
.venv/bin/techno-search score examples/candidates/radio_clean_candidate.json
```

Write Markdown, JSON, and manifest review packets:

```bash
.venv/bin/techno-search score \
  examples/candidates/radio_clean_candidate.json \
  --output-dir examples/reports \
  --prefix example-radio-clean
```

Score every candidate in a directory:

```bash
.venv/bin/techno-search score-batch examples/candidates examples/batch_reports
```

Validate a normalized candidate JSON file:

```bash
.venv/bin/techno-search validate-candidate examples/candidates/radio_clean_candidate.json
```

Validate generated report packets and manifests:

```bash
.venv/bin/techno-search validate-reports examples/reports
```

Example outputs:

- Single radio packet: [`example-radio-clean.md`](examples/reports/example-radio-clean.md)
- Single radio manifest: [`example-radio-clean.manifest.json`](examples/reports/example-radio-clean.manifest.json)
- Batch manifest: [`batch_manifest.json`](examples/batch_reports/batch_manifest.json)
- Batch radio packet: [`example-radio-clean.md`](examples/batch_reports/example-radio-clean.md)
- Batch infrared packet: [`example-infrared-clean.md`](examples/batch_reports/example-infrared-clean.md)
- Batch anomaly packet: [`example-anomaly-clean.md`](examples/batch_reports/example-anomaly-clean.md)

Review packets are conservative artifacts. They are not discovery claims, and they always retain false-positive discussion, negative evidence, blocking issues, and the required disclaimer.

Machine-readable schemas:

- Candidate packet schema: [`candidate_packet.schema.json`](schemas/candidate_packet.schema.json)
- Report manifest schema: [`report_manifest.schema.json`](schemas/report_manifest.schema.json)
- Batch manifest schema: [`batch_manifest.schema.json`](schemas/batch_manifest.schema.json)
- Human-review queue schema: [`review_queue.schema.json`](schemas/review_queue.schema.json)

Validation and schema policy:

- Validation guide: [`docs/VALIDATION.md`](docs/VALIDATION.md)
- Schema versioning: [`docs/SCHEMA_VERSIONING.md`](docs/SCHEMA_VERSIONING.md)

---

## Roadmap

| Milestone | Goal |
|---|---|
| 1 | Multi-modal scoring core |
| 2 | Radio SETI synthetic candidate tests |
| 3 | Radio ingestion + hit scoring demo |
| 4 | Infrared catalog anomaly prototype |
| 5 | Archival anomaly prototype |
| 6 | Candidate reporting system |
| 7 | Injection-recovery calibration |
| 8 | Human-review workflow |

See [`docs/ROADMAP.md`](docs/ROADMAP.md).

---

## Core Components

Planned package layout:

```text
src/
  techno_search/
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

## Documentation

```text
docs/
  PROJECT_STATUS.md
  ROADMAP.md
  DECISIONS.md
  PIPELINE_SPEC.md
  SCORING_MODEL.md
  CLI_USAGE.md
  CALIBRATION_FIXTURES.md
  DATA_POLICY.md
  LOCAL_SYSTEM_PROFILE.md
  PUBLISHING.md
  RADIO_SEARCH_SPEC.md
  INFRARED_SEARCH_SPEC.md
  ANOMALY_SEARCH_SPEC.md
  SUBMISSION_PATHWAYS.md
```

---

## What This Project Is

This project is:

- a reproducible technosignature candidate search platform
- a citizen-science-friendly review system
- a multi-modal anomaly detection framework
- a conservative scientific workflow for follow-up prioritization

---

## What This Project Is Not

This project is not:

- a claim engine
- a discovery announcement platform
- a replacement for professional validation
- proof of extraterrestrial intelligence

Use language such as:

- candidate signal
- anomaly
- follow-up target
- technosignature-interest candidate

Avoid unsupported claims such as:

- confirmed technosignature
- alien signal
- discovery of extraterrestrial intelligence

---

## License

Code: Apache 2.0

Documentation: CC-BY-4.0 unless otherwise noted

External datasets are not relicensed by this repository. Users must follow the terms and citation requirements of the original data providers.

---

## Vision

Build a serious citizen-science platform that can search many kinds of existing astronomical data for unusual, reproducible, scientifically interesting technosignature candidates.
