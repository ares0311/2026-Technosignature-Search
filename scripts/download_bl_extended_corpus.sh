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
#   bash scripts/download_bl_extended_corpus.sh --discover-only \
#       --manifest data_selection/batch_manifests/local_coverage_batch3_manifest.json \
#       --discovery-result-output \
#       data_selection/batch_manifests/local_coverage_batch3_discovery_result.json
#
# Output: data/extended_corpus/<target_name>/<filename>.h5
#
# Scientific guardrail:
#   These files are calibration and generalisation aids.  No downloaded file or
#   derived hit table constitutes a technosignature detection or authorizes
#   external submission.
#
# Data/storage policy guardrail:
#   This script is a targeted batch-pull cache bootstrap, not a broad archive
#   mirror. It keeps raw public HDF5 payloads as evictable cache unless a later
#   candidate/eval/calibration policy explicitly pins them.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${TECHNO_EXTENDED_CORPUS_OUT_DIR:-${REPO_ROOT}/data/extended_corpus}"
VENV_PYTHON="${TECHNO_EXTENDED_CORPUS_PYTHON:-${REPO_ROOT}/.venv/bin/python}"
MANIFEST="${REPO_ROOT}/data/target_sample_manifest.json"
MAX_TARGETS="${TECHNO_EXTENDED_CORPUS_MAX_TARGETS:-0}"
# Real hard constraint, not a 4TB-external-SSD-era fallback: this project has
# no external SSD and no cloud storage available for testing, so the entire
# local data footprint (data/ + models/ + artifacts/) must never exceed this
# cap. See docs/astrometrics_data_selection_policy.md and
# docs/astrometrics_external_and_cloud_storage_policy.md, both corrected
# 2026-07-11.
LOCAL_STORAGE_CAP_GB="${TECHNO_LOCAL_STORAGE_CAP_GB:-100}"
LOCAL_STORAGE_USAGE_DIRS="${TECHNO_LOCAL_STORAGE_USAGE_DIRS:-${REPO_ROOT}/data ${REPO_ROOT}/models ${REPO_ROOT}/artifacts}"
FREE_SPACE_RESERVE_GB="${TECHNO_EXTENDED_CORPUS_FREE_SPACE_RESERVE_GB:-10}"
# No published BL Open Data Archive rate limit exists for this discovery
# endpoint (verified 2026-07-04, see docs/bl_hprc_target_list_research.md) --
# this default is a conservative, configurable choice per AGENTS.md's data
# collection parallelization directive (4-8 bounded workers when no
# documented limit exists), not a claimed archive-published limit.
DISCOVERY_WORKERS="${TECHNO_EXTENDED_CORPUS_DISCOVERY_WORKERS:-4}"
ACQUISITION_ROLE="live_search_bootstrap_cache"
ACQUISITION_MODE="targeted_batch_pull"
RAW_RETENTION_POLICY="public_raw_archive_cache_not_pinned"
DRY_RUN=0
DISCOVER_ONLY=0
AVAILABILITY_OUTPUT=""
DISCOVERY_RESULT_OUTPUT=""

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
    --discovery-result-output)
      DISCOVERY_RESULT_OUTPUT="$2"
      shift 2
      ;;
    -h|--help)
      cat <<'EOF'
Usage: bash scripts/download_bl_extended_corpus.sh [--manifest PATH] [--dry-run] [--discover-only] [--availability-output PATH] [--discovery-result-output PATH]

Downloads current Breakthrough Open Data HDF5 evidence inputs into:
  data/extended_corpus/<target>/

