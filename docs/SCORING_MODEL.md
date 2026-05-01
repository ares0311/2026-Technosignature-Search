# SCORING MODEL

## Project
Technosignature Search

## Status
Research-grade specification v0.1

---

# 1. Purpose

This document defines the scoring framework for multi-modal technosignature-interest candidates.

The scoring system should:

- rank candidate signals and anomalies by credibility
- separate candidate evidence from false-positive evidence
- quantify uncertainty
- support conservative pathway classification
- produce human-readable explanations
- work across radio, infrared, and archival anomaly tracks

The model must never label a candidate as a confirmed technosignature.

---

# 2. Core Philosophy

Most apparent technosignature-like signals are likely false positives.

The scoring engine should therefore ask:

1. Is the signal or anomaly real?
2. Is it unusual after known natural and instrumental explanations?
3. Which false-positive explanation is most plausible?
4. Is it worth human review or follow-up?
5. What pathway is appropriate?

---

# 3. Shared Scoring Framework

For each candidate, evaluate multiple hypotheses.

Conceptual form:

```text
P(H_i | D) = P(D | H_i) P(H_i) / Σ_j P(D | H_j) P(H_j)
```

Early implementation should use interpretable log-score approximations:

```text
log_score_i = log_prior_i + weighted_evidence_i
posterior_i = softmax(log_score_i)
```

---

# 4. Shared Output Fields

Every candidate should output:

```json
{
  "posterior": {
    "technosignature_interest": 0.0,
    "natural_source": 0.0,
    "human_interference": 0.0,
    "instrumental_artifact": 0.0,
    "catalog_or_processing_error": 0.0,
    "known_object": 0.0,
    "noise_or_low_confidence": 0.0
  },
  "scores": {
    "false_positive_probability": 0.0,
    "signal_reality_confidence": 0.0,
    "novelty_score": 0.0,
    "followup_value": 0.0,
    "review_readiness": 0.0
  }
}
```

The false-positive probability is:

```text
false_positive_probability = 1 - posterior.technosignature_interest
```

unless the candidate is a known object, in which case it should be treated as catalog annotation rather than a new candidate.

---

# 5. Radio Candidate Hypotheses

## H_radio_technosignature_interest

Evidence supporting:

- narrowband signal
- nonzero Doppler drift
- present in ON-target scans
- absent in OFF-target scans
- not persistent across unrelated targets
- not in known RFI bands
- repeatable or follow-up worthy
- recovered under synthetic injection tests

## H_human_RFI

Evidence supporting:

- appears in OFF-target scans
- appears across many sky positions
- occurs in known RFI bands
- zero or suspiciously stable drift
- repeated local frequency persistence
- known satellite/aircraft band overlap

## H_instrumental_artifact

Evidence supporting:

- band-edge artifact
- digitization pattern
- gain instability
- broadband impulsive behavior
- repeated instrument pattern
- observation metadata anomaly

## H_noise_or_low_confidence

Evidence supporting:

- low SNR
- single weak hit
- no repeatability
- poor data quality
- insufficient metadata

---

# 6. Infrared Candidate Hypotheses

## H_waste_heat_interest

Evidence supporting:

- significant mid-infrared excess
- stellar-like Gaia solution
- plausible parallax/proper motion
- clean photometry
- no obvious galaxy/AGN/dust explanation
- not blended or confused
- SED not fit well by normal stellar model alone

## H_dust_or_natural_astrophysics

Evidence supporting:

- young stellar object indicators
- debris disk explanation
- AGB-like colors
- star-forming region context
- known dusty source class

## H_galaxy_or_AGN

Evidence supporting:

- extended morphology
- extragalactic catalog match
- AGN-like colors
- weak or absent stellar parallax/proper motion
- inconsistent Gaia solution

## H_blended_or_confused_source

Evidence supporting:

- crowded field
- nearby bright source
- poor WISE image quality
- inconsistent cross-match
- large photometric uncertainties

## H_catalog_artifact

Evidence supporting:

- bad flags
- saturation
- inconsistent epochs
- impossible colors
- duplicate or unreliable source association

