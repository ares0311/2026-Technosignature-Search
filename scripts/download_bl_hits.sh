#!/usr/bin/env bash
# download_bl_hits.sh — Download or synthesize a BL Voyager-1 hit table
#
# Usage:
#   caffeinate -i bash scripts/download_bl_hits.sh 2>&1 | tee scripts/download_bl_hits.log
#
# Closes: Tier 1 gap — "Real observation data — no actual telescope data has been ingested"
#
# Root causes fixed (6 total):
#   Fix 1: pkg_resources shim for Python 3.13+ (get_distribution)
#   Fix 2: drift_indexes auto-download from GitHub if absent
#   Fix 3: blimpy reads ALL headers from ds.attrs (dataset), NOT f.attrs (root)
#   Fix 4: drift_indexes path resolves via turbo_seti package root
#   Fix 5: n_time set to minimum available drift_index power
#   Fix 6: resource_filename added to pkg_resources shim (Python 3.14 regression)
#
# Download strategy (tried in order):
#   A1. turboSETI GitHub test data — canonical BL Voyager file used in BL CI
#   A2. BL Open Data Archive (HTTP) — blpd0.ssl.berkeley.edu
#   A3. BL Open Data Archive (HTTPS -k) — cert bypass for Berkeley's misconfigured cert
#   B.  Synthetic fallback — pipeline smoke-test ONLY, does NOT close Tier 1
#
# All Python is invoked via .venv/bin/python (Python 3.14.3+, never system python3).

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
# Helper: verify a downloaded file is a real HDF5
# ---------------------------------------------------------------------------
is_hdf5() {
  local f="$1"
  [[ -f "$f" ]] || return 1
  local magic
  magic="$("$VENV" -c "import sys; d=open('$f','rb').read(4); sys.exit(0 if d==b'\x89HDF' else 1)" 2>/dev/null && echo ok || echo fail)"
  [[ "$magic" == "ok" ]]
}

# ---------------------------------------------------------------------------
# The Python heredoc used for both Option A and Option B turboSETI runs.
# All 6 root-cause fixes are embedded here.
# ---------------------------------------------------------------------------
run_turboseti() {
  local h5="$1"
  local out="$2"
  "$VENV" - <<PYEOF "$h5" "$out"
import sys, os, glob, types, importlib.metadata, importlib.util

# ── Fix 1 + Fix 6: complete pkg_resources shim for Python 3.13+ ──────────────
if "pkg_resources" not in sys.modules:
    pkg = types.ModuleType("pkg_resources")

    def _get_dist(name):
        class _D: version = importlib.metadata.version(name)
        return _D()
    pkg.get_distribution = _get_dist
    pkg.DistributionNotFound = Exception

    def _resource_filename(package_name, resource_name):
        """Fix 6: return filesystem path for an in-package resource."""
        if not isinstance(package_name, str):
            package_name = getattr(package_name, "__name__", str(package_name))
        top = package_name.split(".")[0]
        spec = importlib.util.find_spec(top)
        if spec and spec.submodule_search_locations:
            base = list(spec.submodule_search_locations)[0]
            return os.path.join(base, resource_name.replace("/", os.sep).lstrip(os.sep))
        return resource_name

    pkg.resource_filename = _resource_filename
    pkg.resource_stream   = None   # not needed by turboSETI
    sys.modules["pkg_resources"] = pkg
# ─────────────────────────────────────────────────────────────────────────────

h5_path = sys.argv[1]
out_dir  = sys.argv[2]

# Fix 4: drift_indexes lives at the turbo_seti package root
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
        urllib.request.urlretrieve(f"{_base}/{_fname}", os.path.join(_drift_dir, _fname))
    _avail = sorted(glob.glob(os.path.join(_drift_dir, "drift_indexes_array_*.txt")))

from turbo_seti.find_doppler.find_doppler import FindDoppler
fd = FindDoppler(h5_path, max_drift=4, min_drift=1e-4, snr=10,
                 out_dir=out_dir, log_level_int=30)
fd.search()
print("turboSETI search complete.", flush=True)
PYEOF
}

# ---------------------------------------------------------------------------
# Option A: download real Voyager 1 H5 and run turboSETI
# ---------------------------------------------------------------------------
VOYAGER_H5="$DATA_DIR/voyager1.h5"
REAL_DAT="$DATA_DIR/voyager1_hits.dat"
OPTION_A_OK=0

# URL list in priority order.
# A1: turboSETI GitHub test data — the canonical BL Voyager file used in BL CI.
#     This is the same file; size ~4 MB.
# A2: BL Open Data Archive via HTTP (avoids cert issue)
# A3: BL Open Data Archive via HTTPS -k (bypass Berkeley's misconfigured cert)
declare -a URLS=(
  "https://github.com/UCBerkeleySETI/turbo_seti/raw/master/tests/test_data/Voyager1.single_coarse.fine_res.h5"
  "https://media.githubusercontent.com/media/UCBerkeleySETI/turbo_seti/master/tests/test_data/Voyager1.single_coarse.fine_res.h5"
  "http://blpd0.ssl.berkeley.edu/Voyager_data/Voyager1.single_coarse.fine_res.h5"
)

log "Option A: fetching real Voyager 1 H5 ..."
for URL in "${URLS[@]}"; do
  log "  Trying: $URL"
  rm -f "$VOYAGER_H5"
  if curl -k --max-time 120 --retry 2 --retry-delay 5 --progress-bar -L "$URL" -o "$VOYAGER_H5" 2>&1; then
    if is_hdf5 "$VOYAGER_H5"; then
      log "  Valid HDF5: $(du -sh "$VOYAGER_H5" | cut -f1)"
      OPTION_A_OK=1
      break
    else
      log "  Response was not HDF5 (server returned HTML/redirect)."
    fi
  else
    log "  curl failed."
  fi
  rm -f "$VOYAGER_H5"
