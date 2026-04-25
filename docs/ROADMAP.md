# ROADMAP

## Project
Technosignature Search

## Strategy

Build a multi-modal technosignature candidate search platform.

Do not start with live large-scale data. Start with the shared scoring and pathway core using synthetic data, then build track-specific ingestion and search modules.

---

# Milestone 1 — Multi-Modal Scoring Core

## Goal

Create shared candidate scoring logic across radio, infrared, and archival anomaly tracks.

## Tasks

- [ ] Define typed candidate schemas
- [ ] Define shared posterior-style score outputs
- [ ] Define track-specific evidence fields
- [ ] Implement scoring model v0
- [ ] Implement pathway classifier
- [ ] Add synthetic unit tests
- [ ] Add scientific sanity tests

## Output

```text
candidate features → scoring engine → pathway recommendation
```

## Done When

- Clean synthetic radio candidate scores better than obvious RFI
- Clean synthetic infrared excess scores better than AGN/blended source
- Clean synthetic archival anomaly scores better than known artifact
- All tests pass

---

# Milestone 2 — Radio SETI Prototype

## Goal

Build the first radio candidate workflow.

## Tasks

- [ ] Add radio candidate schema
- [ ] Add support for parsing candidate-hit tables
- [ ] Add RFI-band overlap checks
- [ ] Add ON/OFF cadence checks
- [ ] Add waterfall plot placeholder/report interface
- [ ] Add synthetic radio injection tests

## Output

```text
radio hit table → RFI vetting → score → report
```

---

# Milestone 3 — Infrared Waste-Heat Prototype

## Goal

Build the first catalog-based infrared anomaly workflow.

## Tasks

- [ ] Add infrared candidate schema
- [ ] Add Gaia/WISE/2MASS feature schema
- [ ] Add SED/IR-excess feature logic
- [ ] Add source-confusion flags
- [ ] Add galaxy/AGN/dust/YSO rejection flags
- [ ] Add synthetic infrared tests

## Output

```text
catalog features → IR excess checks → score → report
```

---

# Milestone 4 — Archival / Catalog Anomaly Prototype

## Goal

Build the first vanishing/appearing source and catalog anomaly workflow.

## Tasks

- [ ] Add anomaly candidate schema
- [ ] Add cross-match confidence features
- [ ] Add proper-motion sanity checks
- [ ] Add survey-depth mismatch checks
- [ ] Add artifact flags
- [ ] Add synthetic anomaly tests

## Output

```text
cross-match features → artifact checks → score → report
```

---

# Milestone 5 — Reporting System

## Goal

Generate reproducible candidate reports.

## Tasks

- [ ] Markdown report generation
- [ ] JSON candidate packet
- [ ] Plots where available
- [ ] Positive evidence list
- [ ] Negative evidence list
- [ ] Blocking issues list
- [ ] Provenance block

## Done When

Each candidate can generate a review packet without claiming confirmation.

---

# Milestone 6 — Injection-Recovery

## Goal

Measure sensitivity and reliability.

## Tasks

- [ ] Radio synthetic signal injection
- [ ] Infrared synthetic excess injection
- [ ] Archival anomaly simulation
- [ ] Recovery curves
- [ ] False-alarm estimates

---

# Milestone 7 — Human Review Workflow

## Goal

Support citizen-science review.

## Tasks

- [ ] Candidate triage labels
- [ ] Review queue format
- [ ] Exportable review packets
- [ ] Reviewer notes
- [ ] Consensus labels

---

# Milestone 8 — Live Data Integrations

## Goal

Add real data ingestion behind tested abstractions.

## Tasks

- [ ] Breakthrough Listen style file ingestion
- [ ] Gaia/IRSA/VizieR query wrappers
- [ ] Catalog caching
- [ ] Provenance tracking
- [ ] Live integration tests marked separately

---

# Milestone 9 — Calibration

## Goal

Make scores empirically meaningful.

## Tasks

- [ ] Build validation datasets
- [ ] Reliability curves
- [ ] Precision-recall analysis
- [ ] False-positive class analysis
- [ ] Calibration by track

---

# Project-Level Decision Tree

```text
IF known object or known artifact:
    → known_object_annotation

ELIF strong candidate evidence AND low false-positive evidence:
    → candidate_review_packet

ELIF interesting but ambiguous:
    → human_review_queue

ELIF likely false positive:
    → do_not_submit_false_positive

ELSE:
    → github_reproducibility_only
```

---

# Development Principle

Build the candidate evaluation engine first. Add large data ingestion only after the scoring, testing, and reporting interfaces are stable.
