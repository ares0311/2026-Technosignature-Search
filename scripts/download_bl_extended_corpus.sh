#!/usr/bin/env bash
# download_bl_extended_corpus.sh
#
# Downloads additional BL Open Data Archive GBT HDF5 files from non-Cygnus sky
# regions to improve model generalizability across multiple telescope pointings,
# epochs, and galactic coordinates.  The current BL portal exposes these files
# through bldata.berkeley.edu links discovered from the official Open Data
# search page; older blpd0 precomputed .dat URL patterns are stale and must not
# be treated as usable DECISION-134 evidence.
#
# Targets selected to span galactic latitudes and RA ranges not covered by
# the Cygnus calibration corpus (HIP99427 etc.).  All downloads are
# reproducibility aids only — no hit constitutes a detection claim.
#
# Usage:
#   caffeinate -i bash scripts/download_bl_extended_corpus.sh
#   bash scripts/download_bl_extended_corpus.sh --dry-run
#
# Output: data/extended_corpus/<target_name>/<filename>.h5
#
# Scientific guardrail:
#   These files are calibration and generalisation aids.  No downloaded file or
#   derived hit table constitutes a technosignature detection or authorizes
#   external submission.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${REPO_ROOT}/data/extended_corpus"
MAX_TARGETS="${TECHNO_EXTENDED_CORPUS_MAX_TARGETS:-0}"
DRY_RUN=0

for arg in "$@"; do
  case "${arg}" in
    --dry-run)
      DRY_RUN=1
      ;;
    -h|--help)
      cat <<'EOF'
Usage: bash scripts/download_bl_extended_corpus.sh [--dry-run]

Downloads current Breakthrough Open Data HDF5 evidence inputs into:
  data/extended_corpus/<target>/

Environment:
  TECHNO_EXTENDED_CORPUS_MAX_TARGETS=N  Limit target count; 0 means all.

Scientific guardrail:
  Outputs are local calibration/generalisation aids only. They do not
  constitute detections or authorize external submission.
EOF
      exit 0
      ;;
    *)
      echo "[ERROR] Unknown argument: ${arg}" >&2
      exit 2
      ;;
  esac
done

# ---------------------------------------------------------------------------
# Target list: non-Cygnus GBT cadences from the BL Open Data Archive.
#
# These are from the BL GBT survey (MacMahon et al. 2018) covering
# galactic latitudes |b| > 0 and spanning multiple RA hours.
# ---------------------------------------------------------------------------

TARGETS=(
  "HIP17147"
  "HIP39826"
  "HIP66704"
  "HIP74981"
  "HIP82860"
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

log() { echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] $*" >&2; }

discover_hdf5_url() {
  local name="$1"
  local search_url="https://breakthroughinitiatives.org/opendatasearch?project=GBT&file_type=HDF5&target=${name}&search=Search&perPage=100"

  log "[INFO]  Discovering current BL archive URL for ${name}"
  log "[URL]   ${search_url}"

  local page
  if ! page="$(curl -fsSL --retry 3 --retry-delay 5 --location "${search_url}")"; then
    log "[WARN]  Discovery failed for ${name}"
    return 1
  fi

  local url
  url="$(
    printf '%s\n' "${page}" |
      grep -Eo 'https://bldata\.berkeley\.edu/[^"]+\.gpuspec\.0002\.h5' |
      head -1 || true
  )"
  if [[ -z "${url}" ]]; then
    url="$(
      printf '%s\n' "${page}" |
        grep -Eo 'https://bldata\.berkeley\.edu/[^"]+\.h5' |
        head -1 || true
    )"
  fi
  if [[ -z "${url}" ]]; then
    log "[WARN]  No current HDF5 download URL found for ${name}"
    return 1
  fi

  printf '%s\n' "${url}"
}

download_hdf5() {
  local name="$1"
  local url="$2"
  local target_dir="${OUT_DIR}/${name}"
  local filename
  filename="$(basename "${url}")"

  mkdir -p "${target_dir}"
  local out_path="${target_dir}/${filename}"

  if [[ -f "${out_path}" ]]; then
    log "[SKIP] Already downloaded: ${out_path} ($(du -sh "${out_path}" | cut -f1))"
    return 0
  fi

  log "[Step] Downloading ${name} -> ${filename}"
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
    return 1
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
log "[INFO]  Target limit: ${MAX_TARGETS:-0} (0 means all configured targets)"
log "[INFO]  Dry run: ${DRY_RUN}"
mkdir -p "${OUT_DIR}"

count=0
total=${#TARGETS[@]}
downloaded=0
skipped=0

for name in "${TARGETS[@]}"; do
  if [[ "${MAX_TARGETS}" != "0" && "${count}" -ge "${MAX_TARGETS}" ]]; then
    log "[INFO]  Target limit reached (${MAX_TARGETS}); stopping early"
    break
  fi
  count=$((count + 1))
  log "[${count}/${total}] Target: ${name}"
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    log "[DRY-RUN] Would discover and download current HDF5 evidence for ${name}"
    continue
  fi
  if url="$(discover_hdf5_url "${name}")" && download_hdf5 "${name}" "${url}"; then
    downloaded=$((downloaded + 1))
  else
    skipped=$((skipped + 1))
  fi
done

if [[ "${DRY_RUN}" -eq 1 ]]; then
  log "[DONE]  Dry run complete; no network download attempted."
  exit 0
fi

log "[DONE]  Extended corpus download complete"
log "[INFO]  Successful target downloads/reuses: ${downloaded}"
log "[INFO]  Skipped or failed targets: ${skipped}"
log "[INFO]  Files in ${OUT_DIR}:"
find "${OUT_DIR}" -name "*.h5" -exec du -sh {} \; 2>/dev/null || log "[INFO]  (none downloaded)"

if [[ "${downloaded}" -eq 0 ]]; then
  log "[ERROR] No held-out evidence files were downloaded or reused."
  log "[ERROR] DECISION-134 remains blocked; empty directories are not evidence."
  exit 1
fi

echo ""
echo "Scientific guardrail:"
echo "  These HDF5 files and any derived hit tables are calibration and"
echo "  generalisation aids only. No file or hit table entry constitutes a"
echo "  technosignature detection or authorizes external submission."
echo ""
echo "Next step: derive review-safe method-comparison artifacts from this"
echo "ignored local evidence stream, then re-run:"
echo "  .venv/bin/techno-search ai-hardening-gate-summary"
