#!/usr/bin/env bash
# run_stream_process_evict_batch.sh
#
# Executes a prepared stream_process_evict batch manifest
# (data_selection/batch_manifests/*_manifest.json, containing per-target
# "hip"/"source_hdf5_url"/"estimated_download_gb" rows already discovered
# and size-preflighted by an earlier round): download a bounded chunk of
# targets directly from their already-verified URLs, run turboSETI +
# pipeline over the corpus (idempotent, only touches new .dat files), then
# delete each chunk's raw HDF5 payloads once its candidate report exists --
# keeping peak local disk usage bounded to roughly one chunk's size instead
# of the full batch total.
#
# Usage:
#   caffeinate -i bash scripts/run_stream_process_evict_batch.sh \
#       --manifest data_selection/batch_manifests/local_coverage_first_bounded_batch_manifest.json \
#       [--out-dir PATH] [--results-dir PATH] [--status-key NAME] \
#       [--chunk-size 25] [--limit N] [--dry-run]
#
# Scientific guardrail:
#   Downloaded files and derived hit tables/candidate reports are local
#   calibration and generalisation aids only. No file or report entry
#   constitutes a technosignature detection or authorizes external
#   submission.
#
# Data/storage guardrail:
#   Acquisition mode: stream_process_evict. Raw HDF5 payloads are evicted
#   immediately after their candidate report is confirmed; only the .dat
#   hit table and results/ report artifacts are retained.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="${TECHNO_STREAM_PROCESS_PYTHON:-${REPO_ROOT}/.venv/bin/python}"
OUT_DIR="${REPO_ROOT}/data/extended_corpus"
RESULTS_DIR="${REPO_ROOT}/results"
MANIFEST=""
CHUNK_SIZE=25
LIMIT=0
DRY_RUN=0
PIPELINE_WORKERS=12
LOG_FILE=""
LOCAL_STORAGE_CAP_GB="${TECHNO_LOCAL_STORAGE_CAP_GB:-100}"
LOCAL_STORAGE_USAGE_DIRS="${TECHNO_LOCAL_STORAGE_USAGE_DIRS:-${REPO_ROOT}/data ${REPO_ROOT}/models ${REPO_ROOT}/artifacts}"
FREE_SPACE_RESERVE_GB="${TECHNO_EXTENDED_CORPUS_FREE_SPACE_RESERVE_GB:-10}"
PROCESSING_SLOT_DIR="${TECHNO_STREAM_PROCESS_SLOT_DIR:-}"
PROCESSING_SLOT_COUNT="${TECHNO_STREAM_PROCESS_SLOT_COUNT:-0}"
ACTIVE_PROCESSING_SLOT=""
STATUS_KEY=""
REQUIRE_STATUS_RECORD=0

# Always prints to the console AND (once LOG_FILE is set, right after
# manifest validation below) appends to a log file -- the caller must not
# have to remember to add `tee`/redirection themselves to get either one.
# A prior version of this script relied entirely on the caller's shell
# redirection, so a plain `> file 2>&1` invocation (as opposed to `| tee
# file`) silently produced zero terminal output for the many-minutes-long
# gaps between progress lines, looking hung. Fixed 2026-07-11.
log() {
  local line="[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] $*"
  echo "${line}"
  if [[ -n "${LOG_FILE}" ]]; then
    echo "${line}" >> "${LOG_FILE}"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --manifest) MANIFEST="$2"; shift 2 ;;
    --out-dir) OUT_DIR="$2"; shift 2 ;;
    --results-dir) RESULTS_DIR="$2"; shift 2 ;;
    --status-key) STATUS_KEY="$2"; REQUIRE_STATUS_RECORD=1; shift 2 ;;
    --chunk-size) CHUNK_SIZE="$2"; shift 2 ;;
    --limit) LIMIT="$2"; shift 2 ;;
    --pipeline-workers) PIPELINE_WORKERS="$2"; shift 2 ;;
    --log-file) LOG_FILE="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help)
      sed -n '2,26p' "$0" | grep '^#' | sed 's/^# \?//'
      exit 0
      ;;
    *) log "[ERROR] Unknown argument: $1"; exit 2 ;;
  esac