done

if [[ $OPTION_A_OK -eq 1 ]]; then
  log "Option A: running turboSETI on real Voyager 1 H5 ..."
  run_turboseti "$VOYAGER_H5" "$DATA_DIR"
  FOUND_DAT=$(find "$DATA_DIR" -name "*.dat" | head -1)
  [[ -n "$FOUND_DAT" && "$FOUND_DAT" != "$REAL_DAT" ]] && mv "$FOUND_DAT" "$REAL_DAT"
  rm -f "$VOYAGER_H5"
  log "Option A complete — REAL DATA."
  log "Hit table : $REAL_DAT"
  log "Rows      : $(grep -v '^#' "$REAL_DAT" | wc -l | tr -d ' ')"
  log ""
  log "TIER 1 STATUS: partial progress — real turboSETI output ingested."
  log "NEXT STEP: bash scripts/run_pipeline_on_bl_data.sh"
  exit 0
fi

# ---------------------------------------------------------------------------
# Option B: Synthetic fallback — pipeline smoke-test ONLY
# ---------------------------------------------------------------------------
log ""
log "Option B (synthetic — pipeline smoke-test only, does NOT close Tier 1)."

SYN_H5="$DATA_DIR/synthetic_voyager.h5"
SYN_DAT="$DATA_DIR/synthetic_hits.dat"

"$VENV" - <<PYEOF "$SYN_H5"
import sys, os, types, importlib.metadata, importlib.util, numpy as np

# Fix 1 + Fix 6: complete pkg_resources shim
if "pkg_resources" not in sys.modules:
    pkg = types.ModuleType("pkg_resources")
    def _get_dist(n):
        class _D: version = importlib.metadata.version(n)
        return _D()
    pkg.get_distribution = _get_dist
    pkg.DistributionNotFound = Exception
    def _resource_filename(pn, rn):
        if not isinstance(pn, str): pn = getattr(pn, "__name__", str(pn))
        spec = importlib.util.find_spec(pn.split(".")[0])
        if spec and spec.submodule_search_locations:
            base = list(spec.submodule_search_locations)[0]
            return os.path.join(base, rn.replace("/", os.sep).lstrip(os.sep))
        return rn
    pkg.resource_filename = _resource_filename
    pkg.resource_stream = None
    sys.modules["pkg_resources"] = pkg

import h5py

out_h5 = sys.argv[1]
fch1, foff, tsamp = 8421.386719, -2.7939677e-6, 18.25361
n_chans, n_time = 65536, 16  # Fix 5: minimum drift_index power = 2^4

rng  = np.random.default_rng(42)
data = rng.normal(500.0, 20.0, (n_time, 1, n_chans)).astype(np.float32)

# Inject narrowband drifting signal (Voyager 1 X-band carrier vicinity)
sig_chan = int((8421.295 - fch1) / foff)
drift_cp = 0.38 * tsamp / (abs(foff) * 1e6)
for t in range(n_time):
    c = int(sig_chan + t * drift_cp)
    if 0 <= c < n_chans:
        data[t, 0, c] += 1500.0

# Fix 3: ALL headers on ds.attrs (dataset), NOT f.attrs (root group)
with h5py.File(out_h5, "w") as f:
    f.attrs["CLASS"] = "FILTERBANK"; f.attrs["VERSION"] = "1.0"
    ds = f.create_dataset("data", data=data, compression="lzf")
    ds.dims[0].label = b"time"; ds.dims[1].label = b"feed_id"; ds.dims[2].label = b"frequency"
    for k, v in [("fch1",np.float64(fch1)),("foff",np.float64(foff)),
                 ("tsamp",np.float64(tsamp)),("tstart",np.float64(59046.9263)),
                 ("nchans",np.int64(n_chans)),("nifs",np.int64(1)),
                 ("nbits",np.int64(32)),("data_type",np.int64(1)),
                 ("machine_id",np.int64(20)),("telescope_id",np.int64(6)),
                 ("source_name",np.bytes_("SYNTH_BL_TIER1")),
                 ("rawdatafile",np.bytes_("")),("az_start",np.float64(0.0)),
                 ("za_start",np.float64(0.0)),("src_raj",np.float64(17.2112)),
                 ("src_dej",np.float64(12.4038))]:
        ds.attrs[k] = v
print(f"Synthetic H5: {out_h5}  shape={data.shape}", flush=True)
PYEOF

run_turboseti "$SYN_H5" "$DATA_DIR"
FOUND_DAT=$(find "$DATA_DIR" -name "*.dat" | grep -v voyager1_hits | head -1)
[[ -n "$FOUND_DAT" && "$FOUND_DAT" != "$SYN_DAT" ]] && mv "$FOUND_DAT" "$SYN_DAT"
rm -f "$SYN_H5"

log "Option B complete (SYNTHETIC — NOT real observation data)."
log "Hit table : $SYN_DAT"
log "Rows      : $(grep -v '^#' "$SYN_DAT" | wc -l | tr -d ' ')"
log ""
log "TIER 1 STATUS: gap NOT closed — real data required."
log "NEXT STEP: bash scripts/run_pipeline_on_bl_data.sh  (pipeline smoke-test)"
log "=== download_bl_hits.sh done ==="
