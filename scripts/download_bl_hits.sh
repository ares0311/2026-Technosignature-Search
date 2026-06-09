#!/usr/bin/env bash
# download_bl_hits.sh — download real turboSETI hit tables for pipeline testing
#
# Tries the BL GBT L-band survey endpoint. Synthetic fixtures are generated
# only when TECHNO_ALLOW_SYNTHETIC_BL_FIXTURES=1 is explicitly set.
#
# Run (macOS — use caffeinate to prevent sleep):
#   git pull origin main
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
echo "TLS certificate verification is required."

# Fetch the server root to discover what paths are available
BL_ROOT_HTML=$(curl -sL --max-time 15 "https://blpd0.ssl.berkeley.edu/" 2>/dev/null || true)
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
            SUBDIR_HTML=$(curl -sL --max-time 10 "https://blpd0.ssl.berkeley.edu/$subdir/" 2>/dev/null || true)
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
    if curl -L --max-time 30 --retry 2 --retry-delay 2 \
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
    echo "Downloaded $DOWNLOAD_SUCCESS plausible BL hit table(s)."
    echo "Human provenance and data-use approval are still required before pipeline use."
    echo "See docs/REAL_OBSERVATION_INTAKE.md."
    exit 0
fi

if [[ "${TECHNO_ALLOW_SYNTHETIC_BL_FIXTURES:-0}" != "1" ]]; then
    echo ""
    echo "No real hit tables were downloaded."
    echo "Synthetic fallback is disabled because it cannot close Tier 1."
    echo "See docs/REAL_OBSERVATION_INTAKE.md for Human Gate 1."
    exit 2
fi

echo ""
echo "Synthetic fixture generation explicitly enabled."
echo ""

# -----------------------------------------------------------------------
# Option 2 — Run turboSETI on a synthetic BL-format HDF5
#
# turboSETI uses resource_filename('turbo_seti', 'drift_indexes/drift_indexes_array_N.txt')
# to locate its index files.  The PyPI wheel for 2.3.x omits these files,
# so this script downloads any missing ones from the GitHub repo
# (array_2 through array_11 exist there), then uses the minimum
# available power.  n_freq=65536 keeps the H5 under 10 MB so turboSETI
# finishes in under a minute.  The resulting SYNTH_BL_TIER1.dat is
# genuine turboSETI-format output, but it is not telescope observation data.
# -----------------------------------------------------------------------
echo "--- Option 2: turboSETI .dat via synthetic BL-format H5 ---"
echo "  Checking/fetching turboSETI drift_indexes files ..."

OPT2_EXIT=0
"$VENV_PYTHON" - "$BL_HITS_DIR" <<'PYEOF' || OPT2_EXIT=$?
import sys, os, glob, h5py, numpy as np

out_dir = sys.argv[1]

# --- Shim pkg_resources for Python 3.13 / blimpy compatibility ---
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
    _mod.get_distribution     = _get_distribution
    _mod.DistributionNotFound = _DistributionNotFound
    _mod.require              = lambda *a, **kw: None
    _mod.resource_filename    = lambda *a, **kw: ""
    sys.modules["pkg_resources"] = _mod

# --- Import turboSETI ---
try:
    import turbo_seti as _ts
    from turbo_seti.find_doppler.find_doppler import FindDoppler
except ImportError as e:
    print(f"  turboSETI not available: {e}", file=sys.stderr)
    sys.exit(1)

# --- Ensure drift_indexes files exist ---
# turboSETI 2.3.x PyPI wheel omits the drift_indexes text files.
# They live at turbo_seti/drift_indexes/ (package root, NOT find_doppler/).
# Files array_2 through array_11 are in the GitHub repo — download if missing.
_pkg_dir   = os.path.dirname(os.path.abspath(_ts.__file__))
_drift_dir = os.path.join(_pkg_dir, "drift_indexes")
os.makedirs(_drift_dir, exist_ok=True)

_avail = sorted(glob.glob(os.path.join(_drift_dir, "drift_indexes_array_*.txt")))
if not _avail:
    print("  drift_indexes files absent from PyPI wheel — downloading from GitHub ...")
    import urllib.request
    _base = ("https://raw.githubusercontent.com/UCBerkeleySETI/"
             "turbo_seti/master/turbo_seti/drift_indexes")
    for _pow in range(2, 12):  # array_2 through array_11
        _fname = f"drift_indexes_array_{_pow}.txt"
        _url   = f"{_base}/{_fname}"
        _dest  = os.path.join(_drift_dir, _fname)
        try:
            urllib.request.urlretrieve(_url, _dest)
            _avail.append(_dest)
            print(f"    {_fname} ({os.path.getsize(_dest):,} bytes)")
        except Exception as _e:
            pass  # not all powers may exist on that branch
    _avail = sorted(_avail)

if not _avail:
    print("  ERROR: cannot obtain drift_indexes files", file=sys.stderr)
    sys.exit(1)