done

if [[ -z "${MANIFEST}" ]]; then
  log "[ERROR] --manifest PATH is required."
  exit 2
fi
if [[ ! -f "${MANIFEST}" ]]; then
  log "[ERROR] Manifest not found: ${MANIFEST}"
  exit 2
fi

if [[ -n "${STATUS_KEY:-}" && ! "${STATUS_KEY}" =~ ^[A-Za-z0-9_.-]+$ ]]; then
  log "[ERROR] --status-key may contain only letters, numbers, dot, underscore, and hyphen."
  exit 2
fi
if [[ ! -x "${VENV_PYTHON}" ]]; then
  log "[ERROR] Python interpreter not executable: ${VENV_PYTHON}"
  log "[ERROR] Create .venv or set TECHNO_STREAM_PROCESS_PYTHON to the active project interpreter."
  exit 2
fi

mkdir -p "${OUT_DIR}" "${RESULTS_DIR}"

if [[ -z "${LOG_FILE}" ]]; then
  LOG_FILE="${REPO_ROOT}/data_cache/logs/$(basename "${MANIFEST}" .json)_run.log"
fi
mkdir -p "$(dirname "${LOG_FILE}")"
log "[INFO]  Logging to console and ${LOG_FILE}"

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

# TSV rows: hip<TAB>url<TAB>estimated_gb
# Written under the repo's own ignored data_cache/ (not /tmp): this session's
# sandbox confines writes to the repo root, so mktemp against $TMPDIR fails.
SCRATCH_DIR="${REPO_ROOT}/data_cache"
mkdir -p "${SCRATCH_DIR}"
TARGET_ROWS_FILE="${SCRATCH_DIR}/stream_evict_targets.$$.tsv"
CURRENT_CURL_PID=""

release_processing_slot() {
  if [[ -n "${ACTIVE_PROCESSING_SLOT}" ]]; then
    rmdir "${ACTIVE_PROCESSING_SLOT}" 2>/dev/null || true
    log "[SLOT] Released bounded post-processing slot"
    ACTIVE_PROCESSING_SLOT=""
  fi
}

acquire_processing_slot() {
  if [[ -z "${PROCESSING_SLOT_DIR}" || "${PROCESSING_SLOT_COUNT}" -le 0 ]]; then
    return 0
  fi
  mkdir -p "${PROCESSING_SLOT_DIR}"
  local waited=0 slot candidate
  while true; do
    for ((slot=1; slot<=PROCESSING_SLOT_COUNT; slot++)); do
      candidate="${PROCESSING_SLOT_DIR}/slot${slot}"
      if mkdir "${candidate}" 2>/dev/null; then
        ACTIVE_PROCESSING_SLOT="${candidate}"
        log "[SLOT] Acquired post-processing slot ${slot}/${PROCESSING_SLOT_COUNT}"
        return 0
      fi
    done
    sleep 2
    waited=$((waited + 2))
    if (( waited % 20 == 0 )); then
      log "[WAIT] Waiting for a bounded post-processing slot (${waited}s elapsed)"
    fi
  done
}

# Clean Ctrl+C handling, matching this project's VISIBLE PROGRESS DIRECTIVE:
# kill any in-flight background curl (left running would otherwise become an
# orphaned process writing to a file nothing is tracking), then exit. Safe to
# re-run the exact same command afterward -- downloads resume via
# --continue-at plus the real-size check in download_target(), and
# turboSETI/pipeline both skip already-completed targets, so nothing already
# finished is redone and nothing partial is silently treated as done.
_on_interrupt() {
  log "[INTERRUPT] Stopping. Safe to re-run the same command to resume --"
  log "[INTERRUPT] downloads resume from their real byte offset, and"
  log "[INTERRUPT] turboSETI/pipeline skip already-completed targets."
  if [[ -n "${CURRENT_CURL_PID}" ]] && kill -0 "${CURRENT_CURL_PID}" 2>/dev/null; then
    kill "${CURRENT_CURL_PID}" 2>/dev/null || true
  fi
  release_processing_slot
  rm -f "${TARGET_ROWS_FILE}"
  exit 130
}
trap _on_interrupt INT TERM
trap 'release_processing_slot; rm -f "${TARGET_ROWS_FILE}"' EXIT
"${VENV_PYTHON}" -c '
import json
import sys

