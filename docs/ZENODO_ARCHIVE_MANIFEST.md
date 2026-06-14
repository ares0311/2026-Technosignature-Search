# Zenodo Archive Manifest

**Status:** Ready to generate. Upload requires human action (Zenodo account).

**Pipeline milestone:** 77 (Escalation Gate Hardening + External Submission Protocol)

**Scientific guardrail:** This archive is a reproducibility aid only. No entry constitutes
a detection claim, confirmed technosignature, or authorization to submit. No expert or peer
review has occurred.

---

## Purpose

This document defines the contents of the citizen-science reproducibility archive
intended for public deposit on [Zenodo](https://zenodo.org) (or equivalent indexed
repository). The archive satisfies P5 of `docs/EXTERNAL_SUBMISSION_PROTOCOL.md`:
**public reproducibility package posted** before any external submission contact.

As of 2026-06-14, no candidate has passed the escalation gate on real multi-epoch data.
This archive documents the methodology and calibration corpus. A candidate-specific
archive would be created separately when (if) P1–P4 of the external submission protocol
are satisfied.

---

## Generating the Manifest

```bash
git pull origin main

# Generate manifest with checksums (reads from repo + ~/technosignature-data/)
.venv/bin/python scripts/generate_zenodo_manifest.py

# Preview without writing
.venv/bin/python scripts/generate_zenodo_manifest.py --dry-run | jq '.summary'

# With explicit data directory
.venv/bin/python scripts/generate_zenodo_manifest.py \
  --data-dir ~/technosignature-data \
  --output results/zenodo_manifest.json
```

Output: `results/zenodo_manifest.json` (SHA-256 checksums for all files).

---

## Archive Contents

### 1 — Pipeline Source Code

| Path | Description |
|---|---|
| `src/techno_search/` | Full pipeline source (scoring, candidates, escalation, CLI) |
| `pyproject.toml` | Package metadata and dependencies |
| `schemas/` | 109 JSON Schema artifacts |
| `configs/` | Scoring and track configuration JSON |
| `README.md`, `CHANGELOG.md` | Project overview and version history |

### 2 — Calibration Data (Local — Not in Repository)

These files live on the operator's machine at `~/technosignature-data/` and must be
added manually to the Zenodo upload. They are small ASCII tables (not raw HDF5).

| File pattern | Description |
|---|---|
| `guppi_59046_HIP99427*.dat` | turboSETI hit table — HIP99427 (5 cadences, ON+OFF) |
| `guppi_59046_HIP100670*.dat` | turboSETI hit table — HIP100670 |
| `guppi_59046_HIP99560*.dat` | turboSETI hit table — HIP99560 |
| `guppi_59046_HIP99759*.dat` | turboSETI hit table — HIP99759 |
| `bl_turboSETI_test.dat` | Voyager 1 X-band calibration hit table |

SHA-256 checksums for all .dat files are computed by `generate_zenodo_manifest.py`
and stored in `results/zenodo_manifest.json`.

### 3 — Labeled Candidate Dataset

| Path | Description |
|---|---|
| `tests/fixtures/labeled_candidates.json` | 10 synthetic labeled candidates (v0) |
| `tests/fixtures/real_gbt_labeled_candidates.json` | 124 citizen-science labels from HIP99427 real GBT data |

### 4 — Calibration Fixtures

| Path | Description |
|---|---|
| `tests/fixtures/calibration_false_positives.json` | 15 false-positive class fixtures |
| `tests/fixtures/calibration_corpus_manifest.json` | Calibration corpus download manifest |
| `tests/fixtures/gbt_provisional_rfi_catalog.json` | 15-band GBT provisional RFI catalog |

### 5 — Key Documentation

| Path | Description |
|---|---|
| `docs/PRODUCTION_READINESS.md` | Current production readiness state |
| `docs/EXTERNAL_SUBMISSION_PROTOCOL.md` | 7-precondition external submission protocol |
| `docs/CALIBRATION_TRANSFER_PROTOCOL.md` | Recalibration instructions for new telescopes |
| `docs/PIPELINE_SPEC.md` | Pipeline specification |
| `docs/SCORING_MODEL.md` | Scoring model documentation |
| `docs/CITIZEN_SCIENCE_REVIEW.md` | Citizen-science review methodology |

### 6 — Pipeline Validation Output

Include a fresh `validate-all` run output at time of deposit:

```bash
.venv/bin/techno-search validate-all > results/validate_all_at_deposit.json
```

---

## What Is Excluded

| Category | Reason |
|---|---|
| Raw HDF5 files (`*.h5`) | Too large (50–200 MB each); referenced by SHA-256 in manifest |
| `.venv/` | Reconstructable from `pyproject.toml` |
| Local SQLite logs (`logs/*.db`) | Generated artifacts; not reproducibility evidence |
| `results/` (most) | Generated; reconstructable from source + hit tables |
| `.git/` | Repository history not required for reproducibility |

---

## Zenodo Deposit Metadata

```json
{
  "title": "2026 Technosignature Search — Citizen-Science Pipeline v0.77",
  "upload_type": "software",
  "access_right": "open",
  "license": "MIT",
  "keywords": [
    "SETI", "technosignature", "radio astronomy", "citizen science",
    "turboSETI", "Breakthrough Listen", "GBT", "pipeline", "calibration"
  ],
  "description": "Source code, schema artifacts, calibration fixtures, turboSETI hit tables, labeled candidate dataset, and provenance records for the 2026 Technosignature Search citizen-science pipeline. Calibrated against 213 real GBT hits from 5 cadences, 5 targets, 2 epochs. Scoring model v1 achieves 77.42% diagnostic agreement on 124 real HIP99427 citizen-science labels. Scientific guardrail: this archive is a reproducibility aid only. No entry constitutes a detection claim, confirmed technosignature, or authorization to submit. No expert or peer review has occurred.",
  "notes": "Milestone 77. All Tier 1 and Tier 2 production gaps closed. Expert review and peer review remain unclaimed."
}
```

---

## Upload Instructions (Human Action Required)

1. Generate the manifest with checksums:
   ```bash
   .venv/bin/python scripts/generate_zenodo_manifest.py \
     --data-dir ~/technosignature-data
   ```

2. Verify the summary:
   ```bash
   cat results/zenodo_manifest.json | python3 -m json.tool | grep -A5 '"summary"'
   ```

3. Log into [zenodo.org](https://zenodo.org) and create a new upload.

4. Upload files in order:
   - All repository files (zip the `src/`, `schemas/`, `configs/`, `docs/` trees)
   - `.dat` calibration files from `~/technosignature-data/`
   - `results/zenodo_manifest.json` (checksums)
   - `results/validate_all_at_deposit.json` (fresh validate-all output)

5. Use the Zenodo metadata above.

6. Publish the deposit and record the DOI here:

   **DOI:** *(pending)*

7. Add the required disclaimer to the deposit description:

   > "This is a citizen-science calibration and methodology archive. It has not been
   > peer reviewed and does not constitute a confirmed technosignature. Independent
   > scientific review has not occurred."

---

## Decision Reference

See `docs/DECISIONS.md` DECISION-132 for the external submission protocol and the
preconditions (P1–P7) that must all be satisfied before any external submission.
This archive satisfies P5 when uploaded.

---

## Scientific Guardrails (Permanent)

1. No file in this archive constitutes a confirmed technosignature.
2. No scoring result authorizes external submission.
3. This manifest may be updated; updates do not retroactively clear any P1–P6 gate.
4. The public reproducibility package (P5) enables independent reproduction; it is
   not independent scientific confirmation.