Environment:
  TECHNO_EXTENDED_CORPUS_MAX_TARGETS=N  Limit new URL-available downloads;
                                        existing HDF5 evidence is reused without
                                        consuming the limit. 0 means all
                                        available manifest targets.
  TECHNO_EXTENDED_CORPUS_OUT_DIR=PATH   Override output directory for tests or
                                        isolated local runs.
  TECHNO_LOCAL_STORAGE_CAP_GB=N         Hard cap on this project's total local
                                        data footprint (data/ + models/ +
                                        artifacts/), never exceeded. Default:
                                        100. No external SSD or cloud storage
                                        is available for this project -- this
                                        is a real ceiling, not a conservative
                                        fallback. A download that would push
                                        total usage over the cap is skipped
                                        with reason local_storage_cap_exceeded.
  TECHNO_LOCAL_STORAGE_USAGE_DIRS="A B" Space-separated directories summed
                                        against the cap. Default: this
                                        project's data/, models/, artifacts/
                                        directories under the repo root.
  TECHNO_EXTENDED_CORPUS_FREE_SPACE_RESERVE_GB=N
                                        Minimum free GB to preserve on the
                                        underlying disk before each new
                                        payload download. Default: 10.
                                        Tests may set 0 for tiny temp dirs.
  TECHNO_EXTENDED_CORPUS_DISCOVERY_WORKERS=N
                                        Bounded concurrent discovery workers
                                        for --discover-only runs with no
                                        TECHNO_EXTENDED_CORPUS_MAX_TARGETS
                                        limit set. Default: 4. No published BL
                                        rate limit exists (verified 2026-07-04,
                                        docs/bl_hprc_target_list_research.md);
                                        this is a conservative default, not a
                                        claimed archive limit.