manifest = json.loads(open(sys.argv[1], encoding="utf-8").read())
limit = int(sys.argv[2])
rows = manifest.get("targets", [])
if limit > 0:
    rows = rows[:limit]
for row in rows:
    hip = str(row.get("hip", "")).strip()
    url = str(row.get("source_hdf5_url", "")).strip() or "LOCAL_DAT_ONLY"
    gb = row.get("estimated_download_gb", 0)
    if not hip:
        continue
    print(f"{hip}\t{url}\t{gb or 0}")
' "${MANIFEST}" "${LIMIT}" > "${TARGET_ROWS_FILE}"

TOTAL=$(wc -l < "${TARGET_ROWS_FILE}" | tr -d ' ')
log "[START] stream_process_evict batch"
log "[INFO]  Manifest: ${MANIFEST}"
log "[INFO]  Targets: ${TOTAL} (chunk size ${CHUNK_SIZE})"
log "[INFO]  Local storage cap: ${LOCAL_STORAGE_CAP_GB}GB; free-space reserve: ${FREE_SPACE_RESERVE_GB}GB"

if [[ "${TOTAL}" -eq 0 ]]; then
  log "[ERROR] No usable target rows (missing hip) in manifest."
  exit 1
fi

DOWNLOADED_COUNT=0
DOWNLOADED_GB="0"
DOWNLOADED_NAMES=()
EVICTED_COUNT=0
EVICTED_NAMES=()
NEWLY_PROCESSED_COUNT=0
NEWLY_PROCESSED_NAMES=()
LOCAL_DAT_REUSE_COUNT=0
LOCAL_DAT_REUSE_NAMES=()
ALREADY_PROCESSED_COUNT=0
ALREADY_PROCESSED_NAMES=()
FAILED_COUNT=0
FAILED_NAMES=()
FAILED_REASONS=()
DAT_PRODUCED_COUNT=0
REPORT_COUNT=0

target_has_completed_evidence() {
  local hip="$1"
  local target_dir="${OUT_DIR}/${hip}"
  local dat_file dat_stem report_hit
  dat_file="$(find "${target_dir}" -maxdepth 1 -name '*.dat' 2>/dev/null | head -1)"
  if [[ -z "${dat_file}" ]]; then
    return 1
  fi
  dat_stem="$(basename "${dat_file}" .dat)"
  report_hit="$(find "${RESULTS_DIR}" -name '*.manifest.json' -path "*${dat_stem}*" 2>/dev/null | head -1)"
  [[ -n "${report_hit}" ]]
}

target_has_hit_table() {
  local hip="$1"
  find "${OUT_DIR}/${hip}" -maxdepth 1 -name '*.dat' -print -quit 2>/dev/null | grep -q .
}

