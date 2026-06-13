# Automated Scan Schedule

The weekly anomaly scan runs automatically via GitHub Actions every Sunday
at 02:00 UTC when hit table data is present in `data/bl_hits/`.

## Configuration

Workflow file: `.github/workflows/weekly_scan.yml`

The scan requires:
- `data/bl_hits/<target>/` — one subdirectory per target, each containing
  at least one turboSETI `.dat` file
- `validate-all` passing at scan time (scan aborts if validation fails)

## Manual trigger

```bash
# Via GitHub Actions UI: Actions → Weekly Anomaly Scan → Run workflow
# Or via gh CLI:
gh workflow run weekly_scan.yml
```

## What the scan does

1. Runs `validate-all` — scan aborts if any gate fails
2. Runs `review-dashboard` — logs status but does not abort
3. Runs `scan-summary` across all targets in `data/bl_hits/`
4. Applies cross-target RFI suppression (signals at the same frequency
   in ≥2 targets are flagged as likely terrestrial)
5. Checks the escalation gate on any `candidate_review_packet` results
6. Commits `results/scans/<date>/` to main and posts summary to the
   GitHub Actions job summary

## Scan results location

```
results/scans/
  YYYYMMDD/
    scan_summary.json    # ranked anomaly list
    scan_summary.txt     # human-readable log
```

Each entry in `scan_summary.json` includes:
- `rank` — score rank (1 = highest interest)
- `candidate_id`
- `target_name`
- `frequency_hz`
- `snr`
- `recommended_pathway`
- `cross_target_rfi_flagged`

## Escalation

If any candidate scores `candidate_review_packet` with `snr >= 42.4` and
`cross_target_rfi_flagged == false`, the escalation gate check writes a
record with a step-by-step reproduction checklist.  The operator must
manually clear `operator_cleared` before any further action.

No scan result authorizes external submission or constitutes a detection claim.

## Adding targets

To add new BL/GBT targets to the automated scan:

1. Add the target's turboSETI `.dat` file(s) to `data/bl_hits/<target_name>/`
2. Verify with `techno-search validate-input data/bl_hits/<target_name>/<file>.dat --track radio`
3. Commit `data/bl_hits/<target_name>/` to the repository (`.dat` files are
   small ASCII hit tables, not the raw H5 observation data)
4. The next weekly scan will include the new target automatically

## Scientific guardrails

- No scheduled scan result constitutes a detection claim.
- No candidate report authorizes external submission.
- The scan is a local triage tool. Any interesting candidate requires
  independent reproduction before any claim of scientific interest.
