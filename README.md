# 🛰 2026 Technosignature Search

![Status](https://img.shields.io/badge/status-active%20development-blue)
![License](https://img.shields.io/badge/license-Apache%202.0-green)
![Focus](https://img.shields.io/badge/focus-technosignatures-purple)
![Mode](https://img.shields.io/badge/search-multimodal-orange)

---

## 🌌 Overview

A **research-grade, reproducible, multi-modal citizen-science pipeline** for searching existing astronomical datasets for technosignature-interest candidates.

### Core Flow

```text
Ingest → Normalize → Search → Vet → Score → Classify → Report
```

Search tracks:

```text
Radio SETI → Infrared Waste Heat → Archival / Catalog Anomalies
```

This project prioritizes:

- Conservative scientific language
- Explicit false-positive modeling
- Reproducible candidate packets
- Provenance-preserving reports
- Human-in-the-loop triage
- Synthetic injection, recovery, and calibration fixtures

---

## 🧠 Key Idea

Most apparent technosignature-like signals are **false positives until shown otherwise**.

This system is built to **disprove candidate signals first**, preserve negative evidence, and elevate only the strongest follow-up targets for human review.

---

## 📊 Current Status

**Phase:** Initial v0 Implementation / Synthetic Scoring Core

- ✅ Multi-modal project scope selected
- ✅ Package scaffold implemented: `techno_search`
- ✅ Synthetic scoring and pathway core implemented
- ✅ Radio, infrared, and archival anomaly prototypes added
- ✅ Markdown, JSON, manifest, and synthetic plot report outputs added
- ✅ CLI scoring, validation, reporting, and summary commands added
- ✅ Human-review queue, consensus labels, and consensus export fixtures added
- ✅ Calibration, reliability, precision-recall, and benchmark metadata fixtures added
- ✅ Guarded live-provider interfaces and local cache guardrails added

👉 See [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md)

---

## 🛣 Roadmap

| Milestone | Description |
|----------|-------------|
| 1 | Multi-modal scoring core |
| 2 | Radio SETI synthetic candidate tests |
| 3 | Radio ingestion and hit scoring demo |
| 4 | Infrared catalog anomaly prototype |
| 5 | Archival anomaly prototype |
| 6 | Candidate reporting system |
| 7 | Injection-recovery calibration |
| 8 | Human-review workflow |
| 9 | Live data integrations behind opt-in guards |
| 10 | Advanced AI research only after baselines and calibration |

👉 See [`docs/ROADMAP.md`](docs/ROADMAP.md)

---

## ⚙️ Architecture

```text
Ingest → Normalize → Search → Vet → Score → Classify → Report
```

| Module | Purpose |
|--------|---------|
| `schemas.py` | Candidate and scored-candidate data structures |
| `scoring.py` | Interpretable posterior-style scoring |
| `pathway.py` | Conservative pathway classification |
| `reporting.py` | Markdown, JSON, and manifest review packets |
| `provenance.py` | Source, config, cache, and code provenance summaries |
| `radio/` | Synthetic radio hit-table and injection helpers |
| `infrared/` | Synthetic infrared excess prototype |
| `anomalies/` | Synthetic archival/catalog anomaly prototype |
| `live_data.py` | Opt-in provider adapters and cache guardrails |
| `review_queue.py` | Human-review queue, consensus, and export summaries |
| `validation*.py` | Candidate, report, dataset, and promotion validation helpers |

👉 See [`docs/PIPELINE_SPEC.md`](docs/PIPELINE_SPEC.md)

---

## 📐 Scoring Model

The v0 scorer uses an interpretable log-score approximation to a multi-hypothesis Bayesian framing:

```text
P(H_i | D) = P(D | H_i) P(H_i) / Σ_j P(D | H_j) P(H_j)
```

Hypotheses include:

- Technosignature-interest candidate
- Natural source
- Human interference
- Instrumental artifact
- Catalog or processing error
- Known object
- Noise or low-confidence event

Outputs:

- Posterior-style probabilities
- False-positive probability
- Signal reality confidence
- Novelty score
- Follow-up value
- Review readiness
- Recommended pathway

👉 See [`docs/SCORING_MODEL.md`](docs/SCORING_MODEL.md)

---

## 🔎 Search Tracks

| Track | Initial Focus |
|-------|---------------|
| Radio SETI | Narrowband or drifting candidate signals, RFI rejection, ON/OFF cadence checks, waterfall-style diagnostics |
| Infrared Waste Heat | Gaia, 2MASS, WISE/CatWISE context, SED residuals, mid-infrared excess, dust/AGN/blending rejection |
| Archival / Catalog Anomalies | Vanishing or appearing sources, cross-match failures, proper-motion checks, survey-depth and artifact rejection |

Track specs:

- [`docs/RADIO_SEARCH_SPEC.md`](docs/RADIO_SEARCH_SPEC.md)
- [`docs/INFRARED_SEARCH_SPEC.md`](docs/INFRARED_SEARCH_SPEC.md)
- [`docs/ANOMALY_SEARCH_SPEC.md`](docs/ANOMALY_SEARCH_SPEC.md)

---

## ⚡ Quickstart

Create and install the local development environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Score one synthetic candidate:

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

Score every candidate in a directory:

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

## 📦 Example Outputs

- Single radio packet: [`example-radio-clean.md`](examples/reports/example-radio-clean.md)
- Single radio manifest: [`example-radio-clean.manifest.json`](examples/reports/example-radio-clean.manifest.json)
- Batch manifest: [`batch_manifest.json`](examples/batch_reports/batch_manifest.json)
- Batch radio packet: [`example-radio-clean.md`](examples/batch_reports/example-radio-clean.md)
- Batch infrared packet: [`example-infrared-clean.md`](examples/batch_reports/example-infrared-clean.md)
- Batch anomaly packet: [`example-anomaly-clean.md`](examples/batch_reports/example-anomaly-clean.md)

Review packets are conservative artifacts. They are not discovery claims, and they retain false-positive discussion, negative evidence, blocking issues, provenance, and the required disclaimer.

---

## 🧾 Schemas

| Schema | Path |
|--------|------|
| Candidate packet | [`schemas/candidate_packet.schema.json`](schemas/candidate_packet.schema.json) |
| Report manifest | [`schemas/report_manifest.schema.json`](schemas/report_manifest.schema.json) |
| Batch manifest | [`schemas/batch_manifest.schema.json`](schemas/batch_manifest.schema.json) |
| Human-review queue | [`schemas/review_queue.schema.json`](schemas/review_queue.schema.json) |
| Human-review consensus | [`schemas/consensus_labels.schema.json`](schemas/consensus_labels.schema.json) |
| Human-review consensus export | [`schemas/consensus_export.schema.json`](schemas/consensus_export.schema.json) |
| Validation dataset manifest | [`schemas/validation_dataset_manifest.schema.json`](schemas/validation_dataset_manifest.schema.json) |
| Validation promotion rules | [`schemas/validation_promotion_rules.schema.json`](schemas/validation_promotion_rules.schema.json) |
| Benchmark metadata | [`schemas/benchmark_metadata.schema.json`](schemas/benchmark_metadata.schema.json) |
| Benchmark run results | [`schemas/benchmark_run_results.schema.json`](schemas/benchmark_run_results.schema.json) |

👉 See [`docs/VALIDATION.md`](docs/VALIDATION.md) and [`docs/SCHEMA_VERSIONING.md`](docs/SCHEMA_VERSIONING.md)

---

## 📂 Project Structure

```text
src/techno_search/
configs/
docs/
schemas/
examples/
tests/
```

---

## 🖥 Local System Profile

Local development and batch-run sizing guidance is recorded in [`docs/LOCAL_SYSTEM_PROFILE.md`](docs/LOCAL_SYSTEM_PROFILE.md).

Performance defaults may use that profile, but scientific scores, thresholds, candidate claims, and provenance requirements must remain portable and configurable.

---

## ⚠️ Important Disclaimer

This project identifies **candidate signals, anomalies, and follow-up targets only**.

- ❌ No claims of confirmed technosignatures
- ❌ No automated discovery announcements
- ❌ No replacement for professional validation
- ❌ No external follow-up without human review and independent validation

Use conservative language:

- candidate signal
- anomaly
- follow-up target
- technosignature-interest candidate

---

## 📜 License

- Code: Apache 2.0
- Documentation: CC-BY-4.0 unless otherwise noted

External datasets are not relicensed by this repository. Users must follow the terms and citation requirements of the original data providers.

---

## 🔭 Vision

Build a serious citizen-science platform that produces:

> **Scientifically defensible, reproducible technosignature-interest candidates**

not unsupported claims.