Options:
  --manifest PATH  Stratified target manifest JSON. Default:
                   data/target_sample_manifest.json
  --dry-run        Enumerate manifest targets without network access.
  --discover-only  Query BL search pages and print target<TAB>URL rows for
                   URL-available HDF5 records without downloading payloads.
  --availability-output PATH
                   Write URL-available target<TAB>URL rows to PATH. Use with
                   --discover-only for a durable, verified availability map.
  --discovery-result-output PATH
                   Write the full discovery-round summary JSON (available and
                   skipped targets, with skip reasons) to PATH. Use with
                   --discover-only for a durable, per-round committed record —
                   docs/data_collection_status.json only keeps the single
                   most recent discovery run, so without this, a later
                   round's discovery silently loses an earlier round's
                   "no HDF5 URL found" results. Pass the written file to
                   `techno-search build-target-priority-queue
                   --extra-discovery-result-path PATH` (or commit it under
                   data_selection/batch_manifests/*_discovery_result.json,
                   which is auto-globbed by default).

Scientific guardrail:
  Outputs are local calibration/generalisation aids only. They do not
  constitute detections or authorize external submission.

Data/storage guardrail:
  Acquisition role: live_search_bootstrap_cache
  Acquisition mode: targeted_batch_pull
  Raw retention: public raw archive cache, not pinned evidence by default.
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

# Compact progress with a computed ETA -- printed every 10th completion (plus
# the final one), not per-target, so a large bulk discovery run proves it is
# alive without flooding the terminal with thousands of lines.
_log_discovery_progress() {
  local checked="$1" total="$2" start_epoch="$3"
  if [[ "${checked}" -lt "${total}" && $((checked % 10)) -ne 0 ]]; then
    return 0
  fi
  local now elapsed remaining_targets eta_seconds eta_min elapsed_min
  now="$(date +%s)"
  elapsed=$((now - start_epoch))
  [[ "${elapsed}" -lt 1 ]] && elapsed=1
  remaining_targets=$((total - checked))
  eta_seconds=$((remaining_targets * elapsed / checked))
  eta_min=$((eta_seconds / 60))
  elapsed_min=$((elapsed / 60))
  log "[PROGRESS] ${checked}/${total} checked (elapsed ${elapsed_min}m, ETA ~${eta_min}m remaining)"
}

reserve_kb() {
  "${VENV_PYTHON}" -c 'import sys; print(int(float(sys.argv[1]) * 1024 * 1024))' "${FREE_SPACE_RESERVE_GB}"
}

free_kb_for_out_dir() {
  df -Pk "${OUT_DIR}" | awk 'NR == 2 {print $4}'
}

content_length_kb() {
  local url="$1"
  local headers
  if ! headers="$(curl -fsSI --connect-timeout 15 --max-time 60 --retry 3 --retry-delay 5 --location "${url}" 2>/dev/null)"; then
    printf '0\n'
    return 0
  fi
  # Real bug found and fixed 2026-07-11: macOS's /usr/bin/awk (the BWK "one
  # true awk", not gawk) does not support IGNORECASE -- the original pattern
  # never matched a real server's "Content-Length:" header, so this always
  # returned 0 and silently disabled both this and the local-storage-cap
  # check on macOS. tolower($1) is portable POSIX awk.
  printf '%s\n' "${headers}" | awk '{ if (tolower($1) == "content-length:") value = $2 } END { gsub("\r", "", value); if (value == "") print 0; else print int((value + 1023) / 1024) }'
}

ensure_projected_free_space() {
  local url="$1"
  local reserve
  local free_now
  local projected_download
  reserve="$(reserve_kb)"
  if [[ "${reserve}" -le 0 ]]; then
    return 0
  fi
  free_now="$(free_kb_for_out_dir)"
  projected_download="$(content_length_kb "${url}")"
  if [[ -z "${free_now}" || "${free_now}" -le 0 ]]; then
    log "[ERROR] Could not determine free space for ${OUT_DIR}"
    return 1
  fi
  if [[ "${projected_download}" -gt 0 ]]; then
    if [[ "$((free_now - projected_download))" -lt "${reserve}" ]]; then
      log "[ERROR] Free-space policy would be violated by this download."
      log "[ERROR] Free now: $((free_now / 1024 / 1024))GB; projected payload: $((projected_download / 1024 / 1024))GB; reserve: ${FREE_SPACE_RESERVE_GB}GB"
      return 1
    fi
  elif [[ "${free_now}" -lt "${reserve}" ]]; then
    log "[ERROR] Free-space reserve is already below policy before download."
    log "[ERROR] Free now: $((free_now / 1024 / 1024))GB; reserve: ${FREE_SPACE_RESERVE_GB}GB"
    return 1
  fi
  return 0
}

storage_cap_kb() {
  "${VENV_PYTHON}" -c 'import sys; print(int(float(sys.argv[1]) * 1024 * 1024))' "${LOCAL_STORAGE_CAP_GB}"
}

project_storage_usage_kb() {
  local total=0
  local dir
  for dir in ${LOCAL_STORAGE_USAGE_DIRS}; do
    if [[ -d "${dir}" ]]; then
      total=$((total + $(du -sk "${dir}" 2>/dev/null | awk '{print $1}')))
    fi
  done
  printf '%s\n' "${total}"
}

ensure_within_local_storage_cap() {
  local url="$1"
  local cap
  local used_now
  local projected_download
  cap="$(storage_cap_kb)"
  if [[ "${cap}" -le 0 ]]; then
    return 0
  fi
  used_now="$(project_storage_usage_kb)"
  projected_download="$(content_length_kb "${url}")"
  if [[ "$((used_now + projected_download))" -gt "${cap}" ]]; then
    log "[ERROR] Local storage cap would be exceeded by this download."
    log "[ERROR] Used now: $((used_now / 1024 / 1024))GB; projected payload: $((projected_download / 1024 / 1024))GB; cap: ${LOCAL_STORAGE_CAP_GB}GB"
    log "[ERROR] No external SSD or cloud storage is available for this project -- evict already-processed raw payloads before continuing."
    return 1
  fi
  return 0
}

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
    # A bare numeric HIP identifier gets the HIP prefix (matches the
    # existing seed CSVs); any other real identifier (an already-prefixed
    # HIP1234, or a real non-HIP catalog name like GJ1002 for the HPRC
    # list real 60 nearest stars subset) is used verbatim -- see
    # docs/SAMPLING_DESIGN.md for why non-HIP identifiers exist in the
    # real full catalog.
    name = f"HIP{hip}" if hip.isdigit() else hip
    if name in seen:
        continue
    seen.add(name)
    print(name)
' "${manifest_path}"
}

discover_hdf5_url() {
  # Exit codes distinguish a confirmed no-match (1: the archive was queried
  # successfully and has no HDF5 file for this target) from a request
  # failure (2: curl/network/HTTP error, not evidence about the target) --
  # the caller must not record both under the same "no data" reason.
  local name="$1"
  local search_base_url="https://breakthroughinitiatives.org/opendatasearch"

  log "[INFO]  Discovering current BL archive URL for ${name}"
  log "[URL]   ${search_base_url}?project=GBT&file_type=HDF5&target=<url-encoded>&search=Search&perPage=100"

  local page
  # -G --data-urlencode percent-encodes the target name (e.g. spaces in
  # "DENIS-P J1048.0-3956") instead of interpolating it raw into the query
  # string, which curl otherwise rejects as a malformed URL.
  if ! page="$(
    curl -fsSL --connect-timeout 15 --max-time 60 --retry 3 --retry-delay 5 \
      --location -G \
      --data-urlencode "project=GBT" \
      --data-urlencode "file_type=HDF5" \
      --data-urlencode "target=${name}" \
      --data-urlencode "search=Search" \
      --data-urlencode "perPage=100" \
      "${search_base_url}"
  )"; then
    log "[WARN]  Discovery request failed for ${name} (network/HTTP error, not a confirmed no-match)"
    return 2
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
log "[INFO]  Acquisition role: ${ACQUISITION_ROLE}"
log "[INFO]  Acquisition mode: ${ACQUISITION_MODE}"
log "[INFO]  Raw retention policy: ${RAW_RETENTION_POLICY}"
log "[INFO]  Local storage cap: ${LOCAL_STORAGE_CAP_GB}GB (no external SSD or cloud storage available)"
log "[INFO]  Free-space reserve: ${FREE_SPACE_RESERVE_GB}GB"
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
policy_blocked=0
DOWNLOADED_NAMES=()
REUSED_NAMES=()
SKIPPED_NAMES=()
SKIPPED_REASONS=()
AVAILABLE_NAMES=()
AVAILABLE_URLS=()

if [[ "${DISCOVER_ONLY}" -eq 1 && "${DRY_RUN}" -eq 0 && "${MAX_TARGETS}" == "0" ]]; then
  # Bounded-parallel discovery: only used for unlimited discover-only runs.
  # Download mode, dry-run, and MAX_TARGETS-limited discover-only runs keep
  # the sequential loop below unchanged -- MAX_TARGETS early-stop semantics
  # (stop once N available targets are found) depend on strict sequential
  # order and are not reproduced under concurrent dispatch.
  log "[INFO]  Discovery workers: ${DISCOVERY_WORKERS} (bounded; no published BL rate limit exists -- see docs/bl_hprc_target_list_research.md -- conservative default, not a verified archive-published limit)"
  discovery_work_dir="$(mktemp -d "${TMPDIR:-/tmp}/bl_discovery.XXXXXX")"
  trap 'rm -rf "${discovery_work_dir}"' EXIT
  discovery_start_epoch="$(date +%s)"
  discovery_running=0
  discovery_index=0
  for name in "${TARGETS[@]}"; do
    discovery_index=$((discovery_index + 1))
    result_file="${discovery_work_dir}/$(printf '%06d' "${discovery_index}").tsv"
    (
      # Discovery's own per-target [INFO]/[URL]/[WARN] log lines are
      # redirected to /dev/null here (not removed from discover_hdf5_url
      # itself, which sequential download mode still uses for per-target
      # visibility) -- they would otherwise interleave illegibly across
      # concurrent workers and defeat the point of compact progress.
      if job_url="$(discover_hdf5_url "${name}" 2>/dev/null)"; then
        printf 'found\t%s\t%s\n' "${name}" "${job_url}" >"${result_file}"
      else
        job_status=$?
        if [[ "${job_status}" -eq 2 ]]; then
          printf 'failed\t%s\tdiscovery_request_failed\n' "${name}" >"${result_file}"
        else
          printf 'no_url\t%s\tno_hdf5_url_discovered\n' "${name}" >"${result_file}"
        fi
      fi
    ) &
    discovery_running=$((discovery_running + 1))
    if [[ "${discovery_running}" -ge "${DISCOVERY_WORKERS}" ]]; then
      wait -n
      discovery_running=$((discovery_running - 1))
      checked=$((checked + 1))
      _log_discovery_progress "${checked}" "${total}" "${discovery_start_epoch}"
    fi
  done
  while [[ "${discovery_running}" -gt 0 ]]; do
    wait -n
    discovery_running=$((discovery_running - 1))
    checked=$((checked + 1))
    _log_discovery_progress "${checked}" "${total}" "${discovery_start_epoch}"
  done

  # Aggregate in manifest order (zero-padded filenames sort correctly),
  # not completion order, so output/status ordering matches the sequential
  # path exactly regardless of which worker finished first.
  for result_file in "${discovery_work_dir}"/*.tsv; do
    [[ -f "${result_file}" ]] || continue
    IFS=$'\t' read -r result_kind result_name result_detail <"${result_file}"
    if [[ "${result_kind}" == "found" ]]; then
      available=$((available + 1))
      record_available_url "${result_name}" "${result_detail}"
      AVAILABLE_NAMES+=("${result_name}")
      AVAILABLE_URLS+=("${result_detail}")
    else
      skipped=$((skipped + 1))
      SKIPPED_NAMES+=("${result_name}")
      SKIPPED_REASONS+=("${result_detail}")
    fi
  done
  rm -rf "${discovery_work_dir}"
  trap - EXIT
else
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
    # Not `if ! url=...; then` -- `!` negates the exit status itself, so `$?`
    # inside the then-branch would no longer distinguish exit code 1 from 2.
    # A bare `url=$(...)` outside a conditional would also trip `set -e` on
    # the first failure, aborting the whole script instead of skipping one
    # target -- so the assignment must stay the condition of this `if`.
    if url="$(discover_hdf5_url "${name}")"; then
      :
    else
      discover_status=$?
      skipped=$((skipped + 1))
      SKIPPED_NAMES+=("${name}")
      if [[ "${discover_status}" -eq 2 ]]; then
        SKIPPED_REASONS+=("discovery_request_failed")
      else
        SKIPPED_REASONS+=("no_hdf5_url_discovered")
      fi
      continue
    fi
    available=$((available + 1))
    if [[ "${DISCOVER_ONLY}" -eq 1 ]]; then
      record_available_url "${name}" "${url}"
      AVAILABLE_NAMES+=("${name}")
      AVAILABLE_URLS+=("${url}")
      continue
    fi
    if target_hdf5_exists "${name}" "${url}"; then
      log "[SKIP] Reusing existing HDF5 evidence for ${name}; does not consume new-download limit"
      reused=$((reused + 1))
      REUSED_NAMES+=("${name}")
      continue
    fi
    if [[ "${MAX_TARGETS}" != "0" && "${downloaded}" -ge "${MAX_TARGETS}" ]]; then
      log "[INFO]  New-download target limit reached (${MAX_TARGETS}); stopping early"
      break
    fi
    if ! ensure_within_local_storage_cap "${url}"; then
      skipped=$((skipped + 1))
      SKIPPED_NAMES+=("${name}")
      SKIPPED_REASONS+=("local_storage_cap_exceeded")
      policy_blocked=1
      break
    fi
    if ! ensure_projected_free_space "${url}"; then
      skipped=$((skipped + 1))
      SKIPPED_NAMES+=("${name}")
      SKIPPED_REASONS+=("free_space_reserve_not_met")
      policy_blocked=1
      break
    fi
    if download_hdf5 "${name}" "${url}"; then
      downloaded=$((downloaded + 1))
      DOWNLOADED_NAMES+=("${name}")
    else
      skipped=$((skipped + 1))
      SKIPPED_NAMES+=("${name}")
      SKIPPED_REASONS+=("download_failed")
    fi
  done
fi

if [[ "${DRY_RUN}" -eq 1 ]]; then
  log "[DONE]  Dry run complete; no network download attempted."
  exit 0
fi

if [[ "${DISCOVER_ONLY}" -eq 1 ]]; then
  log "[DONE]  Discovery complete; no HDF5 payloads downloaded."
  log "[INFO]  Manifest targets checked: ${checked}/${total}"
  log "[INFO]  URL-available HDF5 targets: ${available}"
  log "[INFO]  Targets without a discovered HDF5 URL: ${skipped}"
  DISCOVERY_RUN_OK=1
  for reason in "${SKIPPED_REASONS[@]:-}"; do
    if [[ "${reason}" == "discovery_request_failed" ]]; then
      DISCOVERY_RUN_OK=0
      break
    fi
  done
  if [[ "${DISCOVERY_RUN_OK}" -eq 0 ]]; then
    log "[ERROR] One or more archive discovery requests failed; no-data conclusions are incomplete."
  elif [[ "${available}" -eq 0 ]]; then
    # A successful archive query that returns no products is valid metadata
    # evidence, not an operational failure. Keep the per-target
    # no_hdf5_url_discovered reasons and publish an ok=true run summary so
    # downstream queue builders do not confuse a confirmed empty result with
    # an unexecuted or transport-failed query.
    log "[INFO]  Discovery completed successfully; no current HDF5 products matched this manifest."
  fi
  TECHNO_SEARCH_BIN="${REPO_ROOT}/.venv/bin/techno-search"
  if [[ ! -x "${TECHNO_SEARCH_BIN}" ]] && command -v techno-search >/dev/null 2>&1; then
    TECHNO_SEARCH_BIN="$(command -v techno-search)"
  fi
  if [[ -x "${TECHNO_SEARCH_BIN}" && -x "${VENV_PYTHON}" ]]; then
    SUMMARY_JSON="$(
      AVAILABLE_NAMES="$(printf '%s\n' "${AVAILABLE_NAMES[@]:-}")" \
      AVAILABLE_URLS="$(printf '%s\n' "${AVAILABLE_URLS[@]:-}")" \
      SKIPPED_NAMES="$(printf '%s\n' "${SKIPPED_NAMES[@]:-}")" \
      SKIPPED_REASONS="$(printf '%s\n' "${SKIPPED_REASONS[@]:-}")" \
      AVAILABLE_COUNT="${available}" \
      SKIPPED_COUNT="${skipped}" \
      CHECKED_COUNT="${checked}" \
      TOTAL_COUNT="${total}" \
      RUN_OK="${DISCOVERY_RUN_OK}" \
      ACQUISITION_ROLE="${ACQUISITION_ROLE}" \
      RAW_RETENTION_POLICY="${RAW_RETENTION_POLICY}" \
      "${VENV_PYTHON}" -c '
import json
import os


def _lines(name):
    text = os.environ.get(name, "")
    return [line for line in text.split("\n") if line]


available_names = _lines("AVAILABLE_NAMES")
available_urls = _lines("AVAILABLE_URLS")
skipped_names = _lines("SKIPPED_NAMES")
skipped_reasons = _lines("SKIPPED_REASONS")
summary = {
    "ok": os.environ["RUN_OK"] == "1",
    "mode": "discover_only",
    "downloaded": 0,
    "reused": 0,
    "available": int(os.environ["AVAILABLE_COUNT"]),
    "skipped": int(os.environ["SKIPPED_COUNT"]),
    "checked": int(os.environ["CHECKED_COUNT"]),
    "total": int(os.environ["TOTAL_COUNT"]),
    "acquisition_role": os.environ["ACQUISITION_ROLE"],
    "acquisition_mode": "metadata_only_discovery",
    "raw_retention_policy": os.environ["RAW_RETENTION_POLICY"],
    "available_targets": [
        {"target": t, "url": u} for t, u in zip(available_names, available_urls)
    ],
    "skipped_targets": [
        {"target": t, "reason": r} for t, r in zip(skipped_names, skipped_reasons)
    ],
}
print(json.dumps(summary))
'
    )"
    "${TECHNO_SEARCH_BIN}" record-data-collection-status \
      --script download_bl_extended_corpus_discovery \
      --summary-json "${SUMMARY_JSON}" \
      >/dev/null 2>&1 || log "[INFO]  Discovery status manifest update/commit skipped (non-fatal)."
    if [[ -n "${DISCOVERY_RESULT_OUTPUT}" ]]; then
      mkdir -p "$(dirname "${DISCOVERY_RESULT_OUTPUT}")"
      printf '%s\n' "${SUMMARY_JSON}" >"${DISCOVERY_RESULT_OUTPUT}"
      log "[INFO]  Discovery result written: ${DISCOVERY_RESULT_OUTPUT}"
      log "[INFO]  Commit this file and re-run 'techno-search build-target-priority-queue' so this round's no-URL-found targets are not lost when a later discovery round overwrites docs/data_collection_status.json."
    fi
  fi
  if [[ "${DISCOVERY_RUN_OK}" -eq 0 ]]; then
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

RUN_OK=1
if [[ "$((downloaded + reused))" -eq 0 ]]; then
  RUN_OK=0
  log "[ERROR] No held-out evidence files were downloaded or reused."
  log "[ERROR] This command did not add usable extended-corpus evidence; empty directories are not evidence."
fi
if [[ "${policy_blocked}" -eq 1 ]]; then
  RUN_OK=0
  log "[ERROR] Data/storage policy blocked this run before completing all requested downloads."
fi

TECHNO_SEARCH_BIN="${REPO_ROOT}/.venv/bin/techno-search"
if [[ ! -x "${TECHNO_SEARCH_BIN}" ]] && command -v techno-search >/dev/null 2>&1; then
  TECHNO_SEARCH_BIN="$(command -v techno-search)"
fi
STATUS_PYTHON="${VENV_PYTHON}"
if [[ ! -x "${STATUS_PYTHON}" ]] && command -v python3 >/dev/null 2>&1; then
  STATUS_PYTHON="$(command -v python3)"
fi
if [[ -x "${TECHNO_SEARCH_BIN}" && -x "${STATUS_PYTHON}" ]]; then
  # Build a JSON summary that names *which* targets were downloaded/reused/
  # skipped (and why skipped ones failed) -- not just counts -- so this
  # committed manifest alone is enough to diagnose a real problem without
  # asking the operator to paste console output. Recorded on both success
  # and failure (RUN_OK) so a zero-evidence run is diagnosable too.
  SUMMARY_JSON="$(
    DOWNLOADED_NAMES="$(printf '%s\n' "${DOWNLOADED_NAMES[@]:-}")" \
    REUSED_NAMES="$(printf '%s\n' "${REUSED_NAMES[@]:-}")" \
    SKIPPED_NAMES="$(printf '%s\n' "${SKIPPED_NAMES[@]:-}")" \
    SKIPPED_REASONS="$(printf '%s\n' "${SKIPPED_REASONS[@]:-}")" \
    DOWNLOADED_COUNT="${downloaded}" \
    REUSED_COUNT="${reused}" \
    AVAILABLE_COUNT="${available}" \
    SKIPPED_COUNT="${skipped}" \
    CHECKED_COUNT="${checked}" \
    TOTAL_COUNT="${total}" \
    RUN_OK="${RUN_OK}" \
    ACQUISITION_ROLE="${ACQUISITION_ROLE}" \
    ACQUISITION_MODE="${ACQUISITION_MODE}" \
    RAW_RETENTION_POLICY="${RAW_RETENTION_POLICY}" \
    FREE_SPACE_RESERVE_GB="${FREE_SPACE_RESERVE_GB}" \
    LOCAL_STORAGE_CAP_GB="${LOCAL_STORAGE_CAP_GB}" \
    POLICY_BLOCKED="${policy_blocked}" \
    "${STATUS_PYTHON}" -c '
import json
import os


def _lines(name):
    text = os.environ.get(name, "")
    return [line for line in text.split("\n") if line]


skipped_names = _lines("SKIPPED_NAMES")
skipped_reasons = _lines("SKIPPED_REASONS")
summary = {
    "ok": os.environ["RUN_OK"] == "1",
    "downloaded": int(os.environ["DOWNLOADED_COUNT"]),
    "reused": int(os.environ["REUSED_COUNT"]),
    "available": int(os.environ["AVAILABLE_COUNT"]),
    "skipped": int(os.environ["SKIPPED_COUNT"]),
    "checked": int(os.environ["CHECKED_COUNT"]),
    "total": int(os.environ["TOTAL_COUNT"]),
    "acquisition_role": os.environ["ACQUISITION_ROLE"],
    "acquisition_mode": os.environ["ACQUISITION_MODE"],
    "raw_retention_policy": os.environ["RAW_RETENTION_POLICY"],
    "free_space_reserve_gb": float(os.environ["FREE_SPACE_RESERVE_GB"]),
    "local_storage_cap_gb": float(os.environ["LOCAL_STORAGE_CAP_GB"]),
    "policy_blocked": os.environ["POLICY_BLOCKED"] == "1",
    "downloaded_targets": _lines("DOWNLOADED_NAMES"),
    "reused_targets": _lines("REUSED_NAMES"),
    "skipped_targets": [
        {"target": t, "reason": r} for t, r in zip(skipped_names, skipped_reasons)
    ],
}
print(json.dumps(summary))
'
  )"
  "${TECHNO_SEARCH_BIN}" record-data-collection-status \
    --script download_bl_extended_corpus \
    --summary-json "${SUMMARY_JSON}" \
    >/dev/null 2>&1 || log "[INFO]  Status manifest update/commit skipped (non-fatal)."
fi

if [[ "${RUN_OK}" -eq 0 ]]; then
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
