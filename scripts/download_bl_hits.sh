#!/usr/bin/env bash
# download_bl_hits.sh — Download or synthesize a BL Voyager-1 hit table
#
# Usage:
#   caffeinate -i bash scripts/download_bl_hits.sh 2>&1 | tee scripts/download_bl_hits.log
#
# Closes: Tier 1 gap — "Real observation data — no actual telescope data has been ingested"
#
# What this script does:
#   Option A (attempted first): Download the Voyager 1 H5 file from the BL Open Data
#              Archive, run turboSETI on it, and write a real .dat hit table.
#   Option B (fallback): Build a synthetic .h5 filterbank with an injected narrowband
#              signal at ~8421.295 MHz (Voyager 1 carrier vicinity), run turboSETI,
#              write a .dat hit table that the pipeline can ingest.
#
# The .dat hit table will be written to:
#   data/bl_hits/voyager1_hits.dat        (Option A, real)
#   data/bl_hits/synthetic_hits.dat       (Option B, fallback)
#
# Requirements (inside .venv):
#   pip install turbo-seti blimpy h5py numpy
#
# All Python is invoked via .venv/bin/python (never system python3).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG="$REPO_ROOT/scripts/download_bl_hits.log"
VENV="$REPO_ROOT/.venv/bin/python"
DATA_DIR="$REPO_ROOT/data/bl_hits"
RESULTS_DIR="$REPO_ROOT/results"

mkdir -p "$DATA_DIR" "$RESULTS_DIR"

log() { echo "[$(date '+%Y-%m-%dT%H:%M:%S')] $*"; }

log "=== download_bl_hits.sh starting ==="
log "Repo root : $REPO_ROOT"
log "Python    : $("$VENV" --version 2>&1)"
log "Data dir  : $DATA_DIR"

# ---------------------------------------------------------------------------
# Install / verify required Python packages inside the venv
# ---------------------------------------------------------------------------
log "Checking / installing turbo-seti and blimpy inside .venv ..."
"$VENV" -m pip install --quiet "turbo-seti>=2.3" blimpy h5py numpy || {
  log "ERROR: pip install failed — check network access and re-run."
  exit 1
}
log "Package check passed."

# ---------------------------------------------------------------------------
# Option A: try to download the real Voyager 1 filterbank from BL archive
# ---------------------------------------------------------------------------
VOYAGER_URL="http://blpd0.ssl.berkeley.edu/Voyager_data/Voyager1.single_coarse.fine_res.h5"
VOYAGER_H5="$DATA_DIR/voyager1.h5"
REAL_DAT="$DATA_DIR/voyager1_hits.dat"
OPTION_A_OK=0

log "Option A: attempting to download Voyager 1 H5 from BL archive ..."
log "  URL: $VOYAGER_URL"

if curl --max-time 120 --retry 3 --retry-delay 5 \
        --progress-bar -L "$VOYAGER_URL" -o "$VOYAGER_H5" 2>&1; then
  log "Download succeeded: $(du -sh "$VOYAGER_H5" | cut -f1)"
  OPTION_A_OK=1
else
  log "Download failed (network unavailable or rate-limited — this is expected in CI)."
  rm -f "$VOYAGER_H5"
fi

if [[ $OPTION_A_OK -eq 1 ]]; then
  log "Option A: running turboSETI on real Voyager 1 file ..."
  "$VENV" - <<'PYEOF' "$VOYAGER_H5" "$DATA_DIR"
import sys, os, glob, types, importlib.metadata

# Fix 1: pkg_resources shim for Python 3.13+
if "pkg_resources" not in sys.modules:
    pkg = types.ModuleType("pkg_resources")
    def _get_dist(name):
        class _D: version = importlib.metadata.version(name)
        return _D()
    pkg.get_distribution = _get_dist
    pkg.DistributionNotFound = Exception
    sys.modules["pkg_resources"] = pkg

h5_path = sys.argv[1]
out_dir  = sys.argv[2]

# Fix 4: resolve drift_indexes via the package root (not find_doppler/)
import turbo_seti as _ts
_pkg_dir   = os.path.dirname(os.path.abspath(_ts.__file__))
_drift_dir = os.path.join(_pkg_dir, "drift_indexes")
os.makedirs(_drift_dir, exist_ok=True)

# Fix 2: download drift_indexes text files from GitHub if absent
_avail = sorted(glob.glob(os.path.join(_drift_dir, "drift_indexes_array_*.txt")))
if not _avail:
    import urllib.request
    _base = "https://raw.githubusercontent.com/UCBerkeleySETI/turbo_seti/master/turbo_seti/drift_indexes"
    for _pow in range(2, 12):
        _fname = f"drift_indexes_array_{_pow}.txt"
        _dest  = os.path.join(_drift_dir, _fname)
        print(f"  Downloading drift index: {_fname}", flush=True)
        urllib.request.urlretrieve(f"{_base}/{_fname}", _dest)
    _avail = sorted(glob.glob(os.path.join(_drift_dir, "drift_indexes_array_*.txt")))

from turbo_seti.find_doppler.find_doppler import FindDoppler
fd = FindDoppler(h5_path, max_drift=4, min_drift=1e-4, snr=10,
                 out_dir=out_dir, log_level_int=30)