download_target() {
  local hip="$1" url="$2" gb="$3"
  local target_dir="${OUT_DIR}/${hip}"
  local filename
  filename="$(basename "${url}")"
  local out_path="${target_dir}/${filename}"

  # Compare against the real remote size (not just local existence) --
  # a same-named file that exists but is smaller than the remote copy is a
  # partial download (e.g. from an interrupted prior run or a concurrent
  # shard) and must be resumed, not silently treated as complete.
  if [[ -f "${out_path}" ]]; then
    local local_size remote_size
    local_size=$(stat -f%z "${out_path}" 2>/dev/null || stat -c%s "${out_path}" 2>/dev/null || echo 0)
    remote_size=$(curl -fsSI --connect-timeout 15 --max-time 30 --location "${url}" 2>/dev/null | \
      awk '{ if (tolower($1) == "content-length:") value = $2 } END { gsub("\r", "", value); print value + 0 }')
    if [[ -n "${remote_size}" && "${remote_size}" -gt 0 && "${local_size}" -ge "${remote_size}" ]]; then
      log "[SKIP] ${hip}: already present and complete (${out_path})"
      return 0
    fi
    log "[RESUME] ${hip}: partial file present (${local_size} of ${remote_size:-unknown} bytes); resuming"
  fi

  local cap_kb used_kb
  cap_kb=$("${VENV_PYTHON}" -c "print(int(${LOCAL_STORAGE_CAP_GB} * 1024 * 1024))")
  used_kb=$(project_storage_usage_kb)
  local projected_kb
  projected_kb=$("${VENV_PYTHON}" -c "print(int(${gb} * 1024 * 1024))")
  if [[ $((used_kb + projected_kb)) -gt "${cap_kb}" ]]; then
    log "[ERROR] ${hip}: local storage cap would be exceeded (used $((used_kb / 1024 / 1024))GB + ${gb}GB > ${LOCAL_STORAGE_CAP_GB}GB cap). Stopping batch."
    return 2
  fi
  local free_kb reserve_kb
  free_kb=$(df -Pk "${OUT_DIR}" | awk 'NR == 2 {print $4}')
  reserve_kb=$("${VENV_PYTHON}" -c "print(int(${FREE_SPACE_RESERVE_GB} * 1024 * 1024))")
  if [[ $((free_kb - projected_kb)) -lt "${reserve_kb}" ]]; then
    log "[ERROR] ${hip}: free-space reserve would be violated. Stopping batch."
    return 2
  fi

  mkdir -p "${target_dir}"
  log "[DL]   ${hip} <- ${filename} (~${gb}GB)"

  # curl runs silently (-s) but in the background so this loop can poll the
  # partially-written file's size every ~20s and print a live progress line
  # -- a single file can take 15-20+ minutes at this sandbox's observed
  # ~200KB/s cap, and printing nothing for that long would look hung
  # (violates the project's VISIBLE PROGRESS DIRECTIVE).
  curl -fsS --continue-at - --connect-timeout 15 --retry 3 --retry-delay 5 \
       --location --output "${out_path}" "${url}" &
  local curl_pid=$!
  local dl_start_epoch dl_expected_bytes
  dl_start_epoch=$(date +%s)
  dl_expected_bytes=$("${VENV_PYTHON}" -c "print(int(${gb} * 1024 * 1024 * 1024))")
  while kill -0 "${curl_pid}" 2>/dev/null; do
    sleep 20
    kill -0 "${curl_pid}" 2>/dev/null || break
    local cur_bytes elapsed pct rate_bps eta_seconds eta_min
    cur_bytes=$(stat -f%z "${out_path}" 2>/dev/null || stat -c%s "${out_path}" 2>/dev/null || echo 0)
    elapsed=$(( $(date +%s) - dl_start_epoch ))
    [[ "${elapsed}" -lt 1 ]] && elapsed=1
    pct=0
    eta_min=0
    if [[ "${dl_expected_bytes}" -gt 0 ]]; then
      pct=$(( cur_bytes * 100 / dl_expected_bytes ))
      rate_bps=$(( cur_bytes / elapsed ))
      if [[ "${rate_bps}" -gt 0 ]]; then
        eta_seconds=$(( (dl_expected_bytes - cur_bytes) / rate_bps ))
        eta_min=$(( eta_seconds / 60 ))
      fi
    fi
    log "[PROGRESS] ${hip}: $((cur_bytes / 1024 / 1024))MB/$((dl_expected_bytes / 1024 / 1024))MB (${pct}%), elapsed $((elapsed / 60))m, ETA ~${eta_min}m"
  done
  if ! wait "${curl_pid}"; then
    log "[WARN] ${hip}: download failed"
    rm -f "${out_path}"
    return 1
  fi
  return 0
}

