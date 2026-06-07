#!/usr/bin/env bash
# download_bl_hits.sh — download real turboSETI hit tables from BL open data archive
#
# Tries multiple sources in order:
#   1. BL GBT L-band survey (blpd0.ssl.berkeley.edu) — requires curl -L for redirects
#   2. turboSETI package test data (from installed package if available)
#   3. Generates synthetic .dat files as a last resort for pipeline testing
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
# Helper: check if a downloaded file looks like a valid turboSETI .dat
# -----------------------------------------------------------------------
is_valid_dat() {
    local f="$1"
    local size
    size=$(wc -c < "$f" 2>/dev/null || echo 0)
    # A valid .dat must be > 200 bytes and contain "# Source:" or "Top_Hit_#"
    if [[ $size -lt 200 ]]; then
        return 1
    fi
    if grep -qE "(# Source:|Top_Hit_#|Drift_Rate)" "$f" 2>/dev/null; then
        return 0
    fi
    return 1
}

DOWNLOAD_SUCCESS=0

# -----------------------------------------------------------------------
# Option 1 — BL GBT L-band survey open data
# NOTE: Server may redirect HTTP→HTTPS; always use -L (follow redirects)
# -----------------------------------------------------------------------
BL_BASE="http://blpd0.ssl.berkeley.edu/L_band_table"
BL_TARGETS=(
    "HIP99427_hits.dat"
    "HIP17378_hits.dat"
    "HIP45167_hits.dat"
    "HIP65352_hits.dat"
    "HIP74995_hits.dat"
)

echo "Attempting download from BL open data archive..."
echo "(If this fails, see docs/BL_DATA_DOWNLOAD.md for manual instructions)"
echo ""

for target in "${BL_TARGETS[@]}"; do
    dest="$BL_HITS_DIR/$target"
    # Try HTTPS first, then HTTP with redirect following
    for url in "https://blpd0.ssl.berkeley.edu/L_band_table/$target" "$BL_BASE/$target"; do
        if curl -L --max-time 30 --retry 2 --retry-delay 2 \
                --fail --silent --show-error \
                -o "$dest" "$url" 2>/dev/null; then
            if is_valid_dat "$dest"; then
                echo "  OK: $target ($(wc -c < "$dest") bytes)"
                DOWNLOAD_SUCCESS=$((DOWNLOAD_SUCCESS + 1))
                break
            else
                echo "  WARN: $target downloaded but looks invalid ($(wc -c < "$dest" 2>/dev/null || echo 0) bytes) — discarding"
                rm -f "$dest"
            fi
        fi
    done
done

if [[ $DOWNLOAD_SUCCESS -gt 0 ]]; then
    echo ""
    echo "Downloaded $DOWNLOAD_SUCCESS real BL hit table(s) from open data archive."
    echo "Run: bash scripts/run_pipeline_on_bl_data.sh"
    exit 0
fi

echo ""
echo "BL server download failed or returned invalid data."
echo ""

# -----------------------------------------------------------------------
# Option 2 — turboSETI package test data (already installed in .venv)
# These are real-format .dat files shipped with the turboSETI test suite.
# -----------------------------------------------------------------------
echo "Looking for turboSETI package test data in .venv..."
TURBO_SETI_DAT=$("$VENV_PYTHON" -c "
import pathlib, sys
pkg_dirs = [
    pathlib.Path('$REPO_ROOT/.venv/lib'),
]
dat_files = []
for d in pkg_dirs:
    if d.exists():
        # Search without importing turbo_seti (avoids blimpy pkg_resources issue)
        dat_files = [f for f in d.rglob('*.dat')
                     if 'turbo_seti' in str(f) or 'blc' in f.name.lower()]
        if dat_files:
            break
for f in dat_files[:5]:
    print(f)
" 2>/dev/null || true)

if [[ -n "$TURBO_SETI_DAT" ]]; then
    PKG_DAT_COUNT=0
    while IFS= read -r src; do
        name=$(basename "$src")
        dest="$BL_HITS_DIR/$name"
        if [[ -f "$src" ]] && is_valid_dat "$src"; then
            cp "$src" "$dest"
            echo "  OK: $name ($(wc -c < "$dest") bytes) [from installed package]"
            PKG_DAT_COUNT=$((PKG_DAT_COUNT + 1))
        fi
    done <<< "$TURBO_SETI_DAT"

    if [[ $PKG_DAT_COUNT -gt 0 ]]; then
        echo ""
        echo "Copied $PKG_DAT_COUNT .dat file(s) from installed turboSETI package."
        echo "NOTE: These are test fixtures from turboSETI, not from your telescope."
        echo "      They are useful for format validation but do not close the real-data gap."
        echo "Run: bash scripts/run_pipeline_on_bl_data.sh"
        exit 0
    fi
fi

echo "No turboSETI package test data found."
echo ""

# -----------------------------------------------------------------------
# Option 3 — Generate synthetic .dat files (pipeline testing only)
# -----------------------------------------------------------------------
echo "Generating synthetic turboSETI .dat files for pipeline testing."
echo "NOTE: These are synthetic — they do NOT constitute real observation data."
echo "      See docs/BL_DATA_DOWNLOAD.md for how to obtain real data."
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
print("Done. Run scripts/run_pipeline_on_bl_data.sh to process these files.")
print("")
print("IMPORTANT: Real BL data must be downloaded manually.")
print("See docs/BL_DATA_DOWNLOAD.md for instructions.")
PYEOF
