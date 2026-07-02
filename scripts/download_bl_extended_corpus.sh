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
#   caffeinate -i bash scripts/download_bl_extended_corpus.sh \
#       --manifest data/target_sample_manifest.json
#   bash scripts/download_bl_extended_corpus.sh --dry-run
#   bash scripts/download_bl_extended_corpus.sh --discover-only \
#       --manifest data/target_sample_manifest.json
#   bash scripts/download_bl_extended_corpus.sh --discover-only \
#       --availability-output /tmp/bl_hdf5_availability.tsv
#
# Output: data/extended_corpus/<target_name>/<filename>.h5
#
# Scientific guardrail:
#   These files are calibration and generalisation aids.  No downloaded file or
#   derived hit table constitutes a technosignature detection or authorizes
#   external submission.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${TECHNO_EXTENDED_CORPUS_OUT_DIR:-${REPO_ROOT}/data/extended_corpus}"
VENV_PYTHON="${TECHNO_EXTENDED_CORPUS_PYTHON:-${REPO_ROOT}/.venv/bin/python}"
MANIFEST="${REPO_ROOT}/data/target_sample_manifest.json"
MAX_TARGETS="${TECHNO_EXTENDED_CORPUS_MAX_TARGETS:-0}"
DRY_RUN=0
DISCOVER_ONLY=0
AVAILABILITY_OUTPUT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --discover-only|--availability-report)
      DISCOVER_ONLY=1
      shift
      ;;
    --manifest)
      MANIFEST="$2"
      shift 2
      ;;
    --availability-output)
      AVAILABILITY_OUTPUT="$2"
      shift 2
      ;;
    -h|--help)
      cat <<'EOF'
Usage: bash scripts/download_bl_extended_corpus.sh [--manifest PATH] [--dry-run] [--discover-only] [--availability-output PATH]

Downloads current Breakthrough Open Data HDF5 evidence inputs into:
  data/extended_corpus/<target>/

Environment:
  TECHNO_EXTENDED_CORPUS_MAX_TARGETS=N  Limit new URL-available downloads;
                                        existing HDF5 evidence is reused without
                                        consuming the limit. 0 means all
                                        available manifest targets.
  TECHNO_EXTENDED_CORPUS_OUT_DIR=PATH   Override output directory for tests or
                                        isolated local runs.

Options:
  --manifest PATH  Stratified target manifest JSON. Default:
                   data/target_sample_manifest.json
  --dry-run        Enumerate manifest targets without network access.
  --discover-only  Query BL search pages and print target<TAB>URL rows for
                   URL-available HDF5 records without downloading payloads.
  --availability-output PATH
                   Write URL-available target<TAB>URL rows to PATH. Use with
                   --discover-only for a durable, verified availability map.

Scientific guardrail:
  Outputs are local calibration/generalisation aids only. They do not
  constitute detections or authorize external submission.
EOF
      exit 0
      ;;
    *)
      echo "[ERROR] Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

# ---------------------------------------------------------------------------
# Fallback target list: pre-DECISION-143 non-Cygnus GBT cadences from the BL
# Open Data Archive. Production runs should use the stratified manifest.
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

record_available_url() {
  local name="$1"
  local url="$2"
  printf '%s\t%s\n' "${name}" "${url}"
  if [[ -n "${AVAILABILITY_OUTPUT}" ]]; then
    printf '%s\t%s\n' "${name}" "${url}" >> "${AVAILABILITY_OUTPUT}"
  fi
}

load_manifest_targets() {
  local manifest_path="$1"
  if [[ ! -f "${manifest_path}" ]]; then
    log "[WARN]  Manifest not found: ${manifest_path}"
    log "[WARN]  Falling back to legacy 5-target list"
    return 1
  fi
  if [[ ! -x "${VENV_PYTHON}" ]]; then
    log "[ERROR] Python environment not found: ${VENV_PYTHON}"
    log "[ERROR] Use .venv/bin/python per project environment rules."
    return 2
  fi
  "${VENV_PYTHON}" -c '
import json
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
targets = manifest.get("targets", [])
seen = set()
for row in targets:
    hip = str(row.get("hip", "")).strip()
    if not hip:
        continue
    name = hip if hip.upper().startswith("HIP") else f"HIP{hip}"
    if name in seen:
        continue
    seen.add(name)
    print(name)
' "${manifest_path}"
}

