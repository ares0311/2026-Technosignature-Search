# Scoring Threshold Calibration Guide

This document explains how to derive and commit calibrated scoring thresholds
from real Breakthrough Listen hit table data (Tier 1 gap: Calibrated scoring
thresholds).

---

## Status

Current scoring config: `configs/scoring_v0.json` — synthetic defaults.  
v1 template: `configs/scoring_v1_template.json` — **requires multiple real
cadences plus citizen-science reproducibility review**.

The production command is provenance-aware and fail-closed. It accepts only
checksum-matching real observation artifacts with approved data-use,
provenance, and local-use reviews. Synthetic, invalid, unapproved, and tampered
artifacts are excluded. A derived cadence CSV is also excluded when any of its
source `.dat` files are selected, preventing duplicate rows.

---

## Step 1 — Download Real Hit Tables

```bash
git pull origin main
caffeinate -i bash scripts/setup_data_dirs.sh
caffeinate -i bash scripts/download_bl_hits.sh
```

Verify files are present:

```bash
git pull origin main
ls ~/technosignature-data/bl_hits/*.dat
```

Aim for at least 10–20 `.dat` files covering multiple targets and epochs.

---

## Step 2 — Run Noise Distribution Analysis

```bash
git pull origin main
caffeinate -i .venv/bin/techno-search noise-threshold-calibration ~/technosignature-data/bl_hits/ \
  > ~/technosignature-data/noise_samples/noise_calibration_$(date +%Y%m%d).json
```

Review the output JSON:

```json
{
  "calibration_ready": false,
  "snr_stats": {
    "percentiles": {
      "p90": 12.3,
      "p95": 18.7,
      "p99": 45.1
    }
  },
  "suggested_thresholds": {
    "snr_thresholds": {
      "noise_floor_snr": 12.3,
      "follow_up_snr": 18.7,
      "high_interest_snr": 45.1
    },
    "drift_rate_thresholds": {
      "max_rfi_like_drift_hz_s": 0.8
    },
    "pathway_probability_thresholds": {
      "status": "not_derived_by_noise_distribution"
    }
  }
}
```

Do not promote the suggested values unless `calibration_ready` is `true`.
The acceptance report requires:

- at least 3 independent cadences;
- at least 3 targets and 2 observing epochs;
- at least 100 admitted hits;
- no cadence contributing more than 50% of admitted hits;
- fixed-seed bootstrap relative span no greater than 50%;
- leave-one-cadence-out relative threshold shift no greater than 25%.

These are minimum admission gates, not evidence of a detection or calibrated
survey sensitivity.

---

## Step 3 — Citizen-Science Reproducibility Review

Before filling in `scoring_v1_template.json`, the project must:

1. Generate percentiles with the production calibration command.
2. Independently recompute the same percentiles from the admitted source rows
   without calling the production percentile helper.
3. Reconcile any disagreement before approval; unresolved disagreement blocks
   threshold promotion.
4. Check whether a small number of RFI-heavy files dominate p90/p95/p99.
5. Compare the interpretation against primary Breakthrough Listen literature
   and record exact citations and any mismatch.
6. Preserve the reviewed source-file hashes, cadence IDs, method versions,
   reviewer identity, date, and abstentions in the calibration artifact.

---

## Step 4 — Fill Physical-Unit Thresholds

After every acceptance gate and the independent-method review pass, fill only
the SNR and drift-rate sections:

```json
{
  "pathway_thresholds": {
    "minimum_signal_reality_for_review": 0.4,
    "candidate_interest_probability": 0.6,
    "candidate_signal_reality": 0.7
  },
  "snr_thresholds": {
    "noise_floor_snr": 12.3,
    "follow_up_snr": 18.7,
    "high_interest_snr": 45.1
  },
  "drift_rate_thresholds": {
    "max_rfi_like_drift_hz_s": 0.8
  },
  "review_status": "approved",
  "reviewed_by": "citizen-reviewer-id",
  "review_date": "2026-06-XX"
}
```

Every `pathway_thresholds` value is a dimensionless probability in `[0, 1]`.
Never place SNR or drift-rate values in those fields. Changing pathway
probabilities requires a separate evaluation against admitted real labels.

---

## Step 5 — Commit as `scoring_v1.json`

After the reproducibility review passes:

```bash
git pull origin main
cp configs/scoring_v1_template.json configs/scoring_v1.json
```

Fill the physical-unit values, preserve the separately reviewed probability
values, and set `review_status` to `approved`. The change must then follow the
repository feature-branch and pull-request workflow.

---

## Step 6 — Update Pipeline to Use v1

```bash
# In configs/scoring_v0.json, update the description to note it's superseded
# Then set the active scoring config reference in pipeline code
```

Currently the pipeline defaults to `scoring_v0.json`. Once `scoring_v1.json`
is approved, update the active scoring configuration reference.

---

## Current Preflight Result

The admitted HIP99427 corpus contains 6 source `.dat` files, 213 hits, 4
targets, 1 cadence, and 1 epoch. The derived cadence CSV is correctly excluded.
It is not calibration-ready because cadence count, epoch count, cadence
dominance, bootstrap stability, and leave-one-cadence-out gates do not pass.
Additional approved GBT cadences from other epochs are required.

---

## Scientific Guardrail

Derived thresholds are calibration aids only.  They do not:
- Constitute calibrated survey sensitivity estimates
- Guarantee detection of real technosignature candidates
- Replace independent reproduction or conservative candidate review
- Authorize external submission of any candidate report
