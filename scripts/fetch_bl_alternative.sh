#!/usr/bin/env bash
# fetch_bl_alternative.sh — Fetch BL hit tables from alternative public sources
#
# Usage:
#   bash scripts/fetch_bl_alternative.sh 2>&1 | tee scripts/fetch_bl_alternative.log
#
# Closes: Tier 1 gap — "Real observation data"
#
# Resume / restart behaviour:
#   Identical to download_bl_hits.sh — downloads split into 16 parallel chunks
#   stored under data/bl_hits/.chunks_*/.  Stop and restart at any time.
#   If a valid hit table already exists the script exits immediately.
#
# Sources tried in order:
#   1. turboSETI GitHub test data (verified real-format H5, used in BL CI)
#   2. GitHub LFS media URL (same file via alternate CDN)
#   3. BL Open Data Archive HTTP direct
#
# All logic lives in scripts/bl_fetch.py.
# All Python is invoked via .venv/bin/python (Python 3.14.3, never system python3).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$REPO_ROOT/.venv/bin/python"
BL_FETCH="$REPO_ROOT/scripts/bl_fetch.py"
DATA_DIR="$REPO_ROOT/data/bl_hits"

mkdir -p "$DATA_DIR"

log() { echo "[$(date '+%Y-%m-%dT%H:%M:%S')] $*"; }

log "=== fetch_bl_alternative.sh starting ==="
log "Python: $("$VENV" --version 2>&1)"

# ---------------------------------------------------------------------------
# Idempotent: skip if a hit table already exists
# ---------------------------------------------------------------------------
EXISTING_DAT=$(find "$DATA_DIR" -name "*.dat" 2>/dev/null | head -1)
if [[ -n "$EXISTING_DAT" ]]; then
  log "Hit table already exists: $EXISTING_DAT"
  log "Rows: $(grep -v '^#' "$EXISTING_DAT" | wc -l | tr -d ' ')"
  log "Delete it to re-run.  Exiting."
  exit 0
fi

# ---------------------------------------------------------------------------
# Install required packages
# ---------------------------------------------------------------------------
log "Checking / installing turbo-seti, blimpy, h5py, numpy ..."
"$VENV" -m pip install --quiet "turbo-seti>=2.3" blimpy h5py numpy || {
  log "ERROR: pip install failed."
  exit 1
}

# ---------------------------------------------------------------------------
# Attempt download from alternative sources (resumable + parallel)
# ---------------------------------------------------------------------------
TSETI_H5="$DATA_DIR/tseti_test.h5"

log "Trying turboSETI GitHub test data (16 parallel connections, resumable) ..."
if "$VENV" "$BL_FETCH" download-h5 "$TSETI_H5" \
     --connections 16 \
     --url "https://github.com/UCBerkeleySETI/turbo_seti/raw/master/tests/test_data/Voyager1.single_coarse.fine_res.h5" \
     --url "https://media.githubusercontent.com/media/UCBerkeleySETI/turbo_seti/master/tests/test_data/Voyager1.single_coarse.fine_res.h5" \
     --url "http://blpd0.ssl.berkeley.edu/Voyager_data/Voyager1.single_coarse.fine_res.h5"; then

  log "Download succeeded.  Running turboSETI ..."
  if "$VENV" "$BL_FETCH" run-turboseti "$TSETI_H5" "$DATA_DIR"; then
    FOUND_DAT=$(find "$DATA_DIR" -name "*.dat" | head -1)
    if [[ -n "$FOUND_DAT" ]]; then
      FINAL_DAT="$DATA_DIR/bl_turboSETI_test.dat"
      [[ "$FOUND_DAT" != "$FINAL_DAT" ]] && mv "$FOUND_DAT" "$FINAL_DAT"
      rm -f "$TSETI_H5"
      log ""
      log "Hit table: $FINAL_DAT"
      log "Rows     : $(grep -v '^#' "$FINAL_DAT" | wc -l | tr -d ' ')"
      log ""
      log "NOTE: turboSETI test H5 is a real-format file used in BL CI."
      log "      It is valid for pipeline calibration."
      log "      For full Tier 1 closure, obtain the full BL GBT Voyager 1 dataset."
      log ""
      log "NEXT STEP: bash scripts/run_pipeline_on_bl_data.sh"
      exit 0
    fi
  fi
fi

# ---------------------------------------------------------------------------
# All automated sources failed — print manual instructions
# ---------------------------------------------------------------------------
log ""
log "=== All automated download attempts failed ==="
log ""
log "MANUAL OPTION A — BL data via browser:"
log "  1. Open in your browser: http://blpd0.ssl.berkeley.edu/Voyager_data/"
log "  2. Download: Voyager1.single_coarse.fine_res.h5"
log "  3. Copy to: $DATA_DIR/voyager1.h5"
log "  4. Run: bash scripts/download_bl_hits.sh"
log ""
log "MANUAL OPTION B — turboSETI GitHub test file via browser:"
log "  1. Open: https://github.com/UCBerkeleySETI/turbo_seti/raw/master/tests/test_data/Voyager1.single_coarse.fine_res.h5"
log "  2. Copy to: $DATA_DIR/voyager1.h5"
log "  3. Run: bash scripts/download_bl_hits.sh"
log ""
log "See docs/REAL_OBSERVATION_INTAKE.md for the full Human Gate checklist."
log "=== fetch_bl_alternative.sh done ==="
exit 1
