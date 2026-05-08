# 🛰 2026 Technosignature Search

![Status](https://img.shields.io/badge/status-active%20development-blue)
![License](https://img.shields.io/badge/license-Apache%202.0-green)
![Focus](https://img.shields.io/badge/focus-technosignatures-purple)

---

## 🌌 Overview

A **research-grade, reproducible pipeline** for detecting and evaluating technosignature-interest candidates from existing astronomical datasets.

Initial search modes:

```text
Radio SETI → Infrared Waste Heat → Archival / Catalog Anomalies
```

### Core Flow

```
Existing Data → Candidate Extraction → Vetting → Bayesian Scoring → Review Pathway
```

This project prioritizes:
- Scientific rigor
- Low false-positive rates
- Reproducibility
- High-value follow-up targets
- Conservative candidate reporting

---

## 🧠 Key Idea

Most signals are **not technosignatures**.

This system is built to **disprove signals first**, then elevate only the strongest candidates for human review and possible follow-up.

---

## 📊 Current Status

**Phase:** Initial v0 Implementation / Synthetic Scoring Core

- ✅ Repo initialized
- ✅ Documentation system built
- ✅ Scoring architecture defined
- ✅ Synthetic radio, infrared, and archival anomaly prototypes implemented
- ✅ Candidate reporting and validation system implemented
- ⏳ Live-data workflows remain opt-in and provenance-only

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
| 7 | Calibration |
| 8 | Injection–recovery |
| 9 | Human review workflow |
| 10 | Guarded live-data integrations |

👉 See [`docs/ROADMAP.md`](docs/ROADMAP.md)

---

## ⚙️ Architecture

```
Ingest → Normalize → Search → Vet → Score → Classify → Report
```

| Module | Purpose |
|-------|--------|
| schemas.py | Candidate and scored-candidate data structures |
| provenance.py | Source, config, cache, and code provenance tracking |
| scoring.py | Bayesian-style candidate classification |
| pathway.py | Conservative review and submission routing |
| reporting.py | Markdown, JSON, and manifest candidate packets |
| radio/ | Radio SETI synthetic hit and injection prototypes |
| infrared/ | Infrared excess and contaminant-rejection prototypes |
| anomalies/ | Archival and catalog anomaly prototypes |
| live_data.py | Guarded provider interfaces and cache policy |

👉 See [`docs/PIPELINE_SPEC.md`](docs/PIPELINE_SPEC.md)

---

## 📐 Scoring Model

Bayesian framework:

```
P(H | D) ∝ P(D | H) P(H)
```

Multi-hypothesis normalization:

```
P(H_i | D) = P(D | H_i) P(H_i) / Σ_j P(D | H_j) P(H_j)
```

Current v0 approximation:

```
log_score_i = log_prior_i + weighted_evidence_i
posterior_i = softmax(log_score_i)
```

Hypotheses:
- Technosignature-interest candidate
- Natural source
- Human interference
- Instrumental artifact
- Catalog or processing error
- Known object
- Noise or low-confidence event

Outputs:
- Posterior probabilities
- False positive probability
- Signal reality confidence
- Follow-up value
- Review readiness
- Submission pathway

👉 See [`docs/SCORING_MODEL.md`](docs/SCORING_MODEL.md)

---

## 📂 Project Structure

```
src/
configs/
docs/
schemas/
examples/
tests/
```

## 🖥 Local System Profile

Local development and batch-run sizing guidance is recorded in [`docs/LOCAL_SYSTEM_PROFILE.md`](docs/LOCAL_SYSTEM_PROFILE.md).

---

## ⚠️ Important Disclaimer

This project identifies **candidate signals and anomalies only**.

❌ No claims of confirmed technosignatures
❌ No discovery announcements
❌ No replacement for professional validation pipelines

Use conservative language:
- candidate signal
- anomaly
- follow-up target
- technosignature-interest candidate

---

## 📜 License

- Code: Apache 2.0
- Docs: CC-BY-4.0

External datasets are not relicensed by this repository. Users must follow the terms and citation requirements of the original data providers.

---

## 🔭 Vision

Build a system that produces:

> **Scientifically defensible, reproducible technosignature-interest candidates**

not just interesting anomalies.
