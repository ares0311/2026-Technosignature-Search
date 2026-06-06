# Breakthrough Listen Open Data — Download Guide

This document explains how to obtain real turboSETI hit tables from the
Breakthrough Listen Open Data Release for use with the techno-search pipeline.

---

## What You Need

- **BL turboSETI hit tables** (`.dat` files) — pre-computed results from the
  turboSETI narrowband drift-rate search algorithm. These are small (KB–MB)
  and are the primary input to the radio scoring pipeline.
- **No credentials required** — the BL Open Data Release is publicly accessible.
- **No raw filterbank files** — raw `.fil` files are multi-GB per observation
  and are not needed for the current pipeline. Do not download them.

---

## Quick Setup (Scripted)

```bash
# 1. Create local data directories
bash scripts/setup_data_dirs.sh

# 2. Download sample hit tables
bash scripts/download_bl_hits.sh

# 3. Run the pipeline on the downloaded data
bash scripts/run_pipeline_on_bl_data.sh
```

All data goes into `~/technosignature-data/` (or `$TECHNO_DATA_DIR` if set).

---

## Manual Download

### Option A — BL HTTPS Data Archive

The BL L-band GBT survey results are hosted at:

```
http://blpd0.ssl.berkeley.edu/L_band_table/
```

Browse the directory listing. Download `.dat` files (not `.fil` or `.h5` files):

```bash
# Example: single target
curl -O http://blpd0.ssl.berkeley.edu/L_band_table/HIP99427_hits.dat

# Save to your data directory
curl -o ~/technosignature-data/bl_hits/HIP99427_hits.dat \
     http://blpd0.ssl.berkeley.edu/L_band_table/HIP99427_hits.dat
```

### Option B — BL GitHub Samples

A small set of example turboSETI outputs is available at:

```
https://github.com/UCBerkeleySETI/turbo_seti/tree/master/tests/test_data
```

These are valid `.dat` files suitable for testing the pipeline.

### Option C — Generate from Raw Data (Advanced)

If you have access to filterbank files:

```bash
pip install turbo_seti
turboSETI your_filterbank.fil -M 4 -s 10 -o ~/technosignature-data/bl_hits/
```

This is only needed if you have raw telescope data. For initial pipeline
testing, use Option A or B.

---

## File Format

Real turboSETI `.dat` files look like this:

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

Key notes:
- **Tab-separated** (not comma-separated)
- Metadata lines start with `# Key: value`
- The column header line starts with `# Top_Hit_#`
- Frequency column is `Corrected_Frequency` (MHz)
- The pipeline reader handles this format automatically

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

Good starting targets from the BL GBT L-band survey:
- `HIP99427` — bright K star, 100 ly
- `HIP17378` — G-type star, ~36 ly
- `HIP45167` — nearby M dwarf

---

## Next Steps After Download

1. Run `bash scripts/run_pipeline_on_bl_data.sh`
2. Review output reports in `~/technosignature-data/pipeline_out/`
3. Manually inspect any candidates with pathway `follow_up_target` or `human_review_queue`
4. See `docs/PRODUCTION_READINESS.md` for the next Tier 1 gap to address
