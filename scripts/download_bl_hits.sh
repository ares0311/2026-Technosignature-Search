#!/usr/bin/env bash
# download_bl_hits.sh — Download or synthesize a BL Voyager-1 hit table
#
# Usage:
#   caffeinate -i bash scripts/download_bl_hits.sh 2>&1 | tee scripts/download_bl_hits.log
#
# Closes: Tier 1 gap — "Real observation data — no actual telescope data has been ingested"
#
# The BL server (blpd0.ssl.berkeley.edu) has a TLS certificate hostname
# mismatch (their cert does not cover that subdomain).  This is a known
# misconfiguration on Berkeley's side; the data itself is authentic public
# scientific data.  We use -k / --insecure only for this specific host.
#
# Download strategy (tried in order):
#   1. HTTP (no TLS) from blpd0.ssl.berkeley.edu — avoids the cert issue entirely
#   2. HTTPS --insecure from blpd0.ssl.berkeley.edu — cert bypass for public data
#   3. Synthetic fallback — pipeline smoke-test only (does NOT close Tier 1)
#
# Real output  → data/bl_hits/voyager1_hits.dat
# Synthetic    → data/bl_hits/synthetic_hits.dat
#
# All Python is invoked via .venv/bin/python (never system python3).
# Python venv must be 3.14.3+ as documented in docs/LOCAL_SYSTEM_PROFILE.md.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$REPO_ROOT/.venv/bin/python"
DATA_DIR="$REPO_ROOT/data/bl_hits"
RESULTS_DIR="$REPO_ROOT/results"

mkdir -p "$DATA_DIR" "$RESULTS_DIR"

log() { echo "[$(date '+%Y-%m-%dT%H:%M:%S')] $*"; }

log "=== download_bl_hits.sh starting ==="
log "Repo root : $REPO_ROOT"
log "Python    : $("$VENV" --version 2>&1)"

# ---------------------------------------------------------------------------
# Install / verify required Python packages inside the venv
# ---------------------------------------------------------------------------
log "Checking / installing turbo-seti and blimpy inside .venv ..."
"$VENV" -m pip install --quiet "turbo-seti>=2.3" blimpy h5py numpy || {
  log "ERROR: pip install failed — check network access."
  exit 1
}
log "Package check passed."

# ---------------------------------------------------------------------------
# Voyager 1 H5 — the authentic BL public dataset
#   File : Voyager1.single_coarse.fine_res.h5  (~1.3 GB)
#   Note : blpd0.ssl.berkeley.edu TLS cert is misconfigured (hostname mismatch).
#          Use HTTP first; fall back to HTTPS -k if the server redirects.
# ---------------------------------------------------------------------------
VOYAGER_H5="$DATA_DIR/voyager1.h5"
REAL_DAT="$DATA_DIR/voyager1_hits.dat"
OPTION_A_OK=0

URL_HTTP="http://blpd0.ssl.berkeley.edu/Voyager_data/Voyager1.single_coarse.fine_res.h5"
URL_HTTPS="https://blpd0.ssl.berkeley.edu/Voyager_data/Voyager1.single_coarse.fine_res.h5"

try_download() {
  local url="$1"; shift
  local extra_flags=("$@")
  log "  Trying: $url"
  if curl "${extra_flags[@]}" --max-time 600 --retry 2 --retry-delay 10 \
          --progress-bar -L "$url" -o "$VOYAGER_H5" 2>&1; then
    # Verify it looks like an HDF5 file (starts with \x89HDF)
    if "$VENV" -c "import sys; d=open('$VOYAGER_H5','rb').read(4); sys.exit(0 if d==b'\\x89HDF' else 1)" 2>/dev/null; then
      log "  Downloaded and verified as HDF5: $(du -sh "$VOYAGER_H5" | cut -f1)"
      return 0
    else
      log "  File downloaded but is not a valid HDF5 (server may have returned HTML)."
      rm -f "$VOYAGER_H5"
      return 1
    fi
  fi
  rm -f "$VOYAGER_H5"
  return 1
}

log "Option A: downloading real Voyager 1 H5 from BL Open Data Archive ..."
if try_download "$URL_HTTP"; then
  OPTION_A_OK=1
elif try_download "$URL_HTTPS" -k; then
  log "  (Used --insecure because blpd0 TLS cert has hostname mismatch — data is authentic BL public release)"
  OPTION_A_OK=1
else
  log "  BL server unreachable or returned non-HDF5 data."
fi

if [[ $OPTION_A_OK -eq 1 ]]; then
  log "Option A: running turboSETI on real Voyager 1 H5 ..."
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

# Fix 4: drift_indexes lives at the turbo_seti package root, not find_doppler/
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
        print(f"  Downloading drift index: {_fname}", flush=True)
        urllib.request.urlretrieve(f"{_base}/{_fname}",
                                   os.path.join(_drift_dir, _fname))
    _avail = sorted(glob.glob(os.path.join(_drift_dir, "drift_indexes_array_*.txt")))

