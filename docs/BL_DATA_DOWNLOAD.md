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

# 2. Download hit tables (tries BL server first, then fallbacks)
caffeinate -i bash scripts/download_bl_hits.sh

# 3. Run the pipeline on the downloaded data
caffeinate -i bash scripts/run_pipeline_on_bl_data.sh
```

The script tries three sources in order:
1. **BL GBT L-band survey** (real data, preferred) — `blpd0.ssl.berkeley.edu`
2. **turboSETI package test data** (real format, if installed) — from `.venv`
3. **Synthetic files** (pipeline testing only, does not close Tier 1 gap)

---

## Manual Download (If Script Fails)

### Option A — BL Open Data Server (HTTPS, follow redirects)

The BL L-band survey results are hosted at the SSL Berkeley data server.
**Always use HTTPS and `-L` to follow redirects:**

```bash
mkdir -p ~/technosignature-data/bl_hits
cd ~/technosignature-data/bl_hits

# Download 5 targets from the GBT L-band survey
for target in HIP99427 HIP17378 HIP45167 HIP65352 HIP74995; do
    curl -L --max-time 60 --retry 3 \
         -o "${target}_hits.dat" \
         "https://blpd0.ssl.berkeley.edu/L_band_table/${target}_hits.dat"
    size=$(wc -c < "${target}_hits.dat")
    echo "$target: $size bytes"
done
```

**Common problems:**
- **153 bytes or less** — the server redirected or returned an error page.
  Make sure you are using `https://` (not `http://`) and `-L` to follow redirects.
- **SSL certificate error** — your Python venv may need certifi:
  `.venv/bin/python -m pip install certifi`
- **Connection refused** — the BL server may be temporarily down. Try again
  in a few hours or use Option B.

### Option B — BL GitHub Test Data (via pip, no browser needed)

The turboSETI package ships with real-format `.dat` test fixtures.
After installing, they are available without importing the package:

```bash
# Install turboSETI (ignore pkg_resources error from blimpy)
.venv/bin/python -m pip install "setuptools>=68" turbo_seti

# Find .dat files in the installed package (bypasses blimpy import)
.venv/bin/python - <<'PYEOF'
import pathlib, shutil

venv_lib = pathlib.Path(".venv/lib")
dat_files = [
    f for f in venv_lib.rglob("*.dat")
    if "turbo_seti" in str(f).lower() or "blc" in f.name.lower()
]
print(f"Found {len(dat_files)} .dat file(s)")
dest_dir = pathlib.Path.home() / "technosignature-data/bl_hits"
dest_dir.mkdir(parents=True, exist_ok=True)
for f in dat_files:
    dst = dest_dir / f.name
    shutil.copy(f, dst)
    print(f"  Copied: {f.name}  ({dst.stat().st_size} bytes)")
PYEOF
```

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
# File should be > 500 bytes and contain header lines
wc -c ~/technosignature-data/bl_hits/*.dat
grep "# Source:" ~/technosignature-data/bl_hits/*.dat | head -5
```

If a file is < 200 bytes or contains HTML, the download was redirected or failed.

---

## pkg_resources Fix (Python 3.13)

If you installed `turbo_seti` and see `ModuleNotFoundError: No module named 'pkg_resources'`,
this is a Python 3.13 compatibility issue with `blimpy`. Fix:

```bash
.venv/bin/python -m pip install "setuptools>=68"
```

This provides `pkg_resources`. The techno-search pipeline itself does NOT use
`pkg_resources`; this only affects Option B above.

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

1. Run `caffeinate -i bash scripts/run_pipeline_on_bl_data.sh`
2. Review output reports in `~/technosignature-data/pipeline_out/`
3. Manually inspect any candidates with pathway `follow_up_target` or `human_review_queue`
4. For threshold calibration, see `docs/THRESHOLD_CALIBRATION.md`
5. See `docs/PRODUCTION_READINESS.md` for the next Tier 1 gap to address