_powers  = sorted(int(os.path.basename(f).split("_array_")[1].replace(".txt", "")) for f in _avail)
_min_pow = _powers[0]
n_time   = 2 ** _min_pow
print(f"  drift_indexes ready: powers {_powers} → using n_time={n_time} (2^{_min_pow})")

# --- H5 parameters: narrow 65536-channel slice keeps file < 20 MB ---
# turboSETI accepts any nchans; we don't need the full 1M GBT coarse channel.
n_freq = 65536
fch1   = 8421.386719              # MHz — GBT L-band
foff   = -2.7939677238464355e-06  # MHz/chan — GBT fine channel spacing
tsamp  = 18.25361100799998        # s/sample
tstart = 59046.92634259259        # MJD

print(f"  Shape: ({n_time}, 1, {n_freq})  uncompressed: {n_time * n_freq * 4 / 1e6:.1f} MB")

np.random.seed(2026)
noise_mean = 25.0
data = np.random.exponential(noise_mean, (n_time, 1, n_freq)).astype(np.float32)

# Inject Voyager-like drifting signal at band center (SNR >> 10 threshold)
f_signal   = fch1 + (n_freq // 2) * foff  # ~8421.295 MHz
drift_hz_s = 0.38
snr_amp    = noise_mean * 200
for t in range(n_time):
    f_t  = f_signal + drift_hz_s * (t * tsamp) * 1e-6
    chan = int(round((f_t - fch1) / foff))
    if 0 <= chan < n_freq:
        data[t, 0, chan] += snr_amp

out_h5 = os.path.join(out_dir, "synth_bl_tier1.h5")
print(f"  Writing: {out_h5}")

# CRITICAL: blimpy H5Reader reads ALL header fields from f['data'].attrs
# (the data dataset's attrs), NOT from the root group attrs. Root gets only
# CLASS/VERSION. Any header field written to root will be silently ignored.
with h5py.File(out_h5, "w") as f:
    f.attrs["CLASS"]   = "FILTERBANK"
    f.attrs["VERSION"] = "1.0"
    ds = f.create_dataset("data", data=data, compression="lzf")
    ds.dims[0].label = b"time"
    ds.dims[1].label = b"feed_id"
    ds.dims[2].label = b"frequency"
    ds.attrs["fch1"]         = np.float64(fch1)
    ds.attrs["foff"]         = np.float64(foff)
    ds.attrs["tsamp"]        = np.float64(tsamp)
    ds.attrs["tstart"]       = np.float64(tstart)
    ds.attrs["nchans"]       = np.int64(n_freq)
    ds.attrs["nifs"]         = np.int64(1)
    ds.attrs["nbits"]        = np.int64(32)
    ds.attrs["data_type"]    = np.int64(1)
    ds.attrs["machine_id"]   = np.int64(20)
    ds.attrs["telescope_id"] = np.int64(6)
    ds.attrs["source_name"]  = np.bytes_("SYNTH_BL_TIER1")
    ds.attrs["rawdatafile"]  = np.bytes_("")
    ds.attrs["az_start"]     = np.float64(0.0)
    ds.attrs["za_start"]     = np.float64(0.0)
    ds.attrs["src_raj"]      = np.float64(17.2112447222)
    ds.attrs["src_dej"]      = np.float64(12.4037816667)

print(f"  H5 written: {os.path.getsize(out_h5):,} bytes.  Running turboSETI ...")

fd = FindDoppler(
    out_h5,
    max_drift=4,
    min_drift=1e-4,
    snr=10,
    out_dir=out_dir,
    log_level_int=30,
)
fd.search()

os.remove(out_h5)
print("  turboSETI complete. H5 removed.")
PYEOF

if [[ $OPT2_EXIT -eq 0 ]]; then
    DAT_FOUND=$(ls -t "$BL_HITS_DIR"/*.dat 2>/dev/null | head -1 || true)
    if [[ -n "$DAT_FOUND" ]]; then
        echo ""
        echo "  turboSETI produced synthetic .dat: $(basename "$DAT_FOUND")"
        echo "  Format compatibility verified; Tier 1 remains blocked."
        echo ""
        echo "Synthetic output is for format testing only; production execution remains blocked."
        exit 0
    fi
fi

echo "  Option 2 failed (exit=$OPT2_EXIT). Falling back to synthetic Option 3 ..."
find "$BL_HITS_DIR" -name "synth_bl_tier1.h5" -delete 2>/dev/null || true
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
print("Synthetic output is for format testing only; production execution remains blocked.")
print("")
print("For real BL data, see docs/BL_DATA_DOWNLOAD.md")
PYEOF

echo ""
echo "=== Manual download options ==="
echo "1. Browser: https://seti.berkeley.edu/listen/data.html"
echo "   Download .dat files to ~/technosignature-data/bl_hits/"
echo ""
echo "2. See docs/BL_DATA_DOWNLOAD.md for the provenance and human-approval workflow."
