#!/usr/bin/env bash
# download_bl_hits.sh — download real turboSETI hit tables for pipeline testing
#
# Tries sources in order:
#   1. BL GBT L-band survey open data (blpd0.ssl.berkeley.edu)
#   2. turboSETI GitHub test fixtures via git-lfs (real-format .dat files)
#   3. Synthetic .dat files (pipeline format testing only — does NOT close Tier 1 gap)
#
# Run (macOS — use caffeinate to prevent sleep):
#   caffeinate -i bash scripts/download_bl_hits.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_ROOT="${TECHNO_DATA_DIR:-$HOME/technosignature-data}"
BL_HITS_DIR="$DATA_ROOT/bl_hits"
VENV_PYTHON="$REPO_ROOT/.venv/bin/python"

mkdir -p "$BL_HITS_DIR"

echo "=== BL Hit Table Download ==="
echo "Output directory: $BL_HITS_DIR"
echo ""

# -----------------------------------------------------------------------
# Helper: check if a file looks like a valid turboSETI .dat
# -----------------------------------------------------------------------
is_valid_dat() {
    local f="$1"
    local size
    size=$(wc -c < "$f" 2>/dev/null || echo 0)
    if [[ $size -lt 200 ]]; then
        return 1
    fi
    if grep -qE "(Top_Hit_#|Drift_Rate|# Source:)" "$f" 2>/dev/null; then
        return 0
    fi
    return 1
}

DOWNLOAD_SUCCESS=0

# -----------------------------------------------------------------------
# Option 1 — BL GBT L-band survey open data (blpd0.ssl.berkeley.edu)
# -----------------------------------------------------------------------
BL_TARGETS=(
    "HIP99427_hits.dat"
    "HIP17378_hits.dat"
    "HIP45167_hits.dat"
    "HIP65352_hits.dat"
    "HIP74995_hits.dat"
)

echo "--- Option 1: BL open data server ---"
echo "Probing https://blpd0.ssl.berkeley.edu/ for directory structure ..."
echo "(Server has an SSL cert mismatch; using -k to bypass)"

# Fetch the server root to discover what paths are available
BL_ROOT_HTML=$(curl -k -sL --max-time 15 "https://blpd0.ssl.berkeley.edu/" 2>/dev/null || true)
if [[ -n "$BL_ROOT_HTML" ]]; then
    echo "  Server responded. Scanning for .dat file paths ..."
    # Extract any href links ending in .dat from the directory listing
    BL_DAT_PATHS=$(echo "$BL_ROOT_HTML" | grep -oE 'href="[^"]*\.dat"' | sed 's/href="//;s/"//' | head -10 || true)
    if [[ -n "$BL_DAT_PATHS" ]]; then
        echo "  Found .dat paths on server:"
        echo "$BL_DAT_PATHS" | while read -r p; do echo "    $p"; done
    else
        # Try known subdirectory paths
        for subdir in "L_band_table" "GBT" "GBT_L_band" "hits" "dat_files"; do
            SUBDIR_HTML=$(curl -k -sL --max-time 10 "https://blpd0.ssl.berkeley.edu/$subdir/" 2>/dev/null || true)
            if echo "$SUBDIR_HTML" | grep -q "\.dat"; then
                echo "  Found .dat files under /$subdir/"
                BL_BASE="https://blpd0.ssl.berkeley.edu/$subdir"
                break
            fi
        done
    fi
else
    echo "  Server did not respond."
fi

for target in "${BL_TARGETS[@]}"; do
    dest="$BL_HITS_DIR/$target"
    if curl -L -k --max-time 30 --retry 2 --retry-delay 2 \
            --fail --show-error \
            -o "$dest" \
            "${BL_BASE:-https://blpd0.ssl.berkeley.edu/L_band_table}/$target" 2>&1; then
        if is_valid_dat "$dest"; then
            echo "  OK: $target ($(wc -c < "$dest") bytes)"
            DOWNLOAD_SUCCESS=$((DOWNLOAD_SUCCESS + 1))
        else
            echo "  WARN: $target invalid ($(wc -c < "$dest" 2>/dev/null || echo 0) bytes)"
            rm -f "$dest"
        fi
    else
        echo "  SKIP: $target (not found at current path)"
        rm -f "$dest" 2>/dev/null || true
    fi
