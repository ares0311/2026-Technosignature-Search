# Production Scan Guide

**Audience:** Citizen-science operator running a full anomaly scan from scratch.

**Goal:** Scan one or more data stores for undetected anomalies, produce a
ranked anomaly report, and hand off any compelling candidates to the review
workflow.

---

## Prerequisites

```bash
git pull origin main
.venv/bin/python -m pytest --tb=short -q   # must pass
.venv/bin/techno-search validate-all        # must return ok=True
```

If either fails, stop and fix before scanning.

---

## Step 1 — Choose your data store

| Data store | Track | Format | Download |
|---|---|---|---|
| BL GBT archive (more targets) | radio | turboSETI `.dat` | `scripts/download_bl_hits.sh` |
| Gaia DR3 | infrared | IRSA TAP CSV | Live query via `TECHNO_SEARCH_ENABLE_LIVE_DATA=1` |
| AllWISE (IRSA) | infrared | IRSA catalog CSV | Live query via `TECHNO_SEARCH_ENABLE_LIVE_DATA=1` |
| Custom turboSETI output | radio | `.dat` | Bring your own |

For a first production scan, **start with BL GBT targets** — the pipeline is
calibrated on GBT data and thresholds transfer directly.

---

## Step 2 — Download target data (BL/GBT path)

```bash
git pull origin main
caffeinate -i bash scripts/download_bl_hits.sh
```

This downloads hit tables for the configured target list into `data/bl_hits/`.
Each target gets a subdirectory with its `.dat` files.

To add more targets, edit `scripts/download_bl_hits.sh` and add the BL
archive URLs for your chosen targets. Verify checksums after download:

```bash
.venv/bin/techno-search validate-input data/bl_hits/<target>/<file>.dat --track radio
```

---

## Step 3 — Run the pipeline across all targets

```bash
git pull origin main
caffeinate -i bash scripts/run_production_scan.sh
```

This runs the local production scan gate sequence:

- `validate-all`
- `scan-summary`
- `cross-target-rfi-summary`
- `escalation-gate-check`
- `review-dashboard`
- `prod-write-outcomes`

Each run writes to a human-readable directory:

```text
results/scans/RUN-YYYY-MM-DD_HHMMSSZ-A7K4-prod-scan/
```

The random four-character token keeps run IDs short enough for humans while
making same-second runs distinct. Production run child records use matching
IDs, for example `NEG-YYYY-MM-DD_HHMMSSZ-A7K4-001` and
`FU-YYYY-MM-DD_HHMMSSZ-A7K4-001`.

---

## Step 4 — Review the anomaly ranking

```bash
git pull origin main
.venv/bin/techno-search prod-runs
.venv/bin/techno-search prod-show results/scans/RUN-YYYY-MM-DD_HHMMSSZ-A7K4-prod-scan
```

The run directory contains both compatibility files and run-prefixed files:

```text
RUN-YYYY-MM-DD_HHMMSSZ-A7K4-prod-scan_manifest.json
RUN-YYYY-MM-DD_HHMMSSZ-A7K4-prod-scan_scan_summary.json
RUN-YYYY-MM-DD_HHMMSSZ-A7K4-prod-scan_non_detections.json
RUN-YYYY-MM-DD_HHMMSSZ-A7K4-prod-scan_follow_ups.json
RUN-YYYY-MM-DD_HHMMSSZ-A7K4-prod-scan_review_dashboard.json
```

The scan summary lists candidates ranked by score. Columns:

- `rank` — score rank across all targets (1 = highest)
- `candidate_id` — unique identifier
- `target_name` — which star
- `frequency_hz` — signal frequency
- `snr` — signal-to-noise ratio
- `pathway` — local routing result, such as `human_review_queue` or `candidate_review_packet`

Focus on candidates where:

- `pathway == "candidate_review_packet"` AND
- `snr >= 42.4` (calibrated noise floor)
- cross-target RFI and escalation records do not block local review

---

## Step 5 — Review non-detections and follow-ups

