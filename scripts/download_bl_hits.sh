#!/usr/bin/env bash
# download_bl_hits.sh — Download Voyager 1 H5, run turboSETI, produce hit table
#
# Usage:
#   caffeinate -i bash scripts/download_bl_hits.sh 2>&1 | tee scripts/download_bl_hits.log
#
# Closes: Tier 1 gap — "Real observation data — no actual telescope data has been ingested"
#
# Resume / restart behaviour:
#   - Download is split into parallel chunks (DEFAULT_CONNECTIONS=16 for gigabit wifi).
#   - Completed chunk files are stored under data/bl_hits/.chunks_voyager1.h5/ and
#     reused on restart — stop the script at any time with Ctrl+C and re-run.
#   - If the hit table (*.dat) already exists the entire script exits immediately.
#
# Fallback:
#   If all real-data URLs fail, a clearly-labelled synthetic H5 is built and run
#   through turboSETI for pipeline smoke-testing.  This does NOT close Tier 1.
#
# All logic (download, turboSETI) lives in scripts/bl_fetch.py.
# All Python is invoked via .venv/bin/python (Python 3.14.3, never system python3).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$REPO_ROOT/.venv/bin/python"
BL_FETCH="$REPO_ROOT/scripts/bl_fetch.py"
DATA_DIR="$REPO_ROOT/data/bl_hits"

mkdir -p "$DATA_DIR"

log() { echo "[$(date '+%Y-%m-%dT%H:%M:%S')] $*"; }

log "=== download_bl_hits.sh starting ==="
log "Repo root : $REPO_ROOT"
log "Python    : $("$VENV" --version 2>&1)"

# ---------------------------------------------------------------------------
# Install / verify required packages
# ---------------------------------------------------------------------------
log "Checking / installing turbo-seti, blimpy, h5py, numpy ..."
"$VENV" -m pip install --quiet "turbo-seti>=2.3" blimpy h5py numpy || {
  log "ERROR: pip install failed.  Check network access."
  exit 1
}
log "Package check passed."

# ---------------------------------------------------------------------------
# Idempotent: skip only if THIS script's real output file already exists.
# Synthetic fallback files (synthetic_*.dat) are intentionally ignored so
# they never block a real-data download attempt.
# ---------------------------------------------------------------------------
REAL_DAT="$DATA_DIR/voyager1_hits.dat"
if [[ -f "$REAL_DAT" ]]; then
  log "Hit table already exists: $REAL_DAT"
  log "Rows: $(grep -v '^#' "$REAL_DAT" | wc -l | tr -d ' ')"
  log "Delete it to re-run.  Exiting."
  exit 0
fi

# ---------------------------------------------------------------------------
# Option A: download real Voyager 1 H5 (resumable + parallel)
# ---------------------------------------------------------------------------
VOYAGER_H5="$DATA_DIR/voyager1.h5"
log "Option A: fetching real Voyager 1 H5 (16 parallel connections, resumable) ..."

if "$VENV" "$BL_FETCH" download-h5 "$VOYAGER_H5" --connections 16; then
  log "Option A: HDF5 download succeeded."
  log "Option A: running turboSETI ..."
  if "$VENV" "$BL_FETCH" run-turboseti "$VOYAGER_H5" "$DATA_DIR"; then
    # Predict the turboSETI output name deterministically from the H5 stem.
    # Using find|head -1 is wrong when pre-existing .dat files are present.
    H5_STEM="$(basename "$VOYAGER_H5" .h5)"
    FOUND_DAT="$DATA_DIR/${H5_STEM}.dat"
    REAL_DAT="$DATA_DIR/voyager1_hits.dat"
    if [[ -f "$FOUND_DAT" ]]; then
      [[ "$FOUND_DAT" != "$REAL_DAT" ]] && mv "$FOUND_DAT" "$REAL_DAT"
      rm -f "$VOYAGER_H5"
      log "Option A complete — REAL DATA."
      log "Hit table : $REAL_DAT"
      log "Rows      : $(grep -v '^#' "$REAL_DAT" | wc -l | tr -d ' ')"
      log ""
      log "TIER 1 STATUS: partial progress — real turboSETI output produced."
      log "NEXT STEP   : bash scripts/run_pipeline_on_bl_data.sh"
      exit 0
    fi
  fi
  log "turboSETI failed or produced no .dat file.  Falling back."
fi

# ---------------------------------------------------------------------------
# Option B: synthetic fallback (smoke-test only, does NOT close Tier 1)
# ---------------------------------------------------------------------------
log ""
log "Option B (synthetic — pipeline smoke-test ONLY, does NOT close Tier 1)."

SYN_H5="$DATA_DIR/synthetic_voyager.h5"
SYN_DAT="$DATA_DIR/synthetic_hits.dat"

log "Building synthetic H5 ..."
"$VENV" "$BL_FETCH" synthetic-h5 "$SYN_H5"

log "Running turboSETI on synthetic H5 ..."
"$VENV" "$BL_FETCH" run-turboseti "$SYN_H5" "$DATA_DIR"

FOUND_DAT=$(find "$DATA_DIR" -name "*.dat" | head -1)
if [[ -n "$FOUND_DAT" && "$FOUND_DAT" != "$SYN_DAT" ]]; then
  mv "$FOUND_DAT" "$SYN_DAT"
fi
rm -f "$SYN_H5"

log "Option B complete (SYNTHETIC — NOT real observation data)."
log "Hit table : $SYN_DAT"
log "Rows      : $(grep -v '^#' "$SYN_DAT" | wc -l | tr -d ' ')"
log ""
log "TIER 1 STATUS: gap NOT closed — real data required."
log "NEXT STEP    : bash scripts/run_pipeline_on_bl_data.sh (pipeline smoke-test)"
log "=== download_bl_hits.sh done ==="
