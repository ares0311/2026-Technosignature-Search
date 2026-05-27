# 🛰 2026 Technosignature Search

![Status](https://img.shields.io/badge/status-active%20development-blue)
![License](https://img.shields.io/badge/license-Apache%202.0-green)
![Focus](https://img.shields.io/badge/focus-technosignatures-purple)
![Mode](https://img.shields.io/badge/search-multimodal-orange)

---

## 📑 Table of Contents

| Section | Contents |
|---------|----------|
| [Introduction](#-introduction) | Abstract, modal search scope, core premise, and at-a-glance summary |
| [Scientific Motivation](#-scientific-motivation) | Research questions and false-positive-first scientific framing |
| [Current Status](#-current-status) | Active implementation state and project phase |
| [Project Roadmap](#-project-roadmap) | Roadmap milestones aligned to the implementation plan |
| [Pipeline Architecture](#%EF%B8%8F-pipeline-architecture) | Global flow, track-specific flow, null models, and shared stage contract |
| [Methodology and Scoring Equations](#-methodology-and-scoring-equations) | Roadmap-aligned methodology, Bayesian framing, scoring equations, calibration targets, and hypotheses |
| [Data Sources](#-data-sources) | Radio, infrared, astrometric, catalog, and archival source roles |
| [Installation](#-installation) | Local `.venv` setup and editable install instructions |
| [Quick Start](#-quick-start) | First scoring, report generation, and validation commands |
| [Using and Recalibrating the Model](#-using-and-recalibrating-the-model) | Operator workflow, recalibration, background target selection, and passive ledger logging |
| [Quality Control](#-quality-control) | Validation commands, test gates, and risk-control matrix |
| [Submission Pathways](#-submission-pathways) | Conservative routing from likely false positives to review packets |
| [Repository Layout](#-repository-layout) | Package, docs, examples, schemas, tests, and fixtures |
| [Local System Profile](#-local-system-profile) | Hardware-aware defaults without scientific hard-coding |
| [Guardrails](#-guardrails) | Scientific, engineering, data, and background-search constraints |
| [Important Disclaimer](#%EF%B8%8F-important-disclaimer) | Explicit limits on claims and interpretation |
| [Works Cited](#-works-cited) | MLA-style references |
| [License](#-license) | Apache 2.0 license |
| [Vision](#-vision) | Long-term project direction |

---

## 🌌 Introduction

### Abstract

Technosignature searches require an analysis framework that is simultaneously sensitive to unusual signals and aggressively skeptical of their interpretation. Existing astronomical archives contain radio observations, infrared photometry, astrometric catalogs, and historical survey records that can be searched for candidate signals or anomalies, but the same archives also contain abundant terrestrial interference, instrumental artifacts, catalog ambiguities, natural astrophysical contaminants, and selection effects. This project develops a reproducible, multi-modal technosignature-interest candidate pipeline that treats those false-positive explanations as the default scientific hypothesis.

The pipeline integrates three search tracks: narrowband or Doppler-drifting radio candidates, infrared-excess or waste-heat-interest catalog candidates, and archival/catalog anomalies such as missing, appearing, displaced, or strongly variable sources. Each track emits a normalized feature packet, preserves provenance, records positive and negative evidence, and routes the result through a shared Bayesian-style scoring and conservative pathway framework. The scoring layer evaluates multiple competing hypotheses, including natural sources, human interference, instrumental artifacts, catalog or processing errors, known objects, low-confidence noise, and technosignature-interest candidates. In the current v0 implementation, calibrated empirical likelihoods are not yet claimed; instead, interpretable log-score approximations and synthetic fixtures provide a transparent baseline for regression testing and future calibration.

The methodological objective is not to identify confirmed technosignatures. It is to produce auditable review packets that make uncertainty explicit, expose blocking issues, retain false-positive evidence, and prioritize candidates for human review only when the available evidence justifies further attention. This makes the project a candidate-evaluation and reproducibility system rather than an announcement or discovery platform.

### Modal Search Scope

```text
Radio SETI          → narrowband / drifting candidate signals
Infrared catalogs   → waste-heat-interest excess candidates
Archival catalogs   → cross-survey anomaly candidates
```

### Core Premise

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

### At a Glance

| Dimension | Design Choice |
|-----------|---------------|
| Scientific posture | Candidate triage and reproducible follow-up prioritization, not discovery claims |
| Default hypothesis | False positive until evidence survives structured vetting |
| Search geometry | Multi-modal: radio, infrared, and archival/catalog anomaly tracks |
| Output artifact | Human-readable Markdown plus machine-readable JSON candidate packets |
| Statistical stance | Interpretable Bayesian-style scoring before learned triage models |
| Validation mode | Synthetic fixtures, score regression snapshots, and non-networked tests by default |

---

## 🧠 Scientific Motivation

Technosignature searches are unusually vulnerable to overinterpretation. Radio signals can be terrestrial interference. Infrared excess can be dust, galaxies, young stellar objects, AGB stars, or blending. Archival anomalies can be plate defects, moving objects, survey-depth differences, proper motion, or catalog mismatch.

This repository treats those explanations as the default. The goal is to produce scientifically defensible **candidate signals**, **anomalies**, and **follow-up targets**, not claims of confirmed technosignatures.

The workflow follows the same broad pattern used in exoplanet vetting: detect an interesting signal, attack it with known false-positive explanations, quantify uncertainty, and route it conservatively.

### Research Questions

| Question | Operational Test |
|----------|------------------|
| Is the signal or anomaly real? | Require signal-reality features, metadata completeness, and reproducible candidate packet generation |
| Is it unusual after known explanations? | Compare candidate evidence against RFI, dust, AGN, artifact, moving-object, and catalog-error hypotheses |
| Which false-positive class is most plausible? | Preserve explicit false-positive features and negative evidence in every packet |
| Is follow-up scientifically useful? | Estimate follow-up value and review readiness separately from candidate-interest score |
| Is the result ready for external attention? | Route through conservative pathways and block unsupported claims |

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
| 2 | Radio SETI prototype | ✅ Implemented |
| 3 | Infrared waste-heat prototype | ✅ Implemented |
| 4 | Archival / catalog anomaly prototype | ✅ Implemented |
| 5 | Reproducible reporting system | ✅ Implemented |
| 6 | Injection-recovery diagnostics | ✅ Implemented |
| 7 | Human-review workflow | ✅ Implemented |
| 8 | Guarded live-data integrations and background search scaffold | ✅ Scaffolded / opt-in |
| 9 | Calibration fixtures, summaries, and benchmark metadata | ✅ Implemented |
| 10 | Advanced AI research track after calibration | ⏳ Deferred |

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

### Evidence and Null-Model Matrix

| Track | Candidate Signal | Primary Null Models | Required Negative Evidence |
|-------|------------------|---------------------|----------------------------|
| Radio SETI | Narrowband, drifting, structured, or cadence-selected signal | RFI, satellite/aircraft emission, band-edge artifact, gain instability, low-SNR noise | OFF-target behavior, frequency persistence, known RFI overlap, metadata quality |
| Infrared Waste Heat | Mid-infrared excess or SED residual around a stellar-like source | Dust, YSO, AGB star, galaxy, AGN, blending, photometric artifact | Gaia solution quality, WISE/2MASS flags, confusion score, natural-source indicators |
| Archival / Catalog Anomaly | Missing, appearing, displaced, or strongly changed source | Proper motion, moving object, plate defect, survey-depth mismatch, bandpass effect, catalog mismatch | Epoch metadata, survey limits, artifact score, cross-match confidence |

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

### Roadmap-Aligned Methodology

The roadmap is methodological, not merely organizational. Each milestone adds a bounded scientific capability while preserving the same conservative inference contract: detect or ingest only enough to build a candidate packet, attack ordinary explanations first, score competing hypotheses, and emit a reproducible review artifact.

| Roadmap Milestone | Methodological Role | README Section That Implements It |
|-------------------|---------------------|-----------------------------------|
| 1. Multi-modal scoring core | Define shared hypotheses, posterior-style scores, pathway logic, and false-positive-first interpretation | Feature representation, Bayesian framing, v0 approximation, false-positive probability |
| 2. Radio SETI prototype | Test narrowband/drift candidates against RFI, cadence, metadata, and instrumental null models | Track-specific flow, evidence and null-model matrix, radio data sources |
| 3. Infrared waste-heat prototype | Test catalog/SED excess candidates against dust, galaxies, AGN, blending, and photometric artifacts | Track-specific flow, hypotheses, Gaia/2MASS/WISE data sources |
| 4. Archival/catalog anomaly prototype | Test missing, appearing, displaced, or variable sources against proper motion, depth, moving-object, and artifact explanations | Track-specific flow, null-model matrix, historical/modern catalog sources |
| 5. Reporting system | Preserve positive evidence, negative evidence, blocking issues, provenance, schema versions, and conservative pathway routing | Shared stage contract, outputs, quality control, submission pathways |
| 6. Injection-recovery | Measure whether synthetic signals are recovered and whether synthetic false alarms remain controlled | Calibration targets, quality-control matrix |
| 7. Human review | Treat review labels, consensus, and exports as triage artifacts rather than validation or discovery claims | Using the model, quality control, submission pathways |
| 8. Live-data integrations | Keep provider access opt-in, cached, provenance-only by default, and compatible with background ledger logging | Data sources, background logging requirements, guardrails |
| 9. Calibration | Evaluate reliability, precision-recall, false-positive classes, benchmark metadata, and score stability before empirical claims | Calibration targets and recalibration workflow |
| 10. Advanced AI research | Permit learned triage only after interpretable baselines, validation datasets, provenance, and calibration exist | Guardrails and roadmap deferral |

The resulting staged method can be summarized as:

$$
\mathcal{M}_{\mathrm{roadmap}} =
\left[
\mathrm{score},
\mathrm{radio},
\mathrm{infrared},
\mathrm{anomaly},
\mathrm{report},
\mathrm{inject/recover},
\mathrm{review},
\mathrm{live\ opt\mbox{-}in},
\mathrm{calibrate},
\mathrm{AI\ after\ calibration}
\right]
$$

The order matters. Large-scale live search and advanced AI triage are downstream of transparent scoring, fixture coverage, report generation, human review, and calibration diagnostics.

### Feature Representation

Each candidate is represented as a track-specific feature vector:

$$
\mathbf{x} =
\left[x_{\mathrm{signal}}, x_{\mathrm{quality}}, x_{\mathrm{provenance}},
x_{\mathrm{artifact}}, x_{\mathrm{natural}}, x_{\mathrm{known}}\right]
$$

The hypothesis set is:

$$
\mathcal{H} =
\{H_{\mathrm{tech}}, H_{\mathrm{natural}}, H_{\mathrm{human}},
H_{\mathrm{instrument}}, H_{\mathrm{catalog}}, H_{\mathrm{known}}, H_{\mathrm{noise}}\}
$$

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

The odds between a candidate-interest hypothesis and a false-positive hypothesis can be summarized by a Bayes factor:

$$
K_{ij} =
\frac{P(D \mid H_i)}{P(D \mid H_j)}
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

### Derived Review Scores

The scorer separates candidate interest from operational readiness:

$$
S_{\mathrm{reality}} =
g(\mathrm{SNR}, \mathrm{repeatability}, \mathrm{data\ quality}, \mathrm{metadata})
$$

$$
S_{\mathrm{novelty}} =
1 - P(H_{\mathrm{known}} \mid D)
$$

$$
S_{\mathrm{followup}} =
h(S_{\mathrm{reality}}, S_{\mathrm{novelty}}, P(H_{\mathrm{tech}} \mid D), P(\mathrm{false\ positive}))
$$

### Review Readiness

The current implementation tracks review readiness as a conservative derived score:

$$
R =
f(\mathrm{signal\ reality}, \mathrm{provenance}, \mathrm{metadata}, \mathrm{negative\ evidence}, \mathrm{blocking\ issues})
$$

where \(R\) is not a discovery probability. It is a measure of whether the packet has enough context for meaningful review.

### Calibration Targets

Future empirical calibration should evaluate reliability and ranking quality:

$$
\mathrm{Brier} =
\frac{1}{N}\sum_{n=1}^{N}\left(p_n - y_n\right)^2
$$

$$
\mathrm{ECE} =
\sum_{m=1}^{M}\frac{|B_m|}{N}
\left|\mathrm{acc}(B_m) - \mathrm{conf}(B_m)\right|
$$

$$
\mathrm{Precision} =
\frac{TP}{TP + FP},
\qquad
\mathrm{Recall} =
\frac{TP}{TP + FN}
$$

Until non-synthetic validation sets exist, these summaries are development diagnostics only.

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

| Source | Use in Project | Principal Features | Failure Modes to Preserve |
|--------|----------------|--------------------|---------------------------|
| Breakthrough Listen-style radio data | Radio SETI candidate search | Frequency, drift rate, SNR, ON/OFF cadence, bandwidth | RFI, backend artifacts, frequency persistence, missing OFF scans |
| Gaia DR3 | Stellar context and astrometry | Parallax, proper motion, quality flags, source identity | Bad astrometric solution, non-stellar source, cross-match ambiguity |
| 2MASS | Near-infrared photometry | J/H/K photometry, near-IR color context | Saturation, blending, catalog mismatch |
| WISE / AllWISE / CatWISE | Mid-infrared photometry and motion-sensitive catalog context | W1-W4 fluxes, mid-IR colors, source confusion | AGN, galaxy, dust, YSO, AGB, poor image quality |
| VizieR | Literature catalog cross-identification | Catalog membership, source class context | Known contaminant, inconsistent identifiers |
| SIMBAD | Object identity and bibliography context | Object type, aliases, known-source annotations | Known object masquerading as a new candidate |
| Historical / modern catalogs | Archival anomaly checks | Epoch, magnitude, limits, cross-match confidence | Proper motion, moving object, survey-depth mismatch, plate artifact |

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

Validate and run one local CSV input through the hardened ingestion path:

```bash
.venv/bin/techno-search validate-input tests/fixtures/radio/sample_hits.csv --track radio
.venv/bin/techno-search run-pipeline tests/fixtures/radio/sample_hits.csv \
  --track radio \
  --output-dir artifacts/pipeline_smoke \
  --candidate-id local-radio-smoke
.venv/bin/techno-search rfi-database-summary
.venv/bin/techno-search rfi-database-admission-summary
.venv/bin/techno-search curated-dataset-admission-summary
.venv/bin/techno-search project-status-consistency-summary
.venv/bin/techno-search production-blocker-consistency-summary
.venv/bin/techno-search operations-alert-review-consistency-summary
.venv/bin/techno-search operations-action-resolution-consistency-summary
.venv/bin/techno-search operations-blocker-progress-consistency-summary
```

Run local validation summaries:

```bash
.venv/bin/techno-search validate-all
.venv/bin/techno-search validation-summary
.venv/bin/techno-search operations-readiness-summary
.venv/bin/techno-search operations-action-plan-summary
.venv/bin/techno-search operations-action-resolution-summary
.venv/bin/techno-search operations-action-resolution-consistency-summary
.venv/bin/techno-search operations-blocker-detail-summary
.venv/bin/techno-search operations-blocker-review-summary
.venv/bin/techno-search operations-blocker-followup-summary
.venv/bin/techno-search operations-blocker-followup-progress-summary
.venv/bin/techno-search operations-blocker-progress-review-summary
.venv/bin/techno-search operations-blocker-progress-next-actions-summary
.venv/bin/techno-search operations-blocker-progress-execution-summary
.venv/bin/techno-search operations-blocker-progress-execution-review-summary
.venv/bin/techno-search operations-blocker-progress-execution-followup-summary
.venv/bin/techno-search operations-blocker-progress-consistency-summary
```

👉 See [`docs/CLI_USAGE.md`](docs/CLI_USAGE.md) and the non-networked CI
template guidance in [`docs/CI.md`](docs/CI.md).

---

## 🧭 Using and Recalibrating the Model

This section is for a non-specialist operator who wants to run the current scorer, understand what the output means, and eventually recalibrate it as better validation data becomes available.

### What the Model Does Today

The current v0 model is an interpretable scoring engine. It does not learn from the internet, does not observe the sky by itself, and does not claim discoveries. It reads a normalized candidate JSON packet, scores competing hypotheses, and writes a conservative review packet.

```text
Candidate JSON
  → feature validation
  → posterior-style hypothesis scores
  → false-positive probability
  → pathway recommendation
  → Markdown / JSON review packet
```

For a layperson, the most important fields are:

| Output Field | Plain-English Meaning | How to Use It |
|--------------|-----------------------|---------------|
| `false_positive_probability` | How strongly the current evidence points away from candidate interest | High values usually mean do not follow up |
| `signal_reality_confidence` | Whether the signal/anomaly appears real independent of interpretation | Low values mean the data itself is weak |
| `followup_value` | Whether more review or observation could be useful | High values identify worthwhile review targets |
| `review_readiness` | Whether the packet has enough context for another person to inspect | Low values mean provenance, metadata, or diagnostics are missing |
| `recommended_pathway` | Conservative routing decision | Use this as a triage label, not a claim |

### Current Operator Workflow

```text
1. Choose or create a candidate JSON file.
2. Run `techno-search score`.
3. Read the Markdown packet.
4. Inspect positive evidence, negative evidence, and blocking issues.
5. Use the recommended pathway to decide whether to ignore, review, or preserve the result.
```

Example:

```bash
.venv/bin/techno-search score \
  examples/candidates/radio_clean_candidate.json \
  --output-dir examples/reports \
  --prefix example-radio-clean
```

To ask the current background-search scaffold which target should be searched next, run:

```bash
.venv/bin/techno-search target-priority-summary
.venv/bin/techno-search target-priority-summary \
  --ledger-path artifacts/background_search_ledger.json
```

This command ranks the committed synthetic target list and returns a selected `target_id`. When a ledger path is supplied, the scheduler score boosts promising never-reviewed targets and applies a bounded penalty to targets already searched. The selected target is a scheduling recommendation only. It is not evidence of a technosignature and it is not a discovery claim.

To append one local-only passive/background search ledger entry for the highest-priority fixture target, run:

```bash
.venv/bin/techno-search background-run-once \
  --ledger-path artifacts/background_search_ledger.json \
  --reviewed-log-path artifacts/background_reviewed_log.json \
  --needs-follow-up-log-path artifacts/background_needs_follow_up_log.json \
  --sqlite-log-path logs/techno_search.sqlite3 \
  --acknowledge-local-run
```

The acknowledgement flag is intentional. The command records a local scheduling/search event without network access and without claiming candidate extraction. Each run writes one durable ledger entry and exactly one outcome entry: either the reviewed log or the needs-follow-up log. Operational logs should also be mirrored into the top-level SQLite database under `logs/`.

To inspect what the passive/background system has already searched, run:

```bash
.venv/bin/techno-search background-ledger-summary
.venv/bin/techno-search reviewed-log-summary
.venv/bin/techno-search needs-follow-up-summary
.venv/bin/techno-search follow-up-test-summary
.venv/bin/techno-search report-readiness-summary
.venv/bin/techno-search submission-recommendation-summary
.venv/bin/techno-search draft-follow-up-report-summary
.venv/bin/techno-search draft-follow-up-report-write \
  --output-dir artifacts/background_draft_reports
.venv/bin/techno-search validate-draft-reports artifacts/background_draft_reports
.venv/bin/techno-search user-decision-summary
.venv/bin/techno-search init-logs
.venv/bin/techno-search sqlite-log-bootstrap-summary
.venv/bin/techno-search sqlite-log-summary
.venv/bin/techno-search sqlite-log-integrity-summary
.venv/bin/techno-search sqlite-recent-runs
.venv/bin/techno-search sqlite-needs-follow-up
.venv/bin/techno-search sqlite-log-export
.venv/bin/techno-search sqlite-migration-summary
.venv/bin/techno-search sqlite-log-pragmas
.venv/bin/techno-search sqlite-log-backup
.venv/bin/techno-search sqlite-log-retention-summary
.venv/bin/techno-search sqlite-log-vacuum
.venv/bin/techno-search sqlite-log-commit-guard
.venv/bin/techno-search sqlite-log-consistency-summary
.venv/bin/techno-search validate-sqlite-logs
.venv/bin/techno-search scheduler-dry-run \
  --artifact-dir artifacts/background_scheduler_dry_run
```

The ledger summary reports searched targets, candidate counts, blocking issues, conservative pathway labels, and run IDs. The reviewed-log summary captures targets that do not currently require follow-up. The needs-follow-up summary captures targets requiring mandatory local tests, human review, and possible report preparation. Follow-up test and report-readiness summaries then show whether mandatory local checks are complete, whether a conservative draft report is allowed, and which top-three review destinations are recommended. Draft follow-up report summaries preserve evidence, negative evidence, uncertainty, limitations, blockers, and next steps; the writer can persist Markdown plus a manifest under ignored `artifacts/` paths. A small persisted example is committed under [`examples/background_draft_reports`](examples/background_draft_reports) for documentation review and can be inspected with `validate-draft-reports examples/background_draft_reports`. User-decision summaries preserve explicit choices to request more tests or close as reviewed while keeping external submission disabled unless the user explicitly approves it. The top-level SQLite log commands initialize, bootstrap readiness visibility, summarize, query, export, check migration status, print a non-destructive migration plan, print a review-safe weekly digest, inspect PRAGMA health, create ignored local backups, summarize retention state, compact the database with `VACUUM`, and validate `logs/techno_search.sqlite3`. The scheduler dry-run writes temporary local artifacts without enabling live provider access. Negative searches must still be logged because they are part of the reproducibility record.

Operators can also clean up the ignored `artifacts/` directory between sessions:

```bash
.venv/bin/techno-search artifacts-cleanup
.venv/bin/techno-search artifacts-cleanup --apply --acknowledge-local-apply
```

The dry-run plan never modifies committed project paths and the apply mode only deletes files under `artifacts/`. Cross-track candidate cross-references are operational metadata only; they link candidate IDs that share a target across radio, infrared, or anomaly tracks without modifying any score. Reproducibility verification re-scores persisted packets with the current scoring implementation and reports drift instead of auto-correcting historical artifacts:

```bash
.venv/bin/techno-search cross-track-summary
.venv/bin/techno-search verify-report-reproducibility examples/reports
.venv/bin/techno-search sqlite-log-weekly-digest
.venv/bin/techno-search sqlite-log-migrate
```

To inspect whether logged background runs are ready for reviewed handoff, run:

```bash
.venv/bin/techno-search background-reviewed-workflow-summary
```

The reviewed-workflow summary reports execution modes, scheduling-only entries, negative-result logging, target-selection rationales, candidate packet IDs, review blockers, and human-review requirements. These fields describe workflow readiness only. They do not turn a target-priority score or a ledger entry into candidate evidence.

To inspect the local handoff contract between a selected target and candidate extraction, run:

```bash
.venv/bin/techno-search candidate-extraction-handoff-summary
```

The handoff summary answers a practical operator question: "What must exist before this target can become a candidate packet?" It reports required inputs, available inputs, expected candidate packet IDs, fixture paths, blockers, negative-result requirements, and whether human review is required. All current handoffs are local fixtures with network access disabled.

### Recalibration Workflow

Recalibration means adjusting scoring assumptions after comparing model outputs against known synthetic injections, known contaminants, curated false-positive examples, or human-reviewed labels. It should not be done by hand-tuning one interesting candidate.

```text
Calibration fixtures
  → score candidates
  → compare expected vs. observed pathways
  → review reliability / precision / recall summaries
  → update versioned config or weights
  → rerun regression tests
  → document the change
```

Recalibration should preserve these rules:

| Rule | Reason |
|------|--------|
| Use validation sets, not single anecdotes | Prevents chasing noise |
| Keep synthetic and non-synthetic calibration separate | Avoids overstating real-world performance |
| Version every config change | Keeps scores reproducible |
| Rerun score-regression snapshots | Exposes unintended score drift |
| Preserve false-positive fixtures | Ensures obvious contaminants still reject conservatively |
| Document thresholds and rationale | Makes scientific choices auditable |

Recommended recalibration checks:

```bash
.venv/bin/techno-search calibration-summary
.venv/bin/techno-search calibration-track-summary
.venv/bin/techno-search false-positive-summary
.venv/bin/techno-search validation-readiness-summary
.venv/bin/techno-search reliability-summary
.venv/bin/techno-search precision-recall-summary
.venv/bin/techno-search score-regression-summary
.venv/bin/techno-search benchmark-run-summary
.venv/bin/techno-search benchmark-run-compare \
  --results-path artifacts/benchmark_run_results.json
.venv/bin/techno-search operations-readiness-digest
.venv/bin/techno-search operations-blocker-detail-summary
.venv/bin/techno-search operations-blocker-review-summary
.venv/bin/techno-search operations-blocker-followup-summary
.venv/bin/techno-search operations-blocker-followup-progress-summary
.venv/bin/techno-search operations-blocker-progress-review-summary
.venv/bin/techno-search operations-blocker-progress-next-actions-summary
.venv/bin/techno-search operations-blocker-progress-execution-summary
.venv/bin/techno-search operations-blocker-progress-execution-review-summary
.venv/bin/techno-search operations-blocker-progress-execution-followup-summary
.venv/bin/techno-search validate-all
```

When recording local benchmark runs, append rather than overwrite:

```bash
.venv/bin/techno-search benchmark-run-append \
  --results-path artifacts/benchmark_run_results.json \
  --run-id pytest-coverage-local-001 \
  --command-name "pytest coverage gate" \
  --command-kind test \
  --status passed \
  --worker-count 1 \
  --input-case-count 194 \
  --duration-seconds 1.58 \
  --git-commit "$(git rev-parse --short HEAD)" \
  --config-version scoring_v0
```

Benchmark run results record local execution context only. They are not calibrated survey sensitivity estimates or candidate-quality claims.

Before any curated non-synthetic dataset is used for calibration claims, inspect readiness:

```bash
.venv/bin/techno-search validation-readiness-summary
```

Readiness status is a gate, not a scientific result. `ready` means the dataset can be considered for curated review; `blocked` means unresolved provenance, licensing, labeling, or review issues remain; `not_yet_admissible` means the dataset is not currently suitable for calibration use.

### Target Selection and Background Search Roadmap

The current v0 background-search system is a fixture-backed scaffold. It can rank possible targets, expose the selected scheduler target, append a durable run ledger, and bifurcate outcomes into reviewed and needs-follow-up logs. It does not run unattended network searches, does not observe the sky by itself, and does not silently promote candidates. Operational background use should call `background-run-once` from an external scheduler rather than placing separate scientific logic in a long-lived process.

```text
Target list or provider query
  → target feature summary
  → priority score plus review-history adjustment
  → external scheduler invokes one bounded run
  → candidate-extraction handoff check
  → durable ledger entry
  → reviewed log OR needs-follow-up log
  → mandatory follow-up tests when warranted
  → report-readiness gate
  → top-three review/submission recommendations
  → candidate extraction / scoring / report only after gates pass
```

Target prioritization should be based on an auditable objective function:

$$
T =
\alpha S_{\mathrm{followup}}
+ \beta S_{\mathrm{novelty}}
+ \gamma S_{\mathrm{data\ quality}}
+ \delta S_{\mathrm{observability}}
- \lambda P(\mathrm{false\ positive})
$$

where \(T\) is a target-priority score, not evidence of a technosignature. The weights \(\alpha, \beta, \gamma, \delta,\lambda\) are versioned in [`configs/background_priority_v0.json`](configs/background_priority_v0.json) and should eventually be calibrated against validation datasets.

Scheduler selection adds a review-history term:

$$
T_{\mathrm{sched}} =
T + b_{\mathrm{new}}\mathbb{1}_{N_{\mathrm{review}}=0}
- \min(\rho N_{\mathrm{review}}, \rho_{\max})
$$

where \(b_{\mathrm{new}}\) boosts promising targets that have not yet been reviewed, \(N_{\mathrm{review}}\) is the number of prior ledger entries for the target, and the bounded penalty prevents the runner from repeatedly choosing the same target without new evidence. This is an operational scheduling term, not candidate evidence.

Current v0 target-priority fixture fields:

| Field | Plain-English Meaning |
|-------|-----------------------|
| `followup_value` | Whether another observation or human review would be useful |
| `novelty_score` | Whether the target looks unusual relative to synthetic comparison examples |
| `data_quality_score` | Whether the supporting metadata and observations are usable |
| `observability_score` | Whether the target is practical to revisit or inspect |
| `false_positive_probability` | How much the current evidence favors ordinary explanations |
| `blocking_issue_count` | How many unresolved issues should penalize priority |

The target selector deliberately subtracts false-positive probability and unresolved blocking issues. In other words, a target can look interesting and still lose priority if the ordinary explanations are too strong or if the packet is not review-ready.

### Background Logging Requirements

Any passive/background runner must maintain a search ledger. The operational log lives in a top-level SQLite database under `logs/`; the committed JSON fixtures remain small regression examples and compatibility artifacts.

| Log Field | Purpose |
|-----------|---------|
| `run_id` | Stable identifier for the background run |
| `target_id` | Source, coordinate, object name, or catalog identifier searched |
| `track` | Radio, infrared, or anomaly |
| `query_parameters` | Provider query, radius, filters, file path, or fixture ID |
| `started_at_utc` / `completed_at_utc` | Runtime provenance |
| `config_version` | Scoring and target-priority settings |
| `code_commit` | Reproducibility anchor |
| `cache_key` | Provider/cache provenance when applicable |
| `candidate_count` | Number of candidates generated |
| `execution_mode` | Local fixture runner, synthetic fixture, or future provider mode |
| `selected_priority_score` | Target-priority score that led to the search |
| `target_selection_rationale` | Auditable reasons the target was searched |
| `candidate_packet_ids` | Candidate packets produced, if any |
| `negative_result_logged` | Whether a no-candidate search was explicitly preserved |
| `requires_human_review` | Whether the logged result needs human review |
| `reviewed_workflow_status` | Candidate-packet-ready, blocked, negative-search, or scheduling-only state |
| `recommended_pathways` | Conservative routing results |
| `blocking_issues` | Missing metadata, failed providers, or invalid candidate packets |

The background system should never silently discard searched targets. A scientifically useful negative result still needs a log entry. The top-level SQLite database is the operational source of truth, while the JSON fixtures and outcome logs make the decision path easy to review:

| Outcome Log | Purpose |
|-------------|---------|
| `logs/techno_search.sqlite3` | Local operational SQLite database for runs, outcomes, draft report references, user decisions, and validation events |
| `background_reviewed_log.json` | Targets searched or assessed with no current follow-up trigger |
| `background_needs_follow_up_log.json` | Targets that require mandatory tests, report readiness review, or human judgment |
| `background_follow_up_tests.json` | Deterministic local follow-up test outcomes |
| `background_report_readiness.json` | Report drafting gates and top-three recommendation records |
| `background_draft_follow_up_reports.json` | Conservative draft report summaries for ready or blocked records |
| `background_user_decisions.json` | Explicit user decisions to request more tests, close as reviewed, or approve submission |

In v0, the committed ledger fixture is summarized by:

```bash
.venv/bin/techno-search background-ledger-summary
.venv/bin/techno-search background-reviewed-workflow-summary
.venv/bin/techno-search reviewed-log-summary
.venv/bin/techno-search needs-follow-up-summary
.venv/bin/techno-search follow-up-test-summary
.venv/bin/techno-search report-readiness-summary
.venv/bin/techno-search submission-recommendation-summary
.venv/bin/techno-search draft-follow-up-report-summary
.venv/bin/techno-search draft-follow-up-report-write \
  --output-dir artifacts/background_draft_reports
.venv/bin/techno-search validate-draft-reports artifacts/background_draft_reports
.venv/bin/techno-search user-decision-summary
.venv/bin/techno-search candidate-extraction-handoff-summary
.venv/bin/techno-search init-logs
.venv/bin/techno-search sqlite-log-bootstrap-summary
.venv/bin/techno-search sqlite-log-summary
.venv/bin/techno-search sqlite-log-integrity-summary
.venv/bin/techno-search sqlite-recent-runs
.venv/bin/techno-search sqlite-needs-follow-up
.venv/bin/techno-search sqlite-log-export
.venv/bin/techno-search sqlite-migration-summary
.venv/bin/techno-search sqlite-log-pragmas
.venv/bin/techno-search sqlite-log-backup
.venv/bin/techno-search sqlite-log-retention-summary
.venv/bin/techno-search sqlite-log-vacuum
.venv/bin/techno-search sqlite-log-commit-guard
.venv/bin/techno-search sqlite-log-consistency-summary
.venv/bin/techno-search validate-sqlite-logs
```

The local append-only runner is invoked explicitly:

```bash
.venv/bin/techno-search background-run-once \
  --ledger-path artifacts/background_search_ledger.json \
  --reviewed-log-path artifacts/background_reviewed_log.json \
  --needs-follow-up-log-path artifacts/background_needs_follow_up_log.json \
  --sqlite-log-path logs/techno_search.sqlite3 \
  --run-id background-local-demo \
  --code-commit "$(git rev-parse --short HEAD)" \
  --acknowledge-local-run
```

This runner selects the top ranked fixture target after review-history adjustment, records one ledger entry, appends exactly one reviewed or needs-follow-up outcome entry, and mirrors that run into SQLite when `--sqlite-log-path` is supplied. Needs-follow-up entries require provenance, false-positive class, cross-source consistency, calibration confidence, reproducibility, and human-review checklist tests before a report can be treated as ready. It is a scheduler-friendly local workflow, not a production autonomous search daemon.

Follow-up test records currently answer whether each mandatory test is `pass`, `ready`, `uncertain`, or `blocked`. Report-readiness records then determine whether a conservative draft report may be prepared or whether the item should request more tests. Draft report summaries are internal review artifacts only. Submission recommendations are ranked, but `external_submission_allowed` remains `false`; the user must explicitly approve any external action, and user-decision records preserve that approval gate.

Scheduler templates live under `docs/templates/background-search.cron` and `docs/templates/background-search.launchd.plist`. Both examples write JSON compatibility logs to ignored `artifacts/` paths, mirror operational state into `logs/techno_search.sqlite3`, call the single-run command, and do not enable live provider access. Use `techno-search scheduler-dry-run --artifact-dir artifacts/background_scheduler_dry_run` to smoke-test the same local path before installing a scheduler entry.

Candidate-extraction handoff records are the next local contract after a target has been selected. A handoff may be ready for extraction, blocked, expected to produce no candidate packet, or scheduling-only. A ready handoff still does not claim a detection. It only means the local fixture inputs are present and can be routed into the normal candidate scoring and reporting workflow.

Before any future passive runner is treated as operational, it must:

| Requirement | Guardrail |
|-------------|-----------|
| Use explicit opt-in execution | No surprise network or long-running searches |
| Record every target searched | Negative results remain auditable |
| Preserve provider/cache provenance | Queries can be reproduced or challenged |
| Keep candidate scoring separate from target scheduling | A high target priority is not a candidate claim |
| Surface blocking issues | Missing metadata must not disappear into a summary score |
| Route outputs through review packets | Human review sees positive and negative evidence |

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

The GitHub Actions template lives at `docs/templates/ci.yml` until the
publishing token has GitHub `workflow` scope. It mirrors the local validation
gate, keeps `TECHNO_SEARCH_ENABLE_LIVE_DATA=0`, and also runs
`techno-search validate-all` plus `techno-search health`.

Scientific quality gates:

- Default tests must be deterministic and non-networked.
- Live-provider tests must be opt-in and marked separately.
- Candidate reports must include positive evidence, negative evidence, blocking issues, and provenance.
- Report language must remain conservative.
- Score changes must be checked against score-regression fixtures.
- Calibration summaries are synthetic development diagnostics, not survey-performance claims.

### Quality-Control Matrix

| Risk | Guardrail | Validation Artifact |
|------|-----------|---------------------|
| Overclaiming | Required disclaimer and conservative language checks | Report validators and docs tests |
| RFI or artifact leakage | False-positive fixtures by track and class | Calibration false-positive suite |
| Schema drift | Versioned JSON schemas and schema path checks | `schema-paths`, schema tests |
| Score instability | Golden score regression snapshots | `score-regression-summary` |
| Hidden data dependency | Synthetic fixtures and mocked services by default | `pytest`, live-data opt-in guards |
| Invalid real-file input | Structural validation before pipeline scoring | `validate-input`, `run-pipeline` |
| Unreviewed RFI screening | RFI database records require ranges, provenance, review status, and synthetic-vs-real labeling | `rfi-database-summary` |
| Premature real RFI source admission | Proposed RFI source lists require admission records with zero real-data authorization by default | `rfi-database-admission-summary` |
| Premature real labeled dataset admission | Proposed curated validation datasets require provenance, licensing, labeling-method, false-positive-baseline, and review gates | `curated-dataset-admission-summary` |
| Stale readiness metadata | Production-readiness milestone, schema-count, decision, and authorization metadata must match validation gates | `project-status-consistency-summary` |
| Hidden production blocker drift | Tier 1 production blockers, admission blockers, operations readiness blockers, and disabled authorization counts must remain aligned | `production-blocker-consistency-summary` |
| Alert/QC review drift | Open-alert, alert-resolution, QC, readiness, and authorization blocker visibility must remain aligned | `operations-alert-review-consistency-summary` |
| Action-resolution staleness drift | Stale resolution records, current action-plan IDs, residual blockers, and disabled authorization counts must remain aligned | `operations-action-resolution-consistency-summary` |
| Blocker-progress chain drift | Blocker-detail, review, follow-up, progress, next-action, execution, execution-review, execution-follow-up, residual blockers, and disabled authorization counts must remain aligned | `operations-blocker-progress-consistency-summary` |
| SQLite log health drift | Top-level SQLite log health, migration state, run/outcome alignment, retention, PRAGMAs, commit guard, and disabled authorization counts must remain aligned | `sqlite-log-consistency-summary` |
| Lost provenance | Manifest and provenance summary validation | Report manifests and provenance summary CLI |
| Misleading calibration | Synthetic-only disclaimers on reliability and PR summaries | Validation summary commands |
| Premature non-synthetic calibration | Readiness review before curated dataset promotion | `validation-readiness-summary` |
| Benchmark drift | Append-only local benchmark run results and repeated-run comparison | `benchmark-run-append`, `benchmark-run-compare` |
| Unreviewed background automation | Reviewed workflow summary for scheduling-only and negative-result ledger entries | `background-reviewed-workflow-summary` |
| Premature candidate extraction | Local handoff contract before target selection becomes candidate packet generation | `candidate-extraction-handoff-summary` |
| Real-data workflow before operations readiness | Local readiness dashboard surfaces QC, alert, review, route, provenance, and SQLite blockers | `operations-readiness-summary` |
| Readiness blockers lack owner actions | Local action plan turns blockers into prioritized operator tasks | `operations-action-plan-summary` |
| Action-plan items lack resolution provenance | Local resolution records cover every current action-plan ID while tracking open, acknowledged, deferred, and resolved operator status without clearing blockers | `operations-action-resolution-summary` |
| Action-plan blockers lack source evidence | Local blocker-detail summary expands each current action into fixture-backed records without clearing blockers | `operations-blocker-detail-summary` |
| Blocker-detail evidence lacks review provenance | Local blocker-review records cover current action IDs and evidence counts while preserving residual blockers | `operations-blocker-review-summary` |
| Reviewed blockers lack local next-action ordering | Local blocker-followup summary derives operator attention, remediation, real-data hold, and verification actions without clearing blockers | `operations-blocker-followup-summary` |
| Follow-up actions lack progress provenance | Local blocker-followup progress records track progress notes, residual blockers, and recommendation consistency without clearing blockers | `operations-blocker-followup-progress-summary` |
| Unresolved progress lacks second-pass review | Local blocker progress-review records cover unresolved progress only while preserving verified-local closures and disabled authorization gates | `operations-blocker-progress-review-summary` |
| Unresolved progress reviews lack ordered local work | Local blocker progress next-action records order unresolved review items without reopening verified-local closures or changing authorization gates | `operations-blocker-progress-next-actions-summary` |
| Ordered local work lacks execution notes | Local blocker progress-execution records track next-action execution notes without clearing blockers or changing authorization gates | `operations-blocker-progress-execution-summary` |
| Execution notes lack review provenance | Local blocker progress-execution review records review execution notes without clearing blockers or changing authorization gates | `operations-blocker-progress-execution-review-summary` |
| Execution reviews lack follow-up planning | Local blocker progress-execution follow-up records plan reviewed execution follow-up without clearing blockers or changing authorization gates | `operations-blocker-progress-execution-followup-summary` |
| CI drift or accidental live access | Template stays non-networked under `docs/templates/` until workflow-scope publishing is available | `docs/CI.md`, `docs/templates/ci.yml` |

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
