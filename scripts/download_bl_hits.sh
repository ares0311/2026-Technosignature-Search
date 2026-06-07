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
# Option 2 — BL Voyager 1 diagnostic data (blpd14.ssl.berkeley.edu)
# turboSETI generates .dat files by running on .h5 filterbank inputs.
# This downloads the BL Voyager 1 test .h5 and runs turboSETI to produce
# a real .dat hit table — the same approach turboSETI's own CI uses.
# -----------------------------------------------------------------------
echo "--- Option 2: BL Voyager 1 test data + turboSETI run ---"

VOYAGER_H5_URL="http://blpd14.ssl.berkeley.edu/voyager_2020/single_coarse_channel/single_coarse_guppi_59046_80036_DIAG_VOYAGER-1_0011.rawspec.0000.h5"
VOYAGER_H5="$DATA_ROOT/bl_hits/Voyager1_test.h5"
VOYAGER_DAT="$BL_HITS_DIR/Voyager1_DIAG_hits.dat"

echo "  Probing blpd14.ssl.berkeley.edu ..."
HTTP_STATUS=$(curl -k -sL -o /dev/null -w "%{http_code}" --max-time 10 \
    "$VOYAGER_H5_URL" 2>/dev/null || echo "000")

if [[ "$HTTP_STATUS" == "200" ]]; then
    echo "  Server accessible (HTTP $HTTP_STATUS). Downloading Voyager 1 .h5 (~200MB) ..."
    if curl -k -L --max-time 300 --retry 2 --retry-delay 5 \
            --progress-bar -o "$VOYAGER_H5" "$VOYAGER_H5_URL" 2>&1; then
        H5_SIZE=$(wc -c < "$VOYAGER_H5" 2>/dev/null || echo 0)
        echo "  Downloaded: Voyager1_test.h5 ($H5_SIZE bytes)"
        if [[ $H5_SIZE -lt 1000000 ]]; then
            echo "  WARN: file too small ($H5_SIZE bytes) — server may have returned an error page"
            rm -f "$VOYAGER_H5"
        else
            echo "  Ensuring pkg_resources available (blimpy dependency) ..."
            "$VENV_PYTHON" -m pip install "setuptools>=68" -q 2>&1 | grep -v "^$" || true
            echo "  Running turboSETI to generate .dat hit table ..."
            TSETI_BIN="$REPO_ROOT/.venv/bin/turboSETI"
            if [[ ! -f "$TSETI_BIN" ]]; then
                echo "  turboSETI not installed — installing ..."
                "$VENV_PYTHON" -m pip install "setuptools>=68" "turbo_seti" -q 2>&1 | grep -v "^$" || true
            fi
            if "$TSETI_BIN" "$VOYAGER_H5" \
                    -o "$BL_HITS_DIR" \
                    -s 10 \
                    -M 4 2>&1; then
                DAT_FOUND=$(find "$BL_HITS_DIR" -name "*.dat" -newer "$VOYAGER_H5" 2>/dev/null | head -1)
                if [[ -n "$DAT_FOUND" ]]; then
                    echo ""
                    echo "  Generated real .dat from Voyager 1 BL data — Tier 1 gap addressed."
                    echo "Run: caffeinate -i bash scripts/run_pipeline_on_bl_data.sh"
                    rm -f "$VOYAGER_H5"
                    exit 0
                else
                    echo "  turboSETI ran but no .dat produced."
                fi
            else
                echo "  turboSETI run failed."
            fi
            rm -f "$VOYAGER_H5"
        fi
    else
        echo "  Download failed."
        rm -f "$VOYAGER_H5" 2>/dev/null || true
    fi
else
    echo "  blpd14 not accessible (HTTP $HTTP_STATUS) — server requires Berkeley network access."
fi

echo ""
echo "All network sources failed. Trying Option 3 (manual instructions below)..."
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
