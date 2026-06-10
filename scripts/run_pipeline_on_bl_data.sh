#!/usr/bin/env bash
# run_pipeline_on_bl_data.sh — Run the scoring pipeline on BL hit tables
#
# Usage:
#   bash scripts/run_pipeline_on_bl_data.sh [--dat PATH]
#
# Closes: Tier 1 gap — "Real observation data — no actual telescope data has been ingested"
#
# Looks for .dat files under data/bl_hits/ (or --dat override), runs
# techno-search run-pipeline on each, and writes scored reports to results/.
#
# All Python is invoked via .venv/bin/python (never system python3).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG="$REPO_ROOT/scripts/run_pipeline.log"
VENV_CLI="$REPO_ROOT/.venv/bin/techno-search"
DATA_DIR="$REPO_ROOT/data/bl_hits"
RESULTS_DIR="$REPO_ROOT/results"

mkdir -p "$RESULTS_DIR"

log() { echo "[$(date '+%Y-%m-%dT%H:%M:%S')] $*"; }

# Parse optional --dat flag
DAT_OVERRIDE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dat) DAT_OVERRIDE="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

log "=== run_pipeline_on_bl_data.sh starting ==="
log "Repo root   : $REPO_ROOT"
log "CLI binary  : $VENV_CLI"
log "Results dir : $RESULTS_DIR"

if [[ ! -f "$VENV_CLI" ]]; then
  log "ERROR: $VENV_CLI not found. Run: cd $REPO_ROOT && .venv/bin/pip install -e .[dev]"
  exit 1
fi

# Build list of .dat files to process
if [[ -n "$DAT_OVERRIDE" ]]; then
  DAT_FILES=("$DAT_OVERRIDE")
else
  mapfile -t DAT_FILES < <(find "$DATA_DIR" -name "*.dat" 2>/dev/null | sort)
fi

if [[ ${#DAT_FILES[@]} -eq 0 ]]; then
  log "No .dat files found in $DATA_DIR"
  log "Run scripts/download_bl_hits.sh first."
  exit 1
fi

log "Found ${#DAT_FILES[@]} .dat file(s) to process."

PASS=0
FAIL=0

for DAT in "${DAT_FILES[@]}"; do
  BASENAME=$(basename "$DAT" .dat)
  OUT_DIR="$RESULTS_DIR/$BASENAME"
  mkdir -p "$OUT_DIR"

  log "--- Processing: $DAT ---"
  log "Output dir: $OUT_DIR"

  # Validate input first
  log "Running validate-input ..."
  if "$VENV_CLI" validate-input "$DAT" --track radio 2>&1; then
    log "Input validation passed."
  else
    log "WARNING: Input validation reported issues (continuing anyway for diagnostic)."
  fi

  # Run the pipeline
  log "Running run-pipeline ..."
  if "$VENV_CLI" run-pipeline "$DAT" \
        --track radio \
        --output-dir "$OUT_DIR" 2>&1; then
    log "Pipeline succeeded."
    PASS=$((PASS + 1))

    # Show the manifest if it exists
    MANIFEST=$(find "$OUT_DIR" -name "*.manifest.json" | head -1)
    if [[ -n "$MANIFEST" ]]; then
      log "Manifest: $MANIFEST"
      log "Manifest contents:"
      cat "$MANIFEST"
    fi
  else
    log "ERROR: Pipeline failed for $DAT"
    FAIL=$((FAIL + 1))
  fi
done

log ""
log "=== Summary ==="
log "  Processed : ${#DAT_FILES[@]}"
log "  Passed    : $PASS"
log "  Failed    : $FAIL"
log ""
log "Scored reports written to: $RESULTS_DIR"
log ""
if [[ $FAIL -gt 0 ]]; then
  log "NEXT STEP: Review errors above, check logs, re-run."
  exit 1
fi
log "NEXT STEP: Review reports in $RESULTS_DIR"
log "  Then: bash scripts/calibrate_thresholds.sh (coming soon)"
log "=== run_pipeline_on_bl_data.sh done ==="