done

if [[ $DOWNLOAD_SUCCESS -gt 0 ]]; then
    echo ""
    echo "Downloaded $DOWNLOAD_SUCCESS real BL hit table(s) — Tier 1 gap partially addressed."
    echo "Run: caffeinate -i bash scripts/run_pipeline_on_bl_data.sh"
    exit 0
fi

echo ""
echo "BL server download failed. Trying Option 2..."
echo ""

# -----------------------------------------------------------------------
# Option 2 — Run turboSETI on a BL-format HDF5 to produce a real .dat
#
# The Voyager 1 diagnostic file (blpd14) has only 16 time samples.
# turboSETI requires ≥32 time samples (needs drift_indexes_array_5.txt).
# So we generate a minimal synthetic BL-format H5 (32 steps, GBT L-band
# parameters, injected narrowband signal) and run turboSETI on it.
# The resulting .dat is in real turboSETI format and exercises the full
# pipeline — the same output format as actual telescope observations.
# -----------------------------------------------------------------------
echo "--- Option 2: turboSETI .dat via synthetic BL-format H5 (32 time steps) ---"
echo "  Generating GBT L-band format H5 with 32 time steps ..."

SYNTH_H5="$DATA_ROOT/bl_hits/synth_bl_32step.h5"
BEFORE_TS=$(date +%s)

# Step 2a: generate the synthetic H5
SYNTH_EXIT=0
"$VENV_PYTHON" - "$SYNTH_H5" <<'PYEOF' || SYNTH_EXIT=$?
import sys, os
import numpy as np
import h5py

out_h5 = sys.argv[1]
print(f"  Writing: {out_h5}")

# GBT L-band parameters matching the BL Voyager 2020 observation format
n_time  = 32          # 32 time samples (minimum for turboSETI drift search)
n_freq  = 1048576     # 1M fine channels = 1 GBT coarse channel at ~2.79 Hz/chan
fch1    = 8421.386719 # MHz (GBT L-band, Voyager-1 frequency region)
foff    = -2.7939677238464355e-06  # MHz/channel (-2.79 Hz/channel, decreasing)
tsamp   = 18.25361100799998        # seconds per time sample
tstart  = 59046.92634259259        # MJD (same as Voyager 2020 observation)

# Background noise: exponential distribution (chi-squared/power detector)
np.random.seed(2026)
noise_mean = 25.0
data = np.random.exponential(noise_mean, size=(n_time, 1, n_freq)).astype(np.float32)

# Inject a narrowband drifting signal (Voyager-like: ~0.38 Hz/s drift)
f_signal_mhz = 8420.5   # MHz
drift_hz_s   = 0.38     # Hz/s
snr_amp      = noise_mean * 200  # Very strong signal (SNR >> 10 threshold)

for t in range(n_time):
    t_sec = t * tsamp
    # Frequency drift: drift_hz_s [Hz/s] * t_sec [s] → Hz → MHz
    f_t = f_signal_mhz + drift_hz_s * t_sec * 1e-6
    # Channel index (foff is negative: higher freq = lower channel index)
    chan = int(round((f_t - fch1) / foff))
    if 0 <= chan < n_freq:
        data[t, 0, chan] += snr_amp

print(f"  Data shape: {data.shape} ({data.nbytes:,} bytes uncompressed)")

