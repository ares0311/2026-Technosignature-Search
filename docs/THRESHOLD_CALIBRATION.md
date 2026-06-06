# Scoring Threshold Calibration Guide

This document explains how to derive and commit calibrated scoring thresholds
from real Breakthrough Listen hit table data (Tier 1 gap: Calibrated scoring
thresholds).

---

## Status

Current scoring config: `configs/scoring_v0.json` — synthetic defaults.  
v1 template: `configs/scoring_v1_template.json` — **requires real data + expert review**.

---

## Step 1 — Download Real Hit Tables

```bash
bash scripts/setup_data_dirs.sh
bash scripts/download_bl_hits.sh
```

Verify files are present:

```bash
ls ~/technosignature-data/bl_hits/*.dat
```

Aim for at least 10–20 `.dat` files covering multiple targets and epochs.

---

## Step 2 — Run Noise Distribution Analysis

```bash
.venv/bin/techno-search noise-threshold-calibration ~/technosignature-data/bl_hits/ \
  > ~/technosignature-data/noise_samples/noise_calibration_$(date +%Y%m%d).json
```

Review the output JSON:

```json
{
  "snr_stats": {
    "percentiles": {
      "p90": 12.3,
      "p95": 18.7,
      "p99": 45.1
    }
  },
  "suggested_thresholds": {
    "snr_noise_floor_estimate": 12.3,
    "snr_follow_up_candidate": 18.7,
    "snr_high_interest_candidate": 45.1,
    "drift_rate_abs_p95_hz_s": 0.8
  }
}
```

---

## Step 3 — Expert Review

Before filling in `scoring_v1_template.json`, a domain expert must:

1. Verify the SNR distribution is consistent with expected GBT sensitivity
   (typical GBT L-band noise floor: SNR 10–25 for real RFI and narrowband hits)
2. Confirm the p90/p95/p99 values are not dominated by RFI contamination
3. Compare against published BL survey sensitivity estimates
   (see Enriquez et al. 2017, ApJ 849:104)
4. Verify the drift rate p95 is consistent with expected Doppler drift for
   real technosignature candidates (< ±4 Hz/s for stellar targets at GBT)

---

## Step 4 — Fill In `scoring_v1_template.json`

Replace all `"FILL_FROM_*"` placeholders with actual values from Step 2:

```json
{
  "pathway_thresholds": {
    "minimum_signal_reality_for_review": 12.3,
    "candidate_interest_probability": 18.7,
    "candidate_signal_reality": 45.1
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
  "reviewed_by": "your-name",
  "review_date": "2026-06-XX"
}
```

---

## Step 5 — Commit as `scoring_v1.json`

After expert review and approval:

```bash
cp configs/scoring_v1_template.json configs/scoring_v1.json
# Edit to fill in all FILL_FROM_* values and set review_status: "approved"
git add configs/scoring_v1.json
git commit -m "Add calibrated scoring thresholds v1 from real BL noise analysis (Tier 1: Calibrated thresholds)"
```

---

## Step 6 — Update Pipeline to Use v1

```bash
# In configs/scoring_v0.json, update the description to note it's superseded
# Then set the active scoring config reference in pipeline code
```

Currently the pipeline defaults to `scoring_v0.json`. Once `scoring_v1.json`
is approved, update `src/techno_search/scoring_config.py` to load it.

---

## Scientific Guardrail

Derived thresholds are calibration aids only.  They do not:
- Constitute calibrated survey sensitivity estimates
- Guarantee detection of real technosignature candidates
- Replace human expert judgment for candidate review
- Authorize external submission of any candidate report