---

# 7. Archival / Catalog Anomaly Hypotheses

## H_true_archival_anomaly_interest

Evidence supporting:

- strong historical detection
- strong modern non-detection or major change
- no proper-motion explanation
- no survey-depth explanation
- no artifact flags
- consistent source context

## H_plate_or_image_artifact

Evidence supporting:

- plate defect
- saturation
- diffraction spike
- cosmic ray
- edge artifact
- poor image quality

## H_moving_object

Evidence supporting:

- Solar System object possibility
- motion between epochs
- known minor planet overlap
- inconsistent stationary source behavior

## H_high_proper_motion_star

Evidence supporting:

- plausible proper-motion displacement
- modern counterpart offset along expected motion vector

## H_survey_depth_or_bandpass_effect

Evidence supporting:

- historical survey deeper than modern survey or vice versa
- strong color dependence
- bandpass mismatch
- local background difference

## H_catalog_mismatch

Evidence supporting:

- ambiguous cross-match
- nearby multiple counterparts
- coordinate uncertainty
- duplicate source associations

---

# 8. Derived Scores

## signal_reality_confidence

Measures whether the signal/anomaly is real independent of interpretation.

## novelty_score

Measures whether the candidate is not already known or trivially explained.

## followup_value

Measures whether the candidate deserves further human or observational attention.

## review_readiness

Measures whether the candidate has enough supporting material for external or community review.

---

# 9. Pathway-Aware Thresholds

The scoring engine should support conservative pathway classification.

Suggested initial thresholds:

```text
candidate_review_packet:
    technosignature_interest >= 0.60
    false_positive_probability <= 0.40
    signal_reality_confidence >= 0.70
    review_readiness >= 0.70

human_review_queue:
    signal_reality_confidence >= 0.40
    false_positive_probability < 0.80

github_reproducibility_only:
    weak, ambiguous, incomplete, or exploratory result

known_object_annotation:
    known_object probability >= 0.80

do_not_submit_false_positive:
    false_positive_probability >= 0.80
```

These thresholds are starting points and must be calibrated.

---

# 10. Explanation Requirements

Every candidate must include:

```json
{
  "positive_evidence": [],
  "negative_evidence": [],
  "blocking_issues": []
}
```

Example radio explanation:

```json
{
  "positive_evidence": [
    "Signal appears in ON-target scan",
    "Signal has nonzero drift rate",
    "Signal is narrowband"
  ],
  "negative_evidence": [
    "Frequency overlaps known RFI region",
    "No repeat observation available"
  ],
  "blocking_issues": [
    "OFF-target scans unavailable"
  ]
}
```

---

# 11. Calibration Plan

Initial scores are not scientifically calibrated.

Calibration should eventually use:

- synthetic injection and recovery
- known RFI examples
- known catalog artifacts
- known infrared contaminants
- known archival false positives
- human-reviewed labels

Evaluate:

- reliability curves
- precision-recall
- false-positive class confusion
- score stability by track
- sensitivity by signal strength

---

# 12. Immediate Implementation Target

First implementation should support synthetic examples only.

Inputs:

- radio candidate feature object
- infrared candidate feature object
- archival anomaly feature object

Outputs:

- posterior-style probabilities
- false-positive probability
- recommended pathway
- explanation

No live data required for v0.

---

# 13. Future AI Research Direction

After the v0 interpretable scoring model, reporting system, injection-recovery tests, and calibration datasets exist, the project should evaluate modern AI methods for candidate triage and feature extraction.

Potential future approaches include:

- CNNs for radio waterfalls, survey cutouts, artifact morphology, and image-like diagnostic products
- Transformers for time series, multi-epoch catalog histories, candidate evidence packets, and cross-track context
- Self-supervised, contrastive, or multimodal representation learning for large unlabeled astronomical datasets
- Hybrid systems that combine learned embeddings with explicit scientific features, provenance, and false-positive evidence

Any learned model must remain conservative and auditable. It should expose uncertainty, be calibrated on known contaminants and synthetic injections, preserve negative evidence, and feed into the pathway system rather than bypassing it.
