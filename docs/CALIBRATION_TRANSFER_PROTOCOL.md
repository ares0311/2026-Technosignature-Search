# Calibration Transfer Protocol

**Purpose:** How to recalibrate scoring thresholds when applying the pipeline
to a new telescope, frequency band, or instrument.

---

## Background

The scoring thresholds used in production were derived from real GBT noise
data (213 hits, 5 cadences, 5 targets, 2 epochs):

| Threshold | Value | Meaning |
|---|---|---|
| `noise_floor_snr` | 42.4 | Below this: `insufficient_evidence` |
| `follow_up_snr` | 54.8 | Above this: `human_review_queue` |
| `high_interest_snr` | 118.3 | Above this: `candidate_review_packet` |
| `max_rfi_like_drift_hz_s` | 5.21 | Drift rates above this are penalized |

These values are **GBT-specific**. They encode the noise floor, backend
sensitivity, and RFI environment of the Green Bank Telescope at the observed
frequencies. They do not transfer directly to:

- MeerKAT, Parkes, FAST, or other radio telescopes
- Different frequency bands (L-band vs S-band vs C-band thresholds differ)
- Different backends or integration times

---

## When Recalibration Is Required

Recalibrate before trusting pipeline scores for any of the following:

1. New telescope (different sensitivity, noise floor, beam shape)
2. New frequency band (different RFI environment, different SNR statistics)
3. New backend/spectrometer (different quantization, resolution, bandwidth)
4. Different integration time (SNR scales with sqrt(t))

Recalibration is **not** required when:
- Running more BL/GBT targets in the same frequency band (thresholds transfer)
- Re-running existing data with a new pipeline version (compare old vs new scores)

---

## Recalibration Steps

### Step 1 — Collect a noise reference corpus

Download ≥100 hit-table rows from known-blank sky or noise-only observations
on the new instrument. The hits must span the frequency band of interest.
Cadence observations (ABACAD or equivalent) are preferred so ON/OFF separation
is available.

Minimum corpus requirements:
- ≥3 independent pointing epochs
- ≥3 different targets (to sample the RFI environment)
- ≥50 OFF-target hits (to characterize the noise floor)

### Step 2 — Run the calibration script

```bash
git pull origin main
.venv/bin/techno-search run-calibration \
  --hits-dir data/new_instrument_hits/ \
  --output configs/scoring_new_instrument.json
```

The script computes:
- 10th percentile SNR of OFF-target hits → `noise_floor_snr`
- 70th percentile SNR of ON-target-only hits → `follow_up_snr`
- 90th percentile SNR of ON-target-only hits → `high_interest_snr`
- Maximum drift rate of confirmed RFI hits → `max_rfi_like_drift_hz_s`

### Step 3 — Gate checks

The calibration script will refuse to emit a config unless all gates pass:

- `calibration_ready: true`
- `n_hits >= 100`
- `n_cadences >= 3`
- `n_targets >= 3`
- `noise_floor_snr > 0`
- `follow_up_snr > noise_floor_snr`
- `high_interest_snr > follow_up_snr`

If any gate fails, the script reports the failure reason and stops.

### Step 4 — Independent method audit

Before using new thresholds in production scoring, a second operator must
independently re-run the calibration script from the same raw hit tables
and confirm that the derived thresholds match within 10%.

Record the audit result in the SQLite log:
```bash
.venv/bin/techno-search calibration-audit-record \
  --config configs/scoring_new_instrument.json \
  --auditor-id <operator_id> \
  --agreement-pct <value>
```

Production scoring is gated on `audit_confirmed: true` in the config.

### Step 5 — Update pipeline config reference

In `run_pipeline()` calls for the new instrument:
```python
run_pipeline(
    dat_file,
    track="radio",
    output_dir=output_dir,
    scoring_config_path="configs/scoring_new_instrument.json",
)
```

---

## Learned Model Transfer

The learned scoring model v1 (logistic regression, 99.19% 3-fold CV accuracy)
was trained on 124 HIP99427/GBT labels. It may not generalize to:

- Different telescopes (different feature distributions)
- Different signal types (narrowband-only training)
- Different frequency bands (different RFI classes)

Before applying the learned model to a new instrument, collect ≥30 labeled
examples from that instrument and run:

```bash
.venv/bin/techno-search eval-against-labels \
  --labels data/new_instrument_labels.json
```

If accuracy falls below 0.70, the model requires retraining on the new
instrument's label set before use in production scoring.

---

## Scientific Guardrails

- Calibrated thresholds are local scheduling aids, not detection thresholds.
- No threshold value constitutes evidence of a technosignature.
- `high_interest_snr` is not a "detection SNR" — it is a scheduling priority cutoff.
- Recalibration does not validate the scientific methodology; it adapts the
  engineering parameters to a new noise environment.
- Independent reproduction of thresholds is required before production use.

---

## Reference

- Current GBT calibration config: `configs/scoring_v0.json`
- Calibration gate implementation: `src/techno_search/scoring_calibration.py`
- DECISION-127: Calibrated scoring configuration from real GBT noise data
