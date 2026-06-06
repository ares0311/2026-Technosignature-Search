#!/usr/bin/env bash
# run_pipeline_on_bl_data.sh — run the techno-search pipeline on downloaded BL hit tables
#
# Prerequisites:
#   1. Run scripts/setup_data_dirs.sh
#   2. Run scripts/download_bl_hits.sh (or manually place .dat files in ~/technosignature-data/bl_hits/)
#
# Run (macOS — use caffeinate to prevent sleep during long pipeline run):
#   caffeinate -i bash scripts/run_pipeline_on_bl_data.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_ROOT="${TECHNO_DATA_DIR:-$HOME/technosignature-data}"
BL_HITS_DIR="$DATA_ROOT/bl_hits"
PIPELINE_OUT="$DATA_ROOT/pipeline_out"

VENV_PYTHON="$REPO_ROOT/.venv/bin/python"
VENV_CLI="$REPO_ROOT/.venv/bin/techno-search"

if [[ ! -f "$VENV_CLI" ]]; then
    echo "ERROR: techno-search CLI not found at $VENV_CLI"
    echo "Run: cd $REPO_ROOT && pip install -e ."
    exit 1
fi

shopt -s nullglob
DAT_FILES=("$BL_HITS_DIR"/*.dat)
shopt -u nullglob
if [[ ${#DAT_FILES[@]} -eq 0 ]]; then
    echo "ERROR: No .dat files found in $BL_HITS_DIR"
    echo "Run scripts/download_bl_hits.sh first."
    exit 1
fi

echo "Running pipeline on BL hit tables in: $BL_HITS_DIR"
echo "Output directory: $PIPELINE_OUT"
echo ""

mkdir -p "$PIPELINE_OUT"

SUCCESS=0
FAILED=0

for DAT_FILE in "$BL_HITS_DIR"/*.dat; do
    BASENAME=$(basename "$DAT_FILE" .dat)
    OUT_DIR="$PIPELINE_OUT/$BASENAME"

    echo "--- Processing: $BASENAME ---"
    mkdir -p "$OUT_DIR"

    if "$VENV_CLI" run-pipeline \
        "$DAT_FILE" \
        --track radio \
        --output-dir "$OUT_DIR" 2>&1; then
        echo "  OK: output in $OUT_DIR"
        SUCCESS=$((SUCCESS + 1))
    else
        echo "  FAILED (see above for error)"
        FAILED=$((FAILED + 1))
    fi
    echo ""
done

echo "Pipeline run complete: $SUCCESS succeeded, $FAILED failed"
echo ""

if [[ $SUCCESS -gt 0 ]]; then
    echo "Review output reports:"
    find "$PIPELINE_OUT" -name "*.md" | head -10
fi
