#!/usr/bin/env bash
# download_bl_extended_corpus.sh
#
# Downloads additional BL Open Data Archive GBT cadence .dat files from
# non-Cygnus sky regions to improve model generalizability across multiple
# telescope pointings, epochs, and galactic coordinates.
#
# Targets selected to span galactic latitudes and RA ranges not covered by
# the Cygnus calibration corpus (HIP99427 etc.).  All downloads are
# reproducibility aids only — no hit constitutes a detection claim.
#
# Usage:
#   caffeinate -i bash scripts/download_bl_extended_corpus.sh
#
# Output: data/extended_corpus/<target_name>/<filename>.dat
#
# Scientific guardrail:
#   These files are calibration and generalisation aids.  No hit table entry
#   constitutes a technosignature detection or authorizes external submission.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${REPO_ROOT}/data/extended_corpus"
THREADS=8

# BL Open Data Archive HTTP root (uses public HTTPS; no auth required)
BL_BASE="https://blpd0.ssl.berkeley.edu"

# ---------------------------------------------------------------------------
# Target list: non-Cygnus GBT L-band cadences from BL archive
# Each entry: "<target_name> <dat_filename> <url_path>"
#
# These are from the BL GBT survey (MacMahon et al. 2018) covering
# galactic latitudes |b| > 0 and spanning multiple RA hours.
# ---------------------------------------------------------------------------

declare -A TARGETS
TARGETS=(
  ["HIP17147"]="HIP17147.dat https://blpd0.ssl.berkeley.edu/GBT_L_band/HIP17147/spliced_blc0001020304050607_guppi_57525_HIP17147_0001.gpuspec.0000.dat"
  ["HIP39826"]="HIP39826.dat https://blpd0.ssl.berkeley.edu/GBT_L_band/HIP39826/spliced_blc0001020304050607_guppi_57607_HIP39826_0001.gpuspec.0000.dat"
  ["HIP66704"]="HIP66704.dat https://blpd0.ssl.berkeley.edu/GBT_L_band/HIP66704/spliced_blc0001020304050607_guppi_57602_HIP66704_0001.gpuspec.0000.dat"
  ["HIP74981"]="HIP74981.dat https://blpd0.ssl.berkeley.edu/GBT_L_band/HIP74981/spliced_blc0001020304050607_guppi_57607_HIP74981_0001.gpuspec.0000.dat"
  ["HIP82860"]="HIP82860.dat https://blpd0.ssl.berkeley.edu/GBT_L_band/HIP82860/spliced_blc0001020304050607_guppi_57603_HIP82860_0001.gpuspec.0000.dat"
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

log() { echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] $*"; }

download_dat() {
  local name="$1"
  local filename="$2"
  local url="$3"
  local target_dir="${OUT_DIR}/${name}"

  mkdir -p "${target_dir}"
  local out_path="${target_dir}/${filename}"

  if [[ -f "${out_path}" ]]; then
    log "[SKIP] Already downloaded: ${out_path} ($(du -sh "${out_path}" | cut -f1))"
    return 0
  fi

  log "[Step] Downloading ${name} → ${filename}"
  log "[URL]  ${url}"

  # --continue-at - resumes partial downloads
  # --progress-bar shows speed + ETA
  # --retry 3 for transient failures
  curl --progress-bar \
       --continue-at - \
       --retry 3 \
       --retry-delay 5 \
       --location \
       --output "${out_path}" \
       "${url}" || {
    log "[WARN] Download failed for ${name} — skipping (URL may be unavailable)"
    rm -f "${out_path}"
    return 0
  }

  local size
  size="$(du -sh "${out_path}" 2>/dev/null | cut -f1 || echo 'unknown')"
  log "[OK]   Downloaded: ${out_path} (${size})"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

log "[START] BL extended corpus download"
log "[INFO]  Output directory: ${OUT_DIR}"
log "[INFO]  Thread count: ${THREADS}"
mkdir -p "${OUT_DIR}"

count=0
total=${#TARGETS[@]}

for name in "${!TARGETS[@]}"; do
  count=$((count + 1))
  IFS=' ' read -r filename url <<< "${TARGETS[$name]}"
  log "[${count}/${total}] Target: ${name}"
  download_dat "${name}" "${filename}" "${url}"
done

log "[DONE]  Extended corpus download complete"
log "[INFO]  Files in ${OUT_DIR}:"
find "${OUT_DIR}" -name "*.dat" -exec du -sh {} \; 2>/dev/null || log "[INFO]  (none downloaded)"

echo ""
echo "Scientific guardrail:"
echo "  These .dat files are calibration and generalisation aids only."
echo "  No hit table entry constitutes a technosignature detection or"
echo "  authorizes external submission."
echo ""
echo "Next step: run cross-band feature extraction against these files:"
echo "  .venv/bin/techno-search cross-band-features-summary"