# Write HDF5 in exact blimpy format.
# CRITICAL: blimpy's H5Reader reads header from f['data'].attrs (the DATA
# DATASET's attributes), NOT from the root group attributes.
# Root group gets only CLASS/VERSION. Everything else goes on the dataset.
# Source: blimpy/io/hdf_reader.py read_header iterates self.h5['data'].attrs
# Source: blimpy/io/hdf_writer.py writes header via `dset.attrs[key] = val`
with h5py.File(out_h5, "w") as f:
    # Root: class metadata only
    f.attrs["CLASS"]   = "FILTERBANK"
    f.attrs["VERSION"] = "1.0"

    # Data dataset — same shape as blimpy HDF5: (n_time, n_ifs, n_chans)
    ds = f.create_dataset("data", data=data, compression="lzf")

    # Dimension labels as bytes (blimpy writes b"time" etc.)
    ds.dims[0].label = b"time"
    ds.dims[1].label = b"feed_id"
    ds.dims[2].label = b"frequency"

    # ALL header fields on the DATASET attrs (blimpy reads here, not root)
    ds.attrs["fch1"]         = np.float64(fch1)
    ds.attrs["foff"]         = np.float64(foff)
    ds.attrs["tsamp"]        = np.float64(tsamp)
    ds.attrs["tstart"]       = np.float64(tstart)
    ds.attrs["nchans"]       = np.int64(n_freq)
    ds.attrs["nifs"]         = np.int64(1)
    ds.attrs["nbits"]        = np.int64(32)
    ds.attrs["data_type"]    = np.int64(1)
    ds.attrs["machine_id"]   = np.int64(20)    # GBT
    ds.attrs["telescope_id"] = np.int64(6)     # GBT
    ds.attrs["source_name"]  = np.bytes_("SYNTH_BL_TIER1")
    ds.attrs["rawdatafile"]  = np.bytes_("")
    ds.attrs["az_start"]     = np.float64(0.0)
    ds.attrs["za_start"]     = np.float64(0.0)
    ds.attrs["src_raj"]      = np.float64(17.2112447222)
    ds.attrs["src_dej"]      = np.float64(12.4037816667)

size = os.path.getsize(out_h5)
print(f"  Written: {out_h5} ({size:,} bytes)")
PYEOF

if [[ $SYNTH_EXIT -ne 0 ]]; then
    echo "  WARN: synthetic H5 generation failed (exit=$SYNTH_EXIT) — skipping turboSETI."
else
    H5_SIZE=$(wc -c < "$SYNTH_H5" 2>/dev/null || echo 0)
    echo "  H5 generated: $H5_SIZE bytes. Running turboSETI ..."

    # Step 2b: run turboSETI on the synthetic H5
    TSETI_EXIT=0
    "$VENV_PYTHON" - "$SYNTH_H5" "$BL_HITS_DIR" <<'PYEOF' || TSETI_EXIT=$?
import sys, os

# Shim pkg_resources for Python 3.13 / blimpy compatibility
try:
    import pkg_resources
except ImportError:
    import types, importlib.metadata
    _mod = types.ModuleType("pkg_resources")
    class _DistributionNotFound(Exception):
        pass
    def _get_distribution(name):
        try:
            d = importlib.metadata.distribution(name)
            class _D:
                version = d.metadata["Version"]
            return _D()
        except importlib.metadata.PackageNotFoundError:
            raise _DistributionNotFound(name)
    _mod.get_distribution = _get_distribution
    _mod.DistributionNotFound = _DistributionNotFound
    _mod.require = lambda *a, **kw: None
    _mod.resource_filename = lambda *a, **kw: ""
    sys.modules["pkg_resources"] = _mod

try:
    from turbo_seti.find_doppler.find_doppler import FindDoppler
except ImportError as e:
    print(f"  turboSETI not installed: {e}")
    sys.exit(1)

h5_file = sys.argv[1]
out_dir  = sys.argv[2]
print(f"  Input:  {os.path.basename(h5_file)}")
print(f"  Output: {out_dir}")

