# Breakthrough Listen Open Data — Download Guide

This document explains how to obtain real turboSETI hit tables from the
Breakthrough Listen Open Data Release for use with the techno-search pipeline.

**Tier 1 gap:** Ingesting real observation data closes the highest-priority
production blocker. See `docs/PRODUCTION_READINESS.md`.

---

## What You Need

- **BL turboSETI hit tables** (`.dat` files) — pre-computed results from the
  turboSETI narrowband drift-rate search algorithm. These are small (KB–MB)
  and are the primary input to the radio scoring pipeline.
- **A reviewed provenance sidecar** (`<filename>.provenance.json`) — required
  before the production-path runner will process a hit table.
- **No credentials required** — the BL Open Data Release is publicly accessible.
- **No raw filterbank files** — raw `.fil` files are multi-GB per observation
  and are not needed for the current pipeline. Do not download them.

---

## Quick Setup (Scripted)

```bash
# Pull latest
git pull origin main

# 1. Create local data directories
bash scripts/setup_data_dirs.sh

# 2. Attempt a TLS-verified download
caffeinate -i bash scripts/download_bl_hits.sh

# 3. Audit classifications and approval state
.venv/bin/python scripts/audit_bl_observation_artifacts.py \
  ~/technosignature-data/bl_hits
```

The downloader probes the BL GBT L-band endpoint with TLS verification enabled.
It does not treat a successful download as human approval. Synthetic generation
is disabled by default and can be enabled only for format testing with
`TECHNO_ALLOW_SYNTHETIC_BL_FIXTURES=1`; synthetic output never closes Tier 1.

The pipeline runner remains blocked until Human Gate 1 in
`docs/REAL_OBSERVATION_INTAKE.md` is complete.

---

## Manual Download (If Script Fails)

### Option A — BL Open Data Server (HTTPS, follow redirects)

> **NOTE**: The `blpd0.ssl.berkeley.edu/L_band_table/` URL pattern was
> incorrect. `blpd0.ssl.berkeley.edu` is a redirect-only page and does not
> serve hit tables at that path. Use Options B–D below for real data access.
>
> If you already have `.dat` files from a prior BL download (e.g., from
> `~/technosignature-data/bl_hits/`), you can use them directly with the
> calibration scripts without re-downloading.

```bash
git pull origin main
# If you already have BL .dat files locally, copy them:
mkdir -p data/calibration_corpus
cp ~/technosignature-data/bl_hits/*.dat data/calibration_corpus/
# Then create provenance sidecars (see "After Downloading" below)
```

**Common problems:**
- **blpd0 returns JavaScript redirect** — the root URL is a web portal, not
  a data server. Use the BL Open Data Portal (Option C) to browse and download.
- **SSL certificate error** — your Python venv may need certifi:
  `.venv/bin/python -m pip install certifi`

### Option B — Human-Reviewed Archive Selection

Use the official BL archive to select a specific observation record, preserve
its exact URL and checksum, and complete Human Gate 1 before pipeline execution.
Package test fixtures and synthetic HDF5 files are format tests only.

### Option C — BL Open Data Portal (Browser)

Visit the BL Open Data portal and download hit tables manually:

1. Go to: `https://seti.berkeley.edu/listen/data.html`
2. Look for GBT L-band survey hit tables (`.dat` files)
3. Save to `~/technosignature-data/bl_hits/`

### Option D — Enriquez et al. 2017 Supplementary Data

The original BL GBT L-band survey paper (ApJ 849:104, 2017) provides
hit tables as supplementary material:

```
https://iopscience.iop.org/article/10.3847/1538-4357/aa8d1b
```

Click "Supplemental data" to find the machine-readable hit tables.

---

## Verifying a Valid Download

A real turboSETI `.dat` file looks like this:

```
# Source:HIP99427
# MJD: 59045.5
# RA: 301.898
# DEC: -44.432
# DELTAT:  18.25396
# DELTAF(Hz):  2.79397
#
# Top_Hit_#	Drift_Rate	SNR	Uncorrected_Frequency	Corrected_Frequency	Index	freq_start	freq_end	SEFD	Coarse_Channel_Width	Full_number_of_hits
1	-0.37253	15.8634	1420.417858	1420.417858	13	1420.417844	1420.417871	0.0	2.794	11
```

Quick validity check:
```bash
git pull origin main
# File should be > 500 bytes and contain header lines
wc -c ~/technosignature-data/bl_hits/*.dat
grep "# Source:" ~/technosignature-data/bl_hits/*.dat | head -5
```

If a file is < 200 bytes or contains HTML, the download was redirected or failed.

---

## pkg_resources Fix (Python 3.13)

If a direct `turbo_seti` import reports
`ModuleNotFoundError: No module named 'pkg_resources'`, install the project radio
extra. BLIMPY 2.1.4 still needs the compatibility API removed from newer
setuptools releases:

```bash
git pull origin main
.venv/bin/python -m pip install -e ".[radio]"
```

The radio extra pins a compatible setuptools range and the manifest-driven
cadence intake also installs a narrow runtime shim. The techno-search pipeline
itself does not use `pkg_resources`; this affects optional turboSETI processing
only.

---

## Data Policy

- BL Open Data is publicly released for scientific use
- Cite the relevant BL publications when using this data in research
- Do **not** commit raw `.dat` files to this repository — the data directory
  (`~/technosignature-data/`) is separate from the codebase
- Do **not** commit large binary files (filterbank `.fil`, HDF5 `.h5`)

---

## Selecting Good Sample Targets

For initial pipeline testing, prefer targets with:
- Multiple hits (SNR > 10)
- Known RFI bands (L-band: avoid 1420 MHz H-line ± 1 MHz, 1612 MHz OH maser)
- A mix of ON and OFF observations for RFI rejection testing

Good starting targets from the BL GBT L-band survey (Enriquez et al. 2017):
- `HIP99427` — bright K star, ~100 ly
- `HIP17378` — G-type star, ~36 ly
- `HIP45167` — nearby M dwarf

---

## Next Steps After Download

1. Complete Human Gate 1 in `docs/REAL_OBSERVATION_INTAKE.md`.
2. Create the reviewed provenance sidecar with the exact artifact checksum.
3. Run the guarded pipeline from an up-to-date local `main` checkout.
4. Review reports for negative evidence, blocking issues, and provenance.
5. Do not calibrate thresholds until real labels and site-specific RFI evidence
   are approved.
