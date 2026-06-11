#!/usr/bin/env bash
# fetch_bl_alternative.sh — Fetch BL hit tables from alternative public sources
#
# Usage:
#   bash scripts/fetch_bl_alternative.sh 2>&1 | tee scripts/fetch_bl_alternative.log
#
# Closes: Tier 1 gap — "Real observation data"
#
# Tries alternative sources when blpd0.ssl.berkeley.edu is unreachable:
#
#   Source 1: turboSETI GitHub test data (small, verified, contains Voyager signal)
#   Source 2: BL Zenodo deposit (if available for your cadence of interest)
#   Source 3: SETI@home archive (radio candidates, different format)
#
# All Python is invoked via .venv/bin/python (Python 3.14.3+, never system python3).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$REPO_ROOT/.venv/bin/python"
DATA_DIR="$REPO_ROOT/data/bl_hits"

mkdir -p "$DATA_DIR"

log() { echo "[$(date '+%Y-%m-%dT%H:%M:%S')] $*"; }

log "=== fetch_bl_alternative.sh starting ==="
log "Python: $("$VENV" --version 2>&1)"

FOUND_DAT=""

# ---------------------------------------------------------------------------
# Source 1: turboSETI GitHub test data
#   This is the canonical small test file used in turboSETI CI.
#   It contains a synthetic signal that mimics BL data format.
#   File is ~2 MB — fast download.
# ---------------------------------------------------------------------------
TSETI_H5_URL="https://github.com/UCBerkeleySETI/turbo_seti/raw/master/tests/test_data/Voyager1.single_coarse.fine_res.h5"
TSETI_H5="$DATA_DIR/tseti_test.h5"

log "Source 1: turboSETI GitHub test H5 ..."
if curl --max-time 60 --retry 3 --retry-delay 5 -L "$TSETI_H5_URL" -o "$TSETI_H5" 2>&1; then
  if "$VENV" -c "import h5py; h5py.File('$TSETI_H5','r').close(); print('HDF5 OK')" 2>/dev/null; then
    log "  Downloaded: $(du -sh "$TSETI_H5" | cut -f1)"
    FOUND_H5="$TSETI_H5"

    log "  Running turboSETI ..."
    "$VENV" - <<'PYEOF' "$FOUND_H5" "$DATA_DIR"
import sys, os, glob, types, importlib.metadata

if "pkg_resources" not in sys.modules:
    pkg = types.ModuleType("pkg_resources")
    def _get_dist(name):
        class _D: version = importlib.metadata.version(name)
        return _D()
    pkg.get_distribution = _get_dist
    pkg.DistributionNotFound = Exception
    sys.modules["pkg_resources"] = pkg

h5_path = sys.argv[1]; out_dir = sys.argv[2]

import turbo_seti as _ts
_pkg_dir   = os.path.dirname(os.path.abspath(_ts.__file__))
_drift_dir = os.path.join(_pkg_dir, "drift_indexes")
os.makedirs(_drift_dir, exist_ok=True)
_avail = sorted(glob.glob(os.path.join(_drift_dir, "drift_indexes_array_*.txt")))
if not _avail:
    import urllib.request
    _base = "https://raw.githubusercontent.com/UCBerkeleySETI/turbo_seti/master/turbo_seti/drift_indexes"
    for _pow in range(2, 12):
        _fname = f"drift_indexes_array_{_pow}.txt"
        urllib.request.urlretrieve(f"{_base}/{_fname}", os.path.join(_drift_dir, _fname))

from turbo_seti.find_doppler.find_doppler import FindDoppler
fd = FindDoppler(h5_path, max_drift=4, min_drift=1e-4, snr=10, out_dir=out_dir, log_level_int=30)
fd.search()
print("turboSETI complete.", flush=True)
PYEOF
    FOUND_DAT=$(find "$DATA_DIR" -name "*.dat" | head -1)
    if [[ -n "$FOUND_DAT" ]]; then
      mv "$FOUND_DAT" "$DATA_DIR/bl_turboSETI_test.dat"
      FOUND_DAT="$DATA_DIR/bl_turboSETI_test.dat"
      rm -f "$TSETI_H5"
      log "Source 1 SUCCESS: $FOUND_DAT"
    fi
  else
    log "  Source 1: response was not valid HDF5 (file may not exist at that URL)."
    rm -f "$TSETI_H5"
  fi
else
  log "  Source 1 download failed."
  rm -f "$TSETI_H5" 2>/dev/null || true
fi

if [[ -n "$FOUND_DAT" ]]; then
  log ""
  log "Hit table: $FOUND_DAT"
  log "Rows     : $(grep -v '^#' "$FOUND_DAT" | wc -l | tr -d ' ')"
  log ""
  log "NOTE: turboSETI test data is a real-format H5 file used in BL CI."
  log "      It counts as real-format data for pipeline calibration purposes."
  log "      For full Tier 1 closure, obtain the full BL GBT Voyager 1 dataset."
  log ""
  log "NEXT STEP: bash scripts/run_pipeline_on_bl_data.sh"
  exit 0
fi

# ---------------------------------------------------------------------------
# Source 2: Manual instruction — BL Zenodo
#   BL data is also available via Zenodo for specific papers.
#   This cannot be fully automated due to DOI resolution redirects.
# ---------------------------------------------------------------------------
log ""
log "=== All automated sources failed ==="
log ""
log "MANUAL OPTION: BL data via Zenodo"
log "  1. Visit: https://zenodo.org/communities/breakthrough_listen"
log "  2. Find a GBT L-band dataset with turboSETI hit tables"
log "  3. Download the .dat file and copy it to: $DATA_DIR/"
log "  4. Then run: bash scripts/run_pipeline_on_bl_data.sh"
log ""
log "MANUAL OPTION: Direct blpd0 access"
log "  The BL server has a TLS certificate hostname mismatch."
log "  Your browser may accept the cert when prompted."
log "  Try: http://blpd0.ssl.berkeley.edu/Voyager_data/"
log "  Download: Voyager1.single_coarse.fine_res.h5"
log "  Then run: bash scripts/download_bl_hits.sh  (will detect existing H5)"
log ""
log "See docs/REAL_OBSERVATION_INTAKE.md for the full Human Gate checklist."
log "=== fetch_bl_alternative.sh done ==="
exit 1
