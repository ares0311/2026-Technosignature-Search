#!/usr/bin/env bash
# run_pipeline_on_bl_data.sh — Run techno-search pipeline on all BL hit tables
#
# Usage:
#   bash scripts/run_pipeline_on_bl_data.sh [--dat-dir PATH] [--workers N]
#
# Closes: Tier 1 gap — "Real observation data — no actual telescope data has been ingested"
#
# Parallel processing:
#   Runs up to 12 workers in parallel (M4 Max has 12 performance cores).
#   Override with --workers N.
#
# Resume / restart behaviour:
#   Each .dat file is scored into its own subdirectory under results/.
#   If that subdirectory already contains a *.manifest.json the file is skipped.
#   Stop and restart at any time — already-completed files are never re-processed.
#
# All logic lives in scripts/bl_fetch.py (run-pipeline subcommand).
# All Python is invoked via .venv/bin/python (Python 3.14.3, never system python3).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$REPO_ROOT/.venv/bin/python"
BL_FETCH="$REPO_ROOT/scripts/bl_fetch.py"
TECHNO_SEARCH="$REPO_ROOT/.venv/bin/techno-search"
DATA_DIR="$REPO_ROOT/data/bl_hits"
RESULTS_DIR="$REPO_ROOT/results"
WORKERS=12

log() { echo "[$(date '+%Y-%m-%dT%H:%M:%S')] $*"; }

# Parse optional flags
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dat-dir)   DATA_DIR="$2";   shift 2 ;;
    --workers)   WORKERS="$2";    shift 2 ;;
    *) log "Unknown argument: $1"; exit 1 ;;
  esac
done

log "=== run_pipeline_on_bl_data.sh starting ==="
log "Repo root   : $REPO_ROOT"
log "Python      : $("$VENV" --version 2>&1)"
log "Data dir    : $DATA_DIR"
log "Results dir : $RESULTS_DIR"
log "Workers     : $WORKERS (M4 Max has 12 performance cores)"

if [[ ! -f "$TECHNO_SEARCH" ]]; then
  log "ERROR: $TECHNO_SEARCH not found."
  log "Run: cd $REPO_ROOT && .venv/bin/pip install -e .[dev]"
  exit 1
fi

DAT_COUNT=$(find "$DATA_DIR" -name "*.dat" 2>/dev/null | wc -l | tr -d ' ')
if [[ "$DAT_COUNT" -eq 0 ]]; then
  log "No .dat files found in $DATA_DIR"
  log "Run scripts/download_bl_hits.sh first."
  exit 1
fi

log "Found $DAT_COUNT .dat file(s) — launching parallel pipeline ..."

"$VENV" "$BL_FETCH" run-pipeline \
  "$DATA_DIR" \
  "$RESULTS_DIR" \
  --techno-search "$TECHNO_SEARCH" \
  --workers "$WORKERS"

log ""
log "Scored reports written to: $RESULTS_DIR"
log "NEXT STEP: Review reports in $RESULTS_DIR"
log "  Then: bash scripts/calibrate_thresholds.sh (coming soon)"
log "=== run_pipeline_on_bl_data.sh done ==="