fd = FindDoppler(
    h5_file,
    max_drift=4,
    min_drift=1e-4,
    snr=10,
    out_dir=out_dir,
    log_level_int=30,   # WARN only — suppress verbose INFO output
)
fd.search()
print("  turboSETI search complete.")
PYEOF

    DAT_FOUND=$(find "$BL_HITS_DIR" -name "*.dat" -newer "$SYNTH_H5" 2>/dev/null | head -1)
    rm -f "$SYNTH_H5"

    if [[ $TSETI_EXIT -eq 0 ]] && [[ -n "$DAT_FOUND" ]]; then
        echo ""
        echo "  turboSETI produced real .dat: $(basename "$DAT_FOUND")"
        echo "  This is real turboSETI output format — pipeline can now be tested."
        echo ""
        echo "Run: caffeinate -i bash scripts/run_pipeline_on_bl_data.sh"
        exit 0
    else
        echo "  turboSETI run failed or produced no .dat (exit=$TSETI_EXIT)."
        rm -f "$SYNTH_H5" 2>/dev/null || true
    fi
fi

echo ""
echo "Option 2 failed. Trying Option 3 (synthetic .dat directly)..."
echo ""

# -----------------------------------------------------------------------
# Option 3 — Synthetic files (pipeline format testing only)
# -----------------------------------------------------------------------
echo "--- Option 3: Synthetic .dat files (pipeline format testing) ---"
echo "NOTE: These do NOT constitute real observation data."
echo "      See docs/BL_DATA_DOWNLOAD.md for manual download instructions."
echo ""

"$VENV_PYTHON" - "$BL_HITS_DIR" <<'PYEOF'
import sys
import random

out_dir = sys.argv[1]

TARGETS = [
    ("GBT_synth_HIP99427", "57650.123", "301.4500", "+21.2300"),
    ("GBT_synth_HIP17378", "57651.456", "55.8900",  "-17.4500"),
    ("GBT_synth_HIP45167", "57652.789", "138.2300", "+12.7800"),
    ("GBT_synth_HIP65352", "57653.012", "201.5600", "+05.1200"),
    ("GBT_synth_HIP74995", "57654.345", "229.9800", "-03.4400"),
]

COLUMNS = "\t".join([
    "# Top_Hit_#", "Drift_Rate", "SNR", "Uncorrected_Frequency",
    "Corrected_Frequency", "Index", "freq_start", "freq_end",
    "SEFD", "SEFD_freq", "Coarse_Channel_Number",
    "Full_number_of_hits",
])

random.seed(42)

for source, mjd, ra, dec in TARGETS:
    filename = f"{source}_hits.dat"
    filepath = f"{out_dir}/{filename}"
    with open(filepath, "w") as f:
        f.write(f"# Source:{source}\n")
        f.write(f"# MJD:{mjd}\n")
        f.write(f"# RA:{ra}\n")
        f.write(f"# DEC:{dec}\n")
        f.write("# DELTAT:18.253611\n")
        f.write("# DELTAF(Hz):2.793968\n")
        f.write(f"{COLUMNS}\n")
        n_hits = random.randint(3, 8)
        for i in range(1, n_hits + 1):
            freq = round(random.uniform(1200.0, 1800.0), 6)
            drift = round(random.uniform(-2.0, 2.0), 6)
            snr = round(random.uniform(6.0, 50.0), 6)
            row = "\t".join([
                str(i),
                str(drift),
                str(snr),
                str(freq),
                str(freq),
                str(random.randint(1000, 9000)),
                str(round(freq - 0.001, 6)),
                str(round(freq + 0.001, 6)),
                "11.0",
                str(freq),
                str(random.randint(0, 63)),
                str(n_hits),
            ])
            f.write(f"{row}\n")
    print(f"  Created: {filename} ({n_hits} hits) [SYNTHETIC]")

print("")
print("Run: caffeinate -i bash scripts/run_pipeline_on_bl_data.sh")
print("")
print("For real BL data, see docs/BL_DATA_DOWNLOAD.md")
PYEOF

echo ""
echo "=== Manual download options ==="
echo "1. Browser: https://seti.berkeley.edu/listen/data.html"
echo "   Download .dat files to ~/technosignature-data/bl_hits/"
echo ""
echo "2. git-lfs (if not installed): brew install git-lfs"
echo "   Then re-run this script."
echo ""
echo "3. See docs/BL_DATA_DOWNLOAD.md for full instructions."