evict_target_if_processed() {
  local hip="$1"
  local target_dir="${OUT_DIR}/${hip}"
  local dat_file
  dat_file="$(find "${target_dir}" -maxdepth 1 -name '*.dat' 2>/dev/null | head -1)"
  if [[ -z "${dat_file}" ]]; then
    log "[HOLD] ${hip}: no .dat produced yet; keeping raw payload"
    return 1
  fi
  local dat_stem
  dat_stem="$(basename "${dat_file}" .dat)"
  local report_hit
  report_hit="$(find "${RESULTS_DIR}" -name "*.manifest.json" -path "*${dat_stem}*" 2>/dev/null | head -1)"
  if [[ -z "${report_hit}" ]]; then
    log "[HOLD] ${hip}: no candidate report found yet for ${dat_stem}; keeping raw payload"
    return 1
  fi
  local h5_count
  h5_count=$(find "${target_dir}" -maxdepth 1 -name '*.h5' | wc -l | tr -d ' ')
  EVICTION_OCCURRED=0
  if [[ "${h5_count}" -eq 0 ]]; then
    return 0
  fi
  find "${target_dir}" -maxdepth 1 -name '*.h5' -delete
  EVICTION_OCCURRED=1
  log "[EVICT] ${hip}: raw HDF5 payload deleted (report: $(basename "${report_hit}"))"
  return 0
}

process_chunk() {
  local -n names_ref=$1
  if [[ "${#names_ref[@]}" -eq 0 ]]; then
    return 0
  fi
  acquire_processing_slot
  local hip
  # Process only this shard's current chunk. The previous implementation
  # passed OUT_DIR to every concurrent shard, so all shards recursively
  # scanned the same global corpus and raced while writing identical .dat
  # outputs. Target directories are disjoint across the prepared manifests,
  # making these per-target calls safe for bounded shard parallelism.
  for hip in "${names_ref[@]}"; do
    log "[CHUNK] ${hip}: running isolated turboSETI"
    if ! bash "${REPO_ROOT}/scripts/run_turboseti_on_extended_corpus.sh" \
      --corpus-dir "${OUT_DIR}/${hip}"; then
      log "[WARN] ${hip}: turboSETI reported a failure; continuing to pipeline/eviction for whatever succeeded"
    fi
    log "[CHUNK] ${hip}: running isolated pipeline (${PIPELINE_WORKERS} workers)"
    if ! bash "${REPO_ROOT}/scripts/run_pipeline_on_bl_data.sh" \
      --dat-dir "${OUT_DIR}/${hip}" --results-dir "${RESULTS_DIR}" \
      --workers "${PIPELINE_WORKERS}"; then
      log "[WARN] ${hip}: pipeline reported a failure; continuing to eviction check"
    fi
  done
  for hip in "${names_ref[@]}"; do
    if evict_target_if_processed "${hip}"; then
      NEWLY_PROCESSED_COUNT=$((NEWLY_PROCESSED_COUNT + 1))
      NEWLY_PROCESSED_NAMES+=("${hip}")
      if [[ "${EVICTION_OCCURRED}" -eq 1 ]]; then
        EVICTED_COUNT=$((EVICTED_COUNT + 1))
        EVICTED_NAMES+=("${hip}")
      else
        LOCAL_DAT_REUSE_COUNT=$((LOCAL_DAT_REUSE_COUNT + 1))
        LOCAL_DAT_REUSE_NAMES+=("${hip}")
      fi
    else
      FAILED_COUNT=$((FAILED_COUNT + 1))
      FAILED_NAMES+=("${hip}")
      FAILED_REASONS+=("pipeline_evidence_incomplete")
    fi
  done
  release_processing_slot
}

if [[ "${DRY_RUN}" -eq 1 ]]; then
  log "[DRY-RUN] Would process ${TOTAL} targets from ${MANIFEST} in chunks of ${CHUNK_SIZE}."
  exit 0
fi