fd.search()
print("turboSETI complete (real file).", flush=True)
PYEOF
  # Rename .dat to canonical output name
  FOUND_DAT=$(find "$DATA_DIR" -name "*.dat" | head -1)
  if [[ -n "$FOUND_DAT" && "$FOUND_DAT" != "$REAL_DAT" ]]; then
    mv "$FOUND_DAT" "$REAL_DAT"
  fi
  rm -f "$VOYAGER_H5"
  log "Option A complete. Hit table: $REAL_DAT"
  log "Line count: $(wc -l < "$REAL_DAT")"
  exit 0
fi

# ---------------------------------------------------------------------------
# Option B: Synthetic fallback — inject a Voyager-like narrowband signal
# ---------------------------------------------------------------------------
log "Option B: building synthetic filterbank with injected narrowband signal ..."

SYN_H5="$DATA_DIR/synthetic_voyager.h5"
SYN_DAT="$DATA_DIR/synthetic_hits.dat"

"$VENV" - <<'PYEOF' "$SYN_H5" "$DATA_DIR"
import sys, os, glob, types, importlib.metadata, numpy as np

# Fix 1: pkg_resources shim for Python 3.13+
if "pkg_resources" not in sys.modules:
    pkg = types.ModuleType("pkg_resources")
    def _get_dist(name):
        class _D: version = importlib.metadata.version(name)
        return _D()
    pkg.get_distribution = _get_dist
    pkg.DistributionNotFound = Exception
    sys.modules["pkg_resources"] = pkg

import h5py

out_h5  = sys.argv[1]
out_dir = sys.argv[2]

# Synthetic GBT L-band parameters (coarse channel ~8421 MHz)
fch1    = 8421.386719      # MHz  — first channel frequency
foff    = -2.7939677e-6    # MHz/chan
tsamp   = 18.25361         # seconds
n_chans = 65536
n_time  = 16               # Fix 5: use minimum available drift_index power (2^4=16)

rng = np.random.default_rng(42)
data = rng.normal(loc=500.0, scale=20.0, size=(n_time, 1, n_chans)).astype(np.float32)

# Inject narrowband drifting signal at Voyager 1 carrier vicinity
# Real Voyager 1 carrier is ~8420.2 MHz; offset to avoid exact BL channels
signal_freq_mhz = 8421.295  # MHz
signal_chan = int((signal_freq_mhz - fch1) / foff)
drift_rate_hz_per_s = 0.38  # Hz/s (Voyager 1 drift)
drift_chan_per_step = drift_rate_hz_per_s * tsamp / (abs(foff) * 1e6)

for t in range(n_time):
    chan = int(signal_chan + t * drift_chan_per_step)
    if 0 <= chan < n_chans:
        data[t, 0, chan] += 1500.0  # SNR ~ 75

# Fix 3: blimpy reads ALL headers from dataset attrs, NOT root group attrs
with h5py.File(out_h5, "w") as f:
    f.attrs["CLASS"]   = "FILTERBANK"
    f.attrs["VERSION"] = "1.0"
    ds = f.create_dataset("data", data=data, compression="lzf")
    ds.dims[0].label = b"time"
    ds.dims[1].label = b"feed_id"
    ds.dims[2].label = b"frequency"
    ds.attrs["fch1"]         = np.float64(fch1)
    ds.attrs["foff"]         = np.float64(foff)
    ds.attrs["tsamp"]        = np.float64(tsamp)
    ds.attrs["tstart"]       = np.float64(59046.92634259259)
    ds.attrs["nchans"]       = np.int64(n_chans)
    ds.attrs["nifs"]         = np.int64(1)
    ds.attrs["nbits"]        = np.int64(32)
    ds.attrs["data_type"]    = np.int64(1)
    ds.attrs["machine_id"]   = np.int64(20)
    ds.attrs["telescope_id"] = np.int64(6)
    ds.attrs["source_name"]  = np.bytes_("SYNTH_BL_TIER1")
    ds.attrs["rawdatafile"]  = np.bytes_("")
    ds.attrs["az_start"]     = np.float64(0.0)
    ds.attrs["za_start"]     = np.float64(0.0)
    ds.attrs["src_raj"]      = np.float64(17.2112447222)
    ds.attrs["src_dej"]      = np.float64(12.4037816667)

print(f"Synthetic H5 written: {out_h5}  shape={data.shape}", flush=True)

# Fix 4 + Fix 2: resolve and populate drift_indexes
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
        _dest  = os.path.join(_drift_dir, _fname)
        print(f"  Downloading drift index: {_fname}", flush=True)
        urllib.request.urlretrieve(f"{_base}/{_fname}", _dest)

from turbo_seti.find_doppler.find_doppler import FindDoppler
fd = FindDoppler(out_h5, max_drift=4, min_drift=1e-4, snr=10,
                 out_dir=out_dir, log_level_int=30)
fd.search()
print("turboSETI complete (synthetic).", flush=True)
PYEOF

# Rename to canonical name
FOUND_DAT=$(find "$DATA_DIR" -name "*.dat" | grep -v voyager1_hits | head -1)
if [[ -n "$FOUND_DAT" && "$FOUND_DAT" != "$SYN_DAT" ]]; then
  mv "$FOUND_DAT" "$SYN_DAT"
fi
rm -f "$SYN_H5"
log "Option B complete."
log "Hit table: $SYN_DAT"
log "Line count: $(wc -l < "$SYN_DAT")"

# Print first few data lines (skip comments)
log "--- First 5 data lines ---"
grep -v "^#" "$SYN_DAT" | head -5 || true

log "=== download_bl_hits.sh done ==="
log "Next step: bash scripts/run_pipeline_on_bl_data.sh"