from turbo_seti.find_doppler.find_doppler import FindDoppler
fd = FindDoppler(h5_path, max_drift=4, min_drift=1e-4, snr=10,
                 out_dir=out_dir, log_level_int=30)
fd.search()
print("turboSETI search complete (real Voyager 1 file).", flush=True)
PYEOF

  FOUND_DAT=$(find "$DATA_DIR" -name "*.dat" | head -1)
  if [[ -n "$FOUND_DAT" && "$FOUND_DAT" != "$REAL_DAT" ]]; then
    mv "$FOUND_DAT" "$REAL_DAT"
  fi
  rm -f "$VOYAGER_H5"
  log "Option A complete."
  log "Hit table : $REAL_DAT"
  log "Rows      : $(grep -v '^#' "$REAL_DAT" | wc -l | tr -d ' ')"
  log ""
  log "NEXT STEP: bash scripts/run_pipeline_on_bl_data.sh"
  exit 0
fi

# ---------------------------------------------------------------------------
# Option B: Synthetic fallback — pipeline smoke-test ONLY
#   This does NOT close the Tier 1 gap.  It lets you verify the pipeline
#   is working while waiting for BL data access to be resolved.
# ---------------------------------------------------------------------------
log ""
log "Option B (synthetic fallback — pipeline smoke-test only)."
log "This does NOT close the Tier 1 gap; see Human Gate 1 in the plan."
log ""

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

# Synthetic GBT L-band parameters matching Voyager 1 single-coarse file
fch1    = 8421.386719      # MHz
foff    = -2.7939677e-6    # MHz/chan
tsamp   = 18.25361
n_chans = 65536
n_time  = 16               # Fix 5: minimum available drift_index power = 2^4

rng = np.random.default_rng(42)
data = rng.normal(loc=500.0, scale=20.0, size=(n_time, 1, n_chans)).astype(np.float32)

# Inject narrowband drifting signal at Voyager 1 carrier vicinity (~8421 MHz X-band)
signal_freq_mhz   = 8421.295
signal_chan        = int((signal_freq_mhz - fch1) / foff)
drift_chan_per_step = 0.38 * tsamp / (abs(foff) * 1e6)
for t in range(n_time):
    chan = int(signal_chan + t * drift_chan_per_step)
    if 0 <= chan < n_chans:
        data[t, 0, chan] += 1500.0

# Fix 3: write ALL header fields to the DATA DATASET attrs, not root group
with h5py.File(out_h5, "w") as f:
    f.attrs["CLASS"]   = "FILTERBANK"
    f.attrs["VERSION"] = "1.0"
    ds = f.create_dataset("data", data=data, compression="lzf")
    ds.dims[0].label = b"time"
    ds.dims[1].label = b"feed_id"
    ds.dims[2].label = b"frequency"
    for k, v in [
        ("fch1", np.float64(fch1)), ("foff", np.float64(foff)),
        ("tsamp", np.float64(tsamp)), ("tstart", np.float64(59046.92634259259)),
        ("nchans", np.int64(n_chans)), ("nifs", np.int64(1)),
        ("nbits", np.int64(32)), ("data_type", np.int64(1)),
        ("machine_id", np.int64(20)), ("telescope_id", np.int64(6)),
        ("source_name", np.bytes_("SYNTH_BL_TIER1")),
        ("rawdatafile", np.bytes_("")),
        ("az_start", np.float64(0.0)), ("za_start", np.float64(0.0)),
        ("src_raj", np.float64(17.2112447222)), ("src_dej", np.float64(12.4037816667)),
    ]:
        ds.attrs[k] = v

print(f"Synthetic H5: {out_h5}  shape={data.shape}", flush=True)

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
        print(f"  Downloading drift index: {_fname}", flush=True)
        urllib.request.urlretrieve(f"{_base}/{_fname}",
                                   os.path.join(_drift_dir, _fname))

from turbo_seti.find_doppler.find_doppler import FindDoppler
fd = FindDoppler(out_h5, max_drift=4, min_drift=1e-4, snr=10,
                 out_dir=out_dir, log_level_int=30)
fd.search()
print("turboSETI complete (synthetic fallback).", flush=True)
PYEOF

FOUND_DAT=$(find "$DATA_DIR" -name "*.dat" | grep -v voyager1_hits | head -1)
if [[ -n "$FOUND_DAT" && "$FOUND_DAT" != "$SYN_DAT" ]]; then
  mv "$FOUND_DAT" "$SYN_DAT"
fi
rm -f "$SYN_H5"

log "Option B complete (SYNTHETIC — not real observation data)."
log "Hit table : $SYN_DAT"
log "Rows      : $(grep -v '^#' "$SYN_DAT" | wc -l | tr -d ' ')"
log ""
log "TIER 1 STATUS: gap NOT closed — synthetic data cannot substitute for real observations."
log "To close Tier 1, you must obtain real BL hit tables."
log "See scripts/fetch_bl_alternative.sh (coming soon) for alternative download sources."
log ""
log "NEXT STEP: bash scripts/run_pipeline_on_bl_data.sh  (pipeline smoke-test)"
log "=== download_bl_hits.sh done ==="