TOTAL_GB=$("${VENV_PYTHON}" -c "
import sys
total = 0.0
for line in open(sys.argv[1], encoding='utf-8'):
    parts = line.rstrip('\n').split('\t')
    if len(parts) == 3:
        total += float(parts[2])
print(total)
" "${TARGET_ROWS_FILE}")
BATCH_START_EPOCH=$(date +%s)

CHUNK_NAMES=()
processed_in_run=0
STOP=0
while IFS=$'\t' read -r hip url gb; do
  if [[ "${STOP}" -eq 1 ]]; then
    break
  fi
  processed_in_run=$((processed_in_run + 1))
  log "[${processed_in_run}/${TOTAL}] ${hip}"
  if target_has_completed_evidence "${hip}"; then
    if evict_target_if_processed "${hip}" && [[ "${EVICTION_OCCURRED}" -eq 1 ]]; then
      EVICTED_COUNT=$((EVICTED_COUNT + 1))
      EVICTED_NAMES+=("${hip}")
    fi
    ALREADY_PROCESSED_COUNT=$((ALREADY_PROCESSED_COUNT + 1))
    ALREADY_PROCESSED_NAMES+=("${hip}")
    log "[DONE] ${hip}: existing .dat and candidate report; no re-download needed"
    continue
  fi
  if target_has_hit_table "${hip}"; then
    CHUNK_NAMES+=("${hip}")
    log "[REUSE] ${hip}: existing .dat will be scored into this search; no re-download needed"
    if [[ "${#CHUNK_NAMES[@]}" -ge "${CHUNK_SIZE}" ]]; then
      process_chunk CHUNK_NAMES
      CHUNK_NAMES=()
    fi
    continue
  fi
  if [[ "${url}" == "LOCAL_DAT_ONLY" ]]; then
    FAILED_COUNT=$((FAILED_COUNT + 1))
    FAILED_NAMES+=("${hip}")
    FAILED_REASONS+=("source_url_missing_and_no_local_dat")
    log "[ERROR] ${hip}: no source URL and no reusable local .dat evidence"
    continue
  fi
  if download_target "${hip}" "${url}" "${gb}"; then
    DOWNLOADED_COUNT=$((DOWNLOADED_COUNT + 1))
    DOWNLOADED_GB="$("${VENV_PYTHON}" -c "print(${DOWNLOADED_GB} + ${gb})")"
    DOWNLOADED_NAMES+=("${hip}")
    CHUNK_NAMES+=("${hip}")
  else
    status=$?
    FAILED_COUNT=$((FAILED_COUNT + 1))
    FAILED_NAMES+=("${hip}")
    if [[ "${status}" -eq 2 ]]; then
      FAILED_REASONS+=("storage_policy_blocked")
      STOP=1
    else
      FAILED_REASONS+=("download_failed")
    fi
  fi

  # Batch-level cumulative ETA -- printed after every target regardless of
  # success/failure, so the whole run's liveness and remaining-time estimate
  # is visible even during a single very slow download (see per-file
  # [PROGRESS] lines inside download_target for that finer-grained case).
  batch_elapsed=$(( $(date +%s) - BATCH_START_EPOCH ))
  [[ "${batch_elapsed}" -lt 1 ]] && batch_elapsed=1
  "${VENV_PYTHON}" -c "
downloaded_gb = ${DOWNLOADED_GB}
total_gb = ${TOTAL_GB}
elapsed = ${batch_elapsed}
pct = (downloaded_gb / total_gb * 100) if total_gb > 0 else 0
rate = downloaded_gb / elapsed if elapsed > 0 else 0
eta_min = int((total_gb - downloaded_gb) / rate / 60) if rate > 0 else 0
print(f'[BATCH] {downloaded_gb:.2f}GB/{total_gb:.2f}GB downloaded ({pct:.1f}%), '
      f'elapsed {elapsed // 60}m, ETA ~{eta_min}m remaining')
" | while IFS= read -r batch_line; do log "${batch_line}"; done

  if [[ "${#CHUNK_NAMES[@]}" -ge "${CHUNK_SIZE}" || ( "${STOP}" -eq 1 && "${#CHUNK_NAMES[@]}" -gt 0 ) ]]; then
    process_chunk CHUNK_NAMES
    CHUNK_NAMES=()
  fi
done < "${TARGET_ROWS_FILE}"

if [[ "${#CHUNK_NAMES[@]}" -gt 0 ]]; then
  process_chunk CHUNK_NAMES
  CHUNK_NAMES=()
fi

DAT_PRODUCED_COUNT=$(find "${OUT_DIR}" -maxdepth 2 -name '*.dat' 2>/dev/null | wc -l | tr -d ' ')
REPORT_COUNT=$(find "${RESULTS_DIR}" -name '*.manifest.json' 2>/dev/null | wc -l | tr -d ' ')

log "[DONE]  stream_process_evict batch complete"
log "[INFO]  Targets attempted: ${processed_in_run}/${TOTAL}"
log "[INFO]  Downloaded: ${DOWNLOADED_COUNT} (~${DOWNLOADED_GB}GB)"
log "[INFO]  Newly processed: ${NEWLY_PROCESSED_COUNT}"
log "[INFO]  Evicted (raw payload deleted after processing): ${EVICTED_COUNT}"
log "[INFO]  Reused local DAT (no raw payload present): ${LOCAL_DAT_REUSE_COUNT}"
log "[INFO]  Already processed (download skipped): ${ALREADY_PROCESSED_COUNT}"
log "[INFO]  Failed: ${FAILED_COUNT}"
log "[INFO]  Total .dat files now in ${OUT_DIR}: ${DAT_PRODUCED_COUNT}"
log "[INFO]  Total candidate report manifests in ${RESULTS_DIR}: ${REPORT_COUNT}"

RUN_OK=1
COMPLETED_COUNT=$((NEWLY_PROCESSED_COUNT + ALREADY_PROCESSED_COUNT))
if [[ "${COMPLETED_COUNT}" -ne "${TOTAL}" || "${FAILED_COUNT}" -gt 0 ]]; then
  RUN_OK=0
fi

# Guard against exactly the incident this project has already hit twice
# (see AGENTS.md's DATA COLLECTION STATUS REPORTING DIRECTIVE and CLAUDE.md's
# "Git-Add-Safe Label Regeneration" note): running this script against a
# scratch/test manifest must never auto-commit a status entry to the
# canonical, tracked docs/data_collection_status.json. Only manifests under
# the official data_selection/batch_manifests/ directory (real, committed
# batch plans) are eligible to record status; anything else (data_cache/
# scratch slices, ad hoc test manifests) is skipped silently here.
MANIFEST_REALPATH="$(cd "$(dirname "${MANIFEST}")" && pwd)/$(basename "${MANIFEST}")"
CANONICAL_MANIFEST_DIR="${REPO_ROOT}/data_selection/batch_manifests"
RECORD_STATUS=0
case "${MANIFEST_REALPATH}" in
  "${CANONICAL_MANIFEST_DIR}"/*) RECORD_STATUS=1 ;;
esac
if [[ -n "${STATUS_KEY:-}" ]]; then
  RECORD_STATUS=1
fi

TECHNO_SEARCH_BIN="${REPO_ROOT}/.venv/bin/techno-search"
if [[ "${RECORD_STATUS}" -eq 0 ]]; then
  log "[INFO]  Manifest is not under data_selection/batch_manifests/ -- skipping status-manifest record (scratch/test run)."
elif [[ -x "${TECHNO_SEARCH_BIN}" ]]; then
  SUMMARY_JSON="$(
    DOWNLOADED_NAMES="$(printf '%s\n' "${DOWNLOADED_NAMES[@]:-}")" \
    NEWLY_PROCESSED_NAMES="$(printf '%s\n' "${NEWLY_PROCESSED_NAMES[@]:-}")" \
    EVICTED_NAMES="$(printf '%s\n' "${EVICTED_NAMES[@]:-}")" \
    LOCAL_DAT_REUSE_NAMES="$(printf '%s\n' "${LOCAL_DAT_REUSE_NAMES[@]:-}")" \
    ALREADY_PROCESSED_NAMES="$(printf '%s\n' "${ALREADY_PROCESSED_NAMES[@]:-}")" \
    FAILED_NAMES="$(printf '%s\n' "${FAILED_NAMES[@]:-}")" \
    FAILED_REASONS="$(printf '%s\n' "${FAILED_REASONS[@]:-}")" \
    MANIFEST="${MANIFEST}" \
    TOTAL="${TOTAL}" \
    ATTEMPTED="${processed_in_run}" \
    DOWNLOADED_COUNT="${DOWNLOADED_COUNT}" \
    DOWNLOADED_GB="${DOWNLOADED_GB}" \
    NEWLY_PROCESSED_COUNT="${NEWLY_PROCESSED_COUNT}" \
    EVICTED_COUNT="${EVICTED_COUNT}" \
    LOCAL_DAT_REUSE_COUNT="${LOCAL_DAT_REUSE_COUNT}" \
    ALREADY_PROCESSED_COUNT="${ALREADY_PROCESSED_COUNT}" \
    COMPLETED_COUNT="${COMPLETED_COUNT}" \
    FAILED_COUNT="${FAILED_COUNT}" \
    DAT_PRODUCED_COUNT="${DAT_PRODUCED_COUNT}" \
    REPORT_COUNT="${REPORT_COUNT}" \
    RUN_OK="${RUN_OK}" \
    "${VENV_PYTHON}" -c '
import json
import os

from techno_search import __version__


def _lines(name):
    text = os.environ.get(name, "")
    return [line for line in text.split("\n") if line]


failed_names = _lines("FAILED_NAMES")
failed_reasons = _lines("FAILED_REASONS")
downloaded_names = _lines("DOWNLOADED_NAMES")
newly_processed_names = _lines("NEWLY_PROCESSED_NAMES")
evicted_names = _lines("EVICTED_NAMES")
local_dat_reuse_names = _lines("LOCAL_DAT_REUSE_NAMES")
already_processed_names = _lines("ALREADY_PROCESSED_NAMES")
summary = {
    "ok": os.environ["RUN_OK"] == "1",
    "app_version": __version__,
    "manifest": os.environ["MANIFEST"],
    "acquisition_mode": "stream_process_evict",
    "raw_retention_policy": "evicted_after_candidate_report_generation",
    "total_targets_in_manifest": int(os.environ["TOTAL"]),
    "targets_attempted": int(os.environ["ATTEMPTED"]),
    "downloaded_count": int(os.environ["DOWNLOADED_COUNT"]),
    "downloaded_gb": float(os.environ["DOWNLOADED_GB"]),
    "downloaded_targets": downloaded_names,
    "newly_processed_count": int(os.environ["NEWLY_PROCESSED_COUNT"]),
    "newly_processed_targets": newly_processed_names,
    "evicted_count": int(os.environ["EVICTED_COUNT"]),
    "evicted_targets": evicted_names,
    "local_dat_reuse_count": int(os.environ["LOCAL_DAT_REUSE_COUNT"]),
    "local_dat_reuse_targets": local_dat_reuse_names,
    "already_processed_count": int(os.environ["ALREADY_PROCESSED_COUNT"]),
    "already_processed_targets": already_processed_names,
    "completed_count": int(os.environ["COMPLETED_COUNT"]),
    "failed_count": int(os.environ["FAILED_COUNT"]),
    "dat_files_total": int(os.environ["DAT_PRODUCED_COUNT"]),
    "candidate_report_manifests_total": int(os.environ["REPORT_COUNT"]),
    "failed_targets": [
        {"target": t, "reason": r} for t, r in zip(failed_names, failed_reasons)
    ],
}
print(json.dumps(summary))
'
  )"
  STATUS_KEY="${STATUS_KEY:-stream_process_evict_batch__$(basename "${MANIFEST}" .json)}"
  if ! "${TECHNO_SEARCH_BIN}" record-data-collection-status \
    --script "${STATUS_KEY}" \
    --summary-json "${SUMMARY_JSON}" \
    >/dev/null 2>&1; then
    if [[ "${REQUIRE_STATUS_RECORD}" -eq 1 ]]; then
      log "[ERROR] Required Hunter acquisition status record failed."
      exit 1
    fi
    log "[INFO]  Status manifest update/commit skipped (non-fatal)."
  fi
fi

echo ""
echo "Scientific guardrail:"
echo "  Downloaded files and derived hit tables/candidate reports are local"
echo "  calibration and generalisation aids only. No file or report entry"
echo "  constitutes a technosignature detection or authorizes external"
echo "  submission."

if [[ "${RUN_OK}" -eq 0 ]]; then
  exit 1
fi
