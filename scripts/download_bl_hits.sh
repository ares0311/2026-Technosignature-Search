#!/usr/bin/env bash
# download_bl_hits.sh — download sample Breakthrough Listen turboSETI hit tables
#
# Uses the BL Open Data Release via HTTP (no credentials required).
# Downloads only small .dat files (KB-MB), not raw filterbank files (GB).
#
# Run (macOS — use caffeinate to prevent sleep during download):
#   caffeinate -i bash scripts/download_bl_hits.sh
#
# To change the download directory:
#   caffeinate -i env TECHNO_DATA_DIR=/some/other/path bash scripts/download_bl_hits.sh

set -euo pipefail

DATA_ROOT="${TECHNO_DATA_DIR:-$HOME/technosignature-data}"
BL_HITS_DIR="$DATA_ROOT/bl_hits"

mkdir -p "$BL_HITS_DIR"

echo "Downloading BL Open Data Release hit tables into: $BL_HITS_DIR"
echo ""

# Base URL for BL Open Data Release (GBT L-band survey, publicly accessible)
BL_BASE="http://blpd0.ssl.berkeley.edu/L_band_table"

# Sample targets from the BL GBT L-band survey (HIP catalog stars)
# These are pre-computed turboSETI hit tables — small .dat files
TARGETS=(
    "HIP99427"
    "HIP17378"
    "HIP45167"
    "HIP65352"
    "HIP74995"
)

DOWNLOADED=0
FAILED=0

for TARGET in "${TARGETS[@]}"; do
    OUTFILE="$BL_HITS_DIR/${TARGET}_hits.dat"
    URL="${BL_BASE}/${TARGET}_hits.dat"

    echo -n "  Downloading $TARGET ... "

    if curl -sf --max-time 30 -o "$OUTFILE" "$URL" 2>/dev/null; then
        SIZE=$(wc -c < "$OUTFILE")
        echo "OK (${SIZE} bytes)"
        DOWNLOADED=$((DOWNLOADED + 1))
    else
        echo "FAILED (will try alternative)"
        rm -f "$OUTFILE"
        FAILED=$((FAILED + 1))
    fi
done

echo ""

# If the primary BL endpoint failed, fall back to the BL GitHub sample data
if [[ $DOWNLOADED -eq 0 ]]; then
    echo "Primary endpoint unavailable. Trying BL GitHub sample data..."
    echo ""

    # BL published a sample turboSETI output on GitHub
    GITHUB_BASE="https://raw.githubusercontent.com/UCBerkeleySETI/breakthrough/master/GBT/GBT_Lband_Survey"
    SAMPLE_FILES=(
        "blc07_guppi_57650_67573_HIP99427_0011.gpuspec.0000.dat"
    )

    for FILE in "${SAMPLE_FILES[@]}"; do
        OUTFILE="$BL_HITS_DIR/$FILE"
        URL="${GITHUB_BASE}/${FILE}"

        echo -n "  Downloading $FILE ... "
        if curl -sf --max-time 60 -L -o "$OUTFILE" "$URL" 2>/dev/null; then
            SIZE=$(wc -c < "$OUTFILE")
            echo "OK (${SIZE} bytes)"
            DOWNLOADED=$((DOWNLOADED + 1))
        else
            echo "FAILED"
            rm -f "$OUTFILE"
        fi
    done
fi

echo ""
echo "Results: $DOWNLOADED downloaded, $FAILED failed"
echo ""

if [[ $DOWNLOADED -gt 0 ]]; then
    echo "Files in $BL_HITS_DIR:"
    ls -lh "$BL_HITS_DIR/"
    echo ""
    echo "Next step: run scripts/run_pipeline_on_bl_data.sh"
else
    echo "WARNING: No files downloaded."
    echo "See docs/BL_DATA_DOWNLOAD.md for manual download instructions."
fi
