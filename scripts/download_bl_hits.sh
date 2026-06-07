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
echo "Trying https://blpd0.ssl.berkeley.edu/L_band_table/ ..."

for target in "${BL_TARGETS[@]}"; do
    dest="$BL_HITS_DIR/$target"
    # Try HTTPS first, then HTTP with redirect following
    # Note: --fail exits non-zero on HTTP 4xx/5xx; errors shown (not suppressed)
    if curl -L --max-time 30 --retry 2 --retry-delay 2 \
            --fail --show-error \
            -o "$dest" \
            "https://blpd0.ssl.berkeley.edu/L_band_table/$target" 2>&1; then
        if is_valid_dat "$dest"; then
            echo "  OK: $target ($(wc -c < "$dest") bytes)"
            DOWNLOAD_SUCCESS=$((DOWNLOAD_SUCCESS + 1))
        else
            echo "  WARN: $target invalid ($(wc -c < "$dest" 2>/dev/null || echo 0) bytes — likely redirect page)"
            rm -f "$dest"
        fi
    else
        echo "  SKIP: $target (server error — see above)"
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
# Option 2 — turboSETI GitHub test fixtures via git-lfs
# These are real GBT observation-derived test fixtures (blc1 = BL Compute node 1)
# -----------------------------------------------------------------------
echo "--- Option 2: turboSETI GitHub test data (requires git-lfs) ---"

if ! command -v git-lfs &>/dev/null; then
    echo "  git-lfs not installed. Install with: brew install git-lfs"
    echo "  Then re-run this script."
else
    CLONE_DIR=$(mktemp -d)
    echo "  Cloning turboSETI (shallow, test_data only) ..."
    if git clone --depth=1 --filter=blob:none --sparse \
            https://github.com/UCBerkeleySETI/turbo_seti \
            "$CLONE_DIR" 2>&1; then
        cd "$CLONE_DIR"
        git sparse-checkout set tests/test_data 2>&1
        git lfs pull --include="tests/test_data/*.dat" 2>&1 || true

        DAT_COUNT=0
        while IFS= read -r -d '' src; do
            name=$(basename "$src")
            dest="$BL_HITS_DIR/$name"
            if is_valid_dat "$src"; then
                cp "$src" "$dest"
                echo "  OK: $name ($(wc -c < "$dest") bytes) [turboSETI test fixture]"
                DAT_COUNT=$((DAT_COUNT + 1))
            fi
        done < <(find "$CLONE_DIR/tests/test_data" -name "*.dat" -print0 2>/dev/null)

        cd "$REPO_ROOT"
        rm -rf "$CLONE_DIR"

        if [[ $DAT_COUNT -gt 0 ]]; then
            echo ""
            echo "Copied $DAT_COUNT .dat file(s) from turboSETI test fixtures."
            echo "NOTE: These are GBT-derived test fixtures, useful for format/pipeline testing."
            echo "      For a full Tier 1 gap closure, also download from the BL open data portal."
            echo "Run: caffeinate -i bash scripts/run_pipeline_on_bl_data.sh"
            exit 0
        else
            echo "  No valid .dat files found in turboSETI test data (LFS may not have resolved)."
        fi
    else
        echo "  git clone failed (network issue or repo moved)."
        rm -rf "$CLONE_DIR" 2>/dev/null || true
    fi
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