discover_hdf5_url() {
  local name="$1"
  local search_url="https://breakthroughinitiatives.org/opendatasearch?project=GBT&file_type=HDF5&target=${name}&search=Search&perPage=100"

  log "[INFO]  Discovering current BL archive URL for ${name}"
  log "[URL]   ${search_url}"

  local page
  if ! page="$(curl -fsSL --connect-timeout 15 --max-time 60 --retry 3 --retry-delay 5 --location "${search_url}")"; then
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
       --connect-timeout 15 \
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

target_hdf5_exists() {
  local name="$1"
  local url="$2"
  local target_dir="${OUT_DIR}/${name}"
  local filename
  filename="$(basename "${url}")"

  [[ -f "${target_dir}/${filename}" ]]
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

log "[START] BL extended corpus download"
log "[INFO]  Output directory: ${OUT_DIR}"
log "[INFO]  Manifest: ${MANIFEST}"
log "[INFO]  Target limit: ${MAX_TARGETS:-0} new URL-available download(s) (0 means all available targets)"
log "[INFO]  Dry run: ${DRY_RUN}"
log "[INFO]  Discover only: ${DISCOVER_ONLY}"
if [[ -n "${AVAILABILITY_OUTPUT}" ]]; then
  log "[INFO]  Availability output: ${AVAILABILITY_OUTPUT}"
  mkdir -p "$(dirname "${AVAILABILITY_OUTPUT}")"
  : > "${AVAILABILITY_OUTPUT}"
fi
mkdir -p "${OUT_DIR}"

if manifest_targets="$(load_manifest_targets "${MANIFEST}")"; then
  mapfile -t TARGETS <<< "${manifest_targets}"
  log "[INFO]  Loaded ${#TARGETS[@]} target(s) from manifest"
else
  status=$?
  if [[ "${status}" -eq 2 ]]; then
    exit 1
  fi
fi

checked=0
total=${#TARGETS[@]}
downloaded=0
reused=0
skipped=0
available=0

for name in "${TARGETS[@]}"; do
  if [[ "${DISCOVER_ONLY}" -eq 1 && "${MAX_TARGETS}" != "0" && "${available}" -ge "${MAX_TARGETS}" ]]; then
    log "[INFO]  URL-available target limit reached (${MAX_TARGETS}); stopping early"
    break
  fi
  checked=$((checked + 1))
  log "[${checked}/${total}] Target: ${name}"
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    log "[DRY-RUN] Would discover and download current HDF5 evidence for ${name}"
    available=$((available + 1))
    continue
  fi
  if ! url="$(discover_hdf5_url "${name}")"; then
    skipped=$((skipped + 1))
    continue
  fi
  available=$((available + 1))
  if [[ "${DISCOVER_ONLY}" -eq 1 ]]; then
    record_available_url "${name}" "${url}"
    continue
  fi
  if target_hdf5_exists "${name}" "${url}"; then
    log "[SKIP] Reusing existing HDF5 evidence for ${name}; does not consume new-download limit"
    reused=$((reused + 1))
    continue
  fi
  if [[ "${MAX_TARGETS}" != "0" && "${downloaded}" -ge "${MAX_TARGETS}" ]]; then
    log "[INFO]  New-download target limit reached (${MAX_TARGETS}); stopping early"
    break
  fi
  if download_hdf5 "${name}" "${url}"; then
    downloaded=$((downloaded + 1))
  else
    skipped=$((skipped + 1))
  fi
done

if [[ "${DRY_RUN}" -eq 1 ]]; then
  log "[DONE]  Dry run complete; no network download attempted."
  exit 0
fi

if [[ "${DISCOVER_ONLY}" -eq 1 ]]; then
  log "[DONE]  Discovery complete; no HDF5 payloads downloaded."
  log "[INFO]  Manifest targets checked: ${checked}/${total}"
  log "[INFO]  URL-available HDF5 targets: ${available}"
  log "[INFO]  Targets without a discovered HDF5 URL: ${skipped}"
  if [[ "${available}" -eq 0 ]]; then
    log "[ERROR] No URL-available HDF5 targets were found."
    exit 1
  fi
  exit 0
fi

log "[DONE]  Extended corpus download complete"
log "[INFO]  Successful new downloads: ${downloaded}"
log "[INFO]  Reused existing HDF5 targets: ${reused}"
log "[INFO]  URL-available HDF5 targets processed: ${available}"
log "[INFO]  Skipped unavailable or failed targets: ${skipped}"
log "[INFO]  Files in ${OUT_DIR}:"
find "${OUT_DIR}" -name "*.h5" -exec du -sh {} \; 2>/dev/null || log "[INFO]  (none downloaded)"

if [[ "$((downloaded + reused))" -eq 0 ]]; then
  log "[ERROR] No held-out evidence files were downloaded or reused."
  log "[ERROR] This command did not add usable extended-corpus evidence; empty directories are not evidence."
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
