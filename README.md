# 🛰 2026 Technosignature Search

![Status](https://img.shields.io/badge/status-active%20development-blue)
![License](https://img.shields.io/badge/license-Apache%202.0-green)
![Focus](https://img.shields.io/badge/focus-technosignatures-purple)
![Mode](https://img.shields.io/badge/search-multimodal-orange)

---

## 🌌 Introduction

A **research-grade, reproducible pipeline** for detecting, vetting, scoring, and reporting technosignature-interest candidates from existing astronomical data.

This project is not a discovery engine. It is a conservative scientific workflow for producing reviewable candidate packets across three complementary search modes:

```text
Radio SETI          → narrowband / drifting candidate signals
Infrared catalogs   → waste-heat-interest excess candidates
Archival catalogs   → cross-survey anomaly candidates
```

The central premise is simple:

> Most apparent technosignature-like signals are false positives.

The pipeline is therefore designed to disprove candidates first. Only candidates that survive structured false-positive checks, provenance review, and conservative scoring should advance to human review or follow-up prioritization.

This project prioritizes:

- Scientific rigor
- Low false-positive rates
- Reproducibility
- Explicit uncertainty
- Negative evidence preservation
- Data provenance
- Conservative candidate reporting
- High-value follow-up targets

---

## 🧠 Scientific Motivation

Technosignature searches are unusually vulnerable to overinterpretation. Radio signals can be terrestrial interference. Infrared excess can be dust, galaxies, young stellar objects, AGB stars, or blending. Archival anomalies can be plate defects, moving objects, survey-depth differences, proper motion, or catalog mismatch.

This repository treats those explanations as the default. The goal is to produce scientifically defensible **candidate signals**, **anomalies**, and **follow-up targets**, not claims of confirmed technosignatures.

The workflow follows the same broad pattern used in exoplanet vetting: detect an interesting signal, attack it with known false-positive explanations, quantify uncertainty, and route it conservatively.

---

## 📊 Current Status

**Phase:** Initial v0 Implementation / Synthetic Scoring Core

- ✅ Repository initialized
- ✅ Documentation system built
- ✅ Multi-modal scoring architecture defined
- ✅ Synthetic radio, infrared, and archival anomaly prototypes implemented
- ✅ Candidate Markdown, JSON, manifest, and diagnostic artifact reporting implemented
- ✅ Calibration, reliability, precision-recall, benchmark, and human-review fixtures added
- ✅ Guarded live-provider interfaces added behind explicit opt-in
- ⏳ Live-data workflows remain provenance-only unless explicitly enabled

👉 See [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md)

---

## 🛣 Project Roadmap

| Milestone | Description | Status |
|----------|-------------|--------|
| 1 | Multi-modal scoring core | ✅ Implemented |
| 2 | Radio SETI synthetic candidate tests | ✅ Implemented |
| 3 | Radio ingestion and hit scoring demo | ✅ Prototype |
| 4 | Infrared catalog anomaly prototype | ✅ Prototype |
| 5 | Archival anomaly prototype | ✅ Prototype |
| 6 | Candidate reporting system | ✅ Implemented |
| 7 | Calibration fixtures and summaries | ✅ Implemented |
| 8 | Injection-recovery and reliability diagnostics | ✅ Implemented |
| 9 | Human-review workflow | ✅ Scaffolded |
| 10 | Guarded live-data integrations | ✅ Scaffolded / opt-in |
| 11 | Curated non-synthetic validation datasets | ⏳ Planned |
| 12 | Advanced AI triage after calibration | ⏳ Deferred |

👉 See [`docs/ROADMAP.md`](docs/ROADMAP.md)

---

## ⚙️ Pipeline Architecture

### Global Flow

```text
Existing astronomical data
  → Ingest
  → Normalize
  → Search
  → Vet
  → Score
  → Classify
  → Report
  → Human review / follow-up prioritization
```

### Track-Specific Flow

```text
Track A: Radio SETI
  Filterbank / HDF5 / hit table
    → metadata normalization
    → narrowband or drift search
    → RFI and cadence vetting
    → candidate packet

Track B: Infrared Waste Heat
  Gaia + 2MASS + WISE / CatWISE context
    → cross-match
    → SED and IR-excess features
    → dust / AGN / blending rejection
    → candidate packet

Track C: Archival / Catalog Anomalies
  Historical + modern catalog context
    → cross-match
    → proper-motion and depth checks
    → artifact and moving-object rejection
    → candidate packet
```

### Shared Stage Contract

| Stage | Required Behavior |
|-------|-------------------|
| Ingest | Load inputs, validate schema, assign candidate IDs, preserve raw provenance |
| Normalize | Standardize units, field names, missing values, and source metadata |
| Search | Identify candidate events or anomalies without interpreting them as technosignatures |
| Vet | Surface natural, instrumental, human-made, and catalog false-positive evidence |
| Score | Compute posterior-style probabilities and derived review-readiness scores |
| Classify | Route candidates to conservative pathways |
| Report | Emit Markdown/JSON packets with positive evidence, negative evidence, blocking issues, and provenance |

👉 See [`docs/PIPELINE_SPEC.md`](docs/PIPELINE_SPEC.md)

---

## 📐 Methodology and Scoring Equations

The scoring model evaluates multiple hypotheses for each candidate. It is Bayesian in structure, but the v0 implementation uses interpretable log-score approximations until calibrated empirical likelihoods are available.

### Bayesian Framing

$$
P(H \mid D) \propto P(D \mid H)P(H)
$$

For a hypothesis set \(H_1, H_2, \ldots, H_n\):

$$
P(H_i \mid D) =
\frac{P(D \mid H_i)P(H_i)}
{\sum_j P(D \mid H_j)P(H_j)}
$$

### v0 Interpretable Approximation

$$
\mathrm{log\_score}_i =
\mathrm{log\_prior}_i + \sum_k w_{ik}x_k
$$

$$
P(H_i \mid D) =
\frac{\exp(\mathrm{log\_score}_i)}
{\sum_j \exp(\mathrm{log\_score}_j)}
$$

### False-Positive Probability

$$
P(\mathrm{false\ positive}) =
1 - P(H_{\mathrm{technosignature\ interest}} \mid D)
$$

### Review Readiness

The current implementation tracks review readiness as a conservative derived score:

$$
R =
f(\mathrm{signal\ reality}, \mathrm{provenance}, \mathrm{metadata}, \mathrm{negative\ evidence}, \mathrm{blocking\ issues})
$$

where \(R\) is not a discovery probability. It is a measure of whether the packet has enough context for meaningful review.

### Hypotheses

| Hypothesis | Typical Evidence |
|------------|------------------|
| Technosignature-interest candidate | Narrowband drift, clean IR excess, unexplained archival anomaly, strong provenance |
| Natural source | Dust, YSO, AGB, galaxy, AGN, variability, moving object |
| Human interference | RFI, satellite/aircraft bands, OFF-target radio recurrence |
| Instrumental artifact | Band-edge behavior, gain instability, plate defects, saturation |
| Catalog or processing error | Bad flags, duplicate associations, cross-match ambiguity |
| Known object | SIMBAD/VizieR match, known source class, known contaminant |
| Noise or low confidence | Low SNR, incomplete metadata, weak single-epoch evidence |

### Outputs

- Posterior probabilities
- False-positive probability
- Signal reality confidence
- Novelty score
- Follow-up value
- Review readiness
- Conservative pathway recommendation

👉 See [`docs/SCORING_MODEL.md`](docs/SCORING_MODEL.md)

---

## 🔭 Data Sources

Default tests use synthetic fixtures and mocked provider metadata. Real provider access must be explicit, opt-in, and provenance-preserving.

| Source | Use in Project | Notes |
|--------|----------------|-------|
| Breakthrough Listen-style radio data | Radio SETI candidate search | Future file/hit-table ingestion; no default network access |
| Gaia DR3 | Stellar context, parallax, proper motion, source quality | Used for infrared and archival context |
| 2MASS | Near-infrared photometry | Helps characterize stellar SEDs and contaminants |
| WISE / AllWISE / CatWISE | Mid-infrared photometry and motion-sensitive catalog context | Supports IR-excess and blending checks |
| VizieR | Catalog cross-identification | Used for known-object and contaminant context |
| SIMBAD | Object identity and bibliography context | Used for known-object annotation |
| Historical / modern catalogs | Archival anomaly checks | Future curated datasets only; no large data committed |

All data products remain governed by their original licenses, citation requirements, and provider policies.

---

## 🚀 Installation

Use the local virtual environment. Do not rely on system Python packages.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Confirm the CLI is available:

```bash
.venv/bin/techno-search --help
```

---

## ⚡ Quick Start

Score one synthetic radio candidate:

```bash
.venv/bin/techno-search score examples/candidates/radio_clean_candidate.json
```

Write Markdown, JSON, manifest, and synthetic diagnostic artifacts:

```bash
.venv/bin/techno-search score \
  examples/candidates/radio_clean_candidate.json \
  --output-dir examples/reports \
  --prefix example-radio-clean
```

Score every example candidate:

```bash
.venv/bin/techno-search score-batch examples/candidates examples/batch_reports
```

Run local validation summaries:

```bash
.venv/bin/techno-search validate-all
.venv/bin/techno-search validation-summary
```

👉 See [`docs/CLI_USAGE.md`](docs/CLI_USAGE.md)

---

## 🧪 Quality Control

Minimum validation:

```bash
.venv/bin/python -m pytest
```

Release-grade local validation:

```bash
.venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing
.venv/bin/ruff check .
.venv/bin/mypy src
git diff --check
```

Scientific quality gates:

- Default tests must be deterministic and non-networked.
- Live-provider tests must be opt-in and marked separately.
- Candidate reports must include positive evidence, negative evidence, blocking issues, and provenance.
- Report language must remain conservative.
- Score changes must be checked against score-regression fixtures.
- Calibration summaries are synthetic development diagnostics, not survey-performance claims.

👉 See [`docs/VALIDATION.md`](docs/VALIDATION.md)

---

## 📤 Submission Pathways

Candidates are routed conservatively:

```text
Known object or known artifact
  → known_object_annotation

Strong false-positive evidence
  → do_not_submit_false_positive

Weak, incomplete, or method-development result
  → github_reproducibility_only

Ambiguous but review-worthy candidate
  → human_review_queue

Stronger, well-documented, still unconfirmed candidate
  → candidate_review_packet

Rare, reviewed, reproducible follow-up target
  → external_followup_candidate
```

No pathway is a confirmation claim.

👉 See [`docs/SUBMISSION_PATHWAYS.md`](docs/SUBMISSION_PATHWAYS.md)

---

## 📂 Repository Layout

```text
src/techno_search/      Python package
configs/                Versioned scoring and track configs
docs/                   Project specifications and policies
schemas/                Machine-readable JSON schemas
examples/               Synthetic candidate inputs and report outputs
tests/                  Unit, regression, schema, and validation tests
```

Key package modules:

| Module | Purpose |
|--------|---------|
| `schemas.py` | Candidate and scored-candidate types |
| `scoring.py` | Posterior-style scoring |
| `pathway.py` | Conservative pathway routing |
| `reporting.py` | Markdown/JSON report packet generation |
| `provenance.py` | Provenance summaries |
| `review_queue.py` | Human-review queue and consensus fixtures |
| `validation.py` | Candidate and report validation |
| `validation_datasets.py` | Validation dataset and promotion summaries |
| `live_data.py` | Guarded provider interfaces and cache policy |

---

## 🖥 Local System Profile

Local development and batch-run sizing guidance is recorded in [`docs/LOCAL_SYSTEM_PROFILE.md`](docs/LOCAL_SYSTEM_PROFILE.md).

Performance defaults may use that profile, but scientific scores, thresholds, candidate claims, and provenance requirements must remain portable and configurable.

---

## 🛡 Guardrails

This project must not claim a confirmed technosignature.

Required language:

- candidate signal
- anomaly
- follow-up target
- technosignature-interest candidate

Avoid unsupported language:

- confirmed technosignature
- alien signal
- discovery of extraterrestrial intelligence
- proof of extraterrestrial intelligence

Data guardrails:

- Do not commit raw survey data.
- Do not commit catalog caches.
- Do not commit API keys or credentials.
- Keep live-data access explicit and opt-in.
- Preserve source IDs, query parameters, cache keys, schema versions, config versions, and code provenance where applicable.

---

## ⚠️ Important Disclaimer

This project identifies **candidate signals and anomalies only**.

❌ No claims of confirmed technosignatures
❌ No discovery announcements
❌ No replacement for professional validation pipelines
❌ No external follow-up without human review and independent validation

---

## 📚 Works Cited

Enriquez, J. Emilio, et al. “The Breakthrough Listen Search for Intelligent Life: 1.1–1.9 GHz Observations of 692 Nearby Stars.” *The Astrophysical Journal*, vol. 849, no. 2, 2017, p. 104. DOI: [10.3847/1538-4357/aa8d1b](https://doi.org/10.3847/1538-4357/aa8d1b).

Gaia Collaboration, A. Vallenari, et al. “Gaia Data Release 3: Summary of the Content and Survey Properties.” *Astronomy & Astrophysics*, vol. 674, 2023, A1. DOI: [10.1051/0004-6361/202243940](https://doi.org/10.1051/0004-6361/202243940).

Marocco, Federico, et al. “The CatWISE2020 Catalog.” *The Astrophysical Journal Supplement Series*, vol. 253, no. 1, 2021, p. 8. DOI: [10.3847/1538-4365/abd805](https://doi.org/10.3847/1538-4365/abd805).

NASA Technosignatures Workshop Participants. “NASA and the Search for Technosignatures: A Report from the NASA Technosignatures Workshop.” *arXiv*, 2018. DOI: [10.48550/arXiv.1812.08681](https://doi.org/10.48550/arXiv.1812.08681).

Ochsenbein, F., P. Bauer, and J. Marcout. “The VizieR Database of Astronomical Catalogues.” *Astronomy and Astrophysics Supplement Series*, vol. 143, 2000, pp. 23–32. DOI: [10.1051/aas:2000169](https://doi.org/10.1051/aas:2000169).

Skrutskie, M. F., et al. “The Two Micron All Sky Survey (2MASS).” *The Astronomical Journal*, vol. 131, no. 2, 2006, pp. 1163–1183. DOI: [10.1086/498708](https://doi.org/10.1086/498708).

Wenger, M., et al. “The SIMBAD Astronomical Database: The CDS Reference Database for Astronomical Objects.” *Astronomy and Astrophysics Supplement Series*, vol. 143, 2000, pp. 9–22. DOI: [10.1051/aas:2000332](https://doi.org/10.1051/aas:2000332).

Wright, Edward L., et al. “The Wide-field Infrared Survey Explorer (WISE): Mission Description and Initial On-Orbit Performance.” *The Astronomical Journal*, vol. 140, no. 6, 2010, pp. 1868–1881. DOI: [10.1088/0004-6256/140/6/1868](https://doi.org/10.1088/0004-6256/140/6/1868).

---

## 📜 License

- Code: Apache 2.0
- Documentation: CC-BY-4.0 unless otherwise noted

External datasets are not relicensed by this repository. Users must follow the terms and citation requirements of the original data providers.

---

## 🔭 Vision

Build a system that produces:

> **Scientifically defensible, reproducible technosignature-interest candidates**

not unsupported claims.