```bash
git pull origin main
.venv/bin/techno-search prod-non-detections results/scans/RUN-YYYY-MM-DD_HHMMSSZ-A7K4-prod-scan
.venv/bin/techno-search prod-follow-ups results/scans/RUN-YYYY-MM-DD_HHMMSSZ-A7K4-prod-scan
```

The non-detection file records what was examined but did not enter a follow-up
pathway. This is not evidence of absence. It is an audit trail.

The follow-up file records candidates requiring local citizen-science review.
This is not a detection or discovery claim, and it does not authorize external
submission.

The run manifest keeps these guardrails machine-readable:

- `detection_claimed: false`
- `discovery_claimed: false`
- `expert_review_claimed: false`
- `external_validation_claimed: false`
- `external_submission_allowed: false`

---

## Step 6 — Check the review dashboard

```bash
git pull origin main
.venv/bin/techno-search review-dashboard
```

Exit code 1 means `needs_attention: true`. Review the dashboard output for:

- Open flags requiring resolution
- Overdue review deadlines
- Real-label accuracy gate status

---

## Step 7 — Escalation gate (if a compelling candidate is found)

If any candidate passes the escalation gate criteria:

```bash
git pull origin main
.venv/bin/techno-search escalation-gate-check results/scan_<date>/<candidate>.json
```

If `escalation_required: true`, the pipeline writes an escalation record with:
- Source data SHA-256 checksums (for independent reproduction)
- Pipeline config version and hash
- Step-by-step reproduction checklist
- `operator_cleared: false` (must be set manually after your review)
- `external_review_authorized: false` (never auto-set)

To clear the escalation gate after your own review:
```bash
git pull origin main
.venv/bin/techno-search operator-clear-escalation <escalation_id> \
  --operator-id <your_id> \
  --review-notes "Your observations here"
```

**Do not clear the gate without completing the reproduction checklist.**

---

## Step 8 — Archive the scan results

```bash
git pull origin main
git add results/scans/RUN-YYYY-MM-DD_HHMMSSZ-A7K4-prod-scan/*.json
git commit -m "Scan results $(date +%Y-%m-%d): <N> targets, <M> follow-up candidates"
git push -u origin claude/general-session-Bb2dZ
```

Scan results are committed to the feature branch and merged to `main` via PR,
giving a full audit trail of every scan.

---

## Step 9 — Long-term: automated weekly scan

Once the manual scan workflow is stable, the GitHub Actions workflow
`.github/workflows/weekly_scan.yml` can run Steps 3–5 automatically on a
weekly schedule. Results are committed to `results/` and a PR is opened for
operator review.

See `docs/SCAN_SCHEDULE.md` for configuration.

---

## Anomaly Triage Criteria

A candidate is worth deeper investigation if it meets **all** of:

1. `recommended_pathway == "candidate_review_packet"`
2. `snr >= 42.4` (calibrated noise floor for GBT)
3. `cross_target_rfi_flagged == false`
4. `off_target_presence_score == 0.0` (not seen in OFF pointings)
5. Present in ≥2 independent epochs of the same target
6. No SIMBAD match within positional tolerance (not a known object)

A candidate meeting all 6 criteria warrants the escalation gate check and
a second independent operator review.

---

## Scientific Guardrails (Non-Negotiable)

- No scan result constitutes a detection claim.
- No candidate report authorizes external submission.
- Pathway routing is a scheduling aid, not a scientific verdict.
- The pipeline does not claim to detect technosignatures.
- Any claim of interest beyond "warrants follow-up observation" requires
  independent reproduction, multi-epoch confirmation, and peer review.

---

## Reference

- Calibration transfer: `docs/CALIBRATION_TRANSFER_PROTOCOL.md`
- Pipeline spec: `docs/PIPELINE_SPEC.md`
- Scoring model: `docs/SCORING_MODEL.md`
- CLI commands: `docs/CLI_USAGE.md`
- Validation guide: `docs/VALIDATION.md`
