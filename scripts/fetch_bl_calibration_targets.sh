#!/usr/bin/env bash
# fetch_bl_calibration_targets.sh
#
# Discover and download GBT L-band H5 files from the Breakthrough Listen
# public archive for calibration corpus assembly, then run turboSETI.
#
# Prints verbose progress and ETA for every step.
#
# Usage:
#   caffeinate -i bash scripts/fetch_bl_calibration_targets.sh [OPTIONS]
#
# Options:
#   --targets LIST   Comma-separated targets (default: HIP65803,HIP8102,HIP16537)
#   --out-dir DIR    Output directory (default: data/calibration_corpus)
#   --discover-only  List available files; do not download
#   --no-turboseti   Download H5 only; skip turboSETI
#   --workers N      turboSETI parallel workers (default: 8)
#   --snr-min FLOAT  Minimum SNR for turboSETI (default: 10.0)
#   --help           Show this help
#
# Archive:
#   Primary: http://blpd0.ssl.berkeley.edu/{TARGET}/blc07/
#   Lists .h5 filenames via directory listing (HTML scrape).
#   Downloads first available single-coarse H5 (~50-200 MB per file).
#
# Scientific guardrail:
#   Downloaded files are BL public archive data — calibration aids only.
#   No result constitutes a detection claim or authorizes external submission.
#
# Example (macOS):
#   caffeinate -i bash scripts/fetch_bl_calibration_targets.sh
#   caffeinate -i bash scripts/fetch_bl_calibration_targets.sh \
#       --targets HIP65803 --discover-only

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON="${REPO_ROOT}/.venv/bin/python"
TECHNO_SEARCH="${REPO_ROOT}/.venv/bin/techno-search"

BL_BASE="http://blpd0.ssl.berkeley.edu"
# blc07 is the Cygnus-region campaign bank.  For targets not found there the
# script will probe ALL_BANKS in order and use the first bank with H5 files.
BANK="blc07"
ALL_BANKS="blc07 blc0 blc1 blc2 blc3 blc4 blc5 blc6 blc20 blc21 blc22 blc23"

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
TARGETS="HIP65803,HIP8102,HIP16537"
OUT_DIR="${REPO_ROOT}/data/calibration_corpus"
DISCOVER_ONLY=0
NO_TURBOSETI=0
WORKERS=8
SNR_MIN=10.0

# ---------------------------------------------------------------------------
# Logging helpers — always visible to terminal
# ---------------------------------------------------------------------------
info()  { echo "[$(date '+%H:%M:%S')] [INFO]  $*"; }
warn()  { echo "[$(date '+%H:%M:%S')] [WARN]  $*" >&2; }
error() { echo "[$(date '+%H:%M:%S')] [ERROR] $*" >&2; exit 1; }
step()  { echo ""; echo "[$(date '+%H:%M:%S')] ===== $* ====="; }

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --targets)    TARGETS="$2"; shift 2 ;;
        --out-dir)    OUT_DIR="$2"; shift 2 ;;
        --discover-only) DISCOVER_ONLY=1; shift ;;
        --no-turboseti)  NO_TURBOSETI=1; shift ;;
        --workers)    WORKERS="$2"; shift 2 ;;
        --snr-min)    SNR_MIN="$2"; shift 2 ;;
        --help)
            sed -n '/^# /p' "$0" | sed 's/^# //'
            exit 0 ;;
        *) error "Unknown option: $1" ;;
    esac
done

# Convert comma-separated to array
IFS=',' read -ra TARGET_LIST <<< "$TARGETS"
N_TARGETS="${#TARGET_LIST[@]}"

# ---------------------------------------------------------------------------
# Startup banner
# ---------------------------------------------------------------------------
echo ""
echo "============================================================"
echo " BL Calibration Target Fetcher"
echo " Targets (${N_TARGETS}): ${TARGETS}"
echo " Output:  ${OUT_DIR}"
echo " Archive: ${BL_BASE}/{TARGET}/${BANK}/"
echo " Mode:    $([ ${DISCOVER_ONLY} -eq 1 ] && echo 'DISCOVER ONLY' || echo 'DOWNLOAD + TURBOSET I')"
echo " Scientific guardrail: calibration aid only; no detection claims"
echo "============================================================"
echo ""

# ---------------------------------------------------------------------------
# Check dependencies
# ---------------------------------------------------------------------------
step "Checking dependencies"
command -v curl >/dev/null 2>&1 || error "curl is required but not found"
if [[ ${DISCOVER_ONLY} -eq 0 && ${NO_TURBOSETI} -eq 0 ]]; then
    "${PYTHON}" -c "import turbo_seti" 2>/dev/null \
        || warn "turbo_seti not importable — will skip turboSETI step"
fi
info "All checks passed"

# ---------------------------------------------------------------------------
# Create output directory
# ---------------------------------------------------------------------------
if [[ ${DISCOVER_ONLY} -eq 0 ]]; then
    mkdir -p "${OUT_DIR}"
    info "Output directory: ${OUT_DIR}"
fi

# ---------------------------------------------------------------------------
# Test archive connectivity
# ---------------------------------------------------------------------------
step "Testing archive connectivity to ${BL_BASE}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 \
    "${BL_BASE}/" 2>/dev/null || echo "000")
if [[ "${HTTP_CODE}" == "200" ]]; then
    info "Archive reachable (HTTP ${HTTP_CODE})"
elif [[ "${HTTP_CODE}" == "403" || "${HTTP_CODE}" == "301" || "${HTTP_CODE}" == "302" ]]; then
    info "Archive reachable — redirects OK (HTTP ${HTTP_CODE})"
else
    warn "Archive returned HTTP ${HTTP_CODE} — downloads may fail"
    warn "If connectivity fails, manually browse: ${BL_BASE}/"
fi

# ---------------------------------------------------------------------------
# Per-target processing
# ---------------------------------------------------------------------------
DOWNLOAD_COUNT=0
SKIP_COUNT=0
FAIL_COUNT=0

for i in "${!TARGET_LIST[@]}"; do
    TARGET="${TARGET_LIST[$i]}"
    STEP_NUM=$((i + 1))
    step "[${STEP_NUM}/${N_TARGETS}] Target: ${TARGET}"

    # Try the default bank first; if empty probe ALL_BANKS in order
    H5_FILES=""
    ACTIVE_BANK=""
    DIR_URL=""
    for TRY_BANK in ${BANK} ${ALL_BANKS}; do
        # Avoid re-trying the default bank if it equals the first ALL_BANKS entry
        [[ -n "${ACTIVE_BANK}" ]] && [[ "${TRY_BANK}" == "${BANK}" ]] && continue

        CANDIDATE_URL="${BL_BASE}/${TARGET}/${TRY_BANK}/"
        info "  Trying bank: ${TRY_BANK} — ${CANDIDATE_URL}"
        LISTING=$(curl -s --max-time 15 "${CANDIDATE_URL}" 2>/dev/null || true)
        [[ -z "${LISTING}" ]] && continue

        # Extract H5 filenames from HTML directory listing
        TRY_FILES=$(echo "${LISTING}" \
            | grep -oE '"guppi_[0-9]+_[0-9]+_[^"]+\.h5"' \
            | tr -d '"' \
            | sort \
            || true)
        if [[ -z "${TRY_FILES}" ]]; then
            TRY_FILES=$(echo "${LISTING}" \
                | grep -oE 'guppi_[0-9]+_[0-9]+_[A-Za-z0-9_]+\.[0-9]+\.h5' \
                | sort \
                || true)
        fi

        if [[ -n "${TRY_FILES}" ]]; then
            H5_FILES="${TRY_FILES}"
            ACTIVE_BANK="${TRY_BANK}"
            DIR_URL="${CANDIDATE_URL}"
            info "  Found H5 files in bank: ${TRY_BANK}"
            break
        fi
    done

    if [[ -z "${H5_FILES}" ]]; then
        warn "  No H5 files found for ${TARGET} in any probed bank"
        warn "  Probed banks: ${BANK} ${ALL_BANKS}"
        warn "  To inspect manually: curl '${BL_BASE}/${TARGET}/'"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        continue
    fi

    # Count and list
    H5_COUNT=$(echo "${H5_FILES}" | wc -l | tr -d ' ')
    info "  Found ${H5_COUNT} H5 file(s) for ${TARGET}:"
    echo "${H5_FILES}" | while read -r fname; do
        echo "    ${DIR_URL}${fname}"
    done

    if [[ ${DISCOVER_ONLY} -eq 1 ]]; then
        info "  [DISCOVER-ONLY] Skipping download"
        continue
    fi

    # Pick the first file (smallest/first index for calibration purposes)
    FIRST_H5=$(echo "${H5_FILES}" | head -1)
    DOWNLOAD_URL="${DIR_URL}${FIRST_H5}"
    OUT_FILE="${OUT_DIR}/${FIRST_H5}"
    DAT_FILE="${OUT_DIR}/${FIRST_H5%.h5}.dat"

    if [[ -f "${OUT_FILE}" ]]; then
        FILE_SIZE=$(du -sh "${OUT_FILE}" | cut -f1)
        info "  Already downloaded: ${OUT_FILE} (${FILE_SIZE}) — skipping"
        SKIP_COUNT=$((SKIP_COUNT + 1))
    else
        info "  Downloading: ${FIRST_H5}"
        info "  URL: ${DOWNLOAD_URL}"
        info "  Destination: ${OUT_FILE}"
        echo ""
        # --progress-bar: shows live speed + ETA in terminal
        curl --progress-bar -L --max-time 600 \
            -o "${OUT_FILE}" \
            "${DOWNLOAD_URL}" \
            || { warn "  Download failed for ${TARGET}"; FAIL_COUNT=$((FAIL_COUNT + 1)); continue; }
        echo ""
        FILE_SIZE=$(du -sh "${OUT_FILE}" | cut -f1)
        info "  [OK] Downloaded: ${FILE_SIZE}  ${OUT_FILE}"
        DOWNLOAD_COUNT=$((DOWNLOAD_COUNT + 1))
    fi

    # Run turboSETI unless skipped
    if [[ ${NO_TURBOSETI} -eq 0 ]]; then
        if "${PYTHON}" -c "import turbo_seti" 2>/dev/null; then
            if [[ -f "${DAT_FILE}" ]]; then
                info "  turboSETI already run: ${DAT_FILE} — skipping"
            else
                info "  Running turboSETI on ${FIRST_H5} (SNR >= ${SNR_MIN})..."
                T_START=$(date +%s)
                "${PYTHON}" scripts/bl_fetch.py run-turboseti \
                    "${OUT_FILE}" "${OUT_DIR}" \
                    --snr-min "${SNR_MIN}" \
                    && {
                        T_END=$(date +%s)
                        ELAPSED=$((T_END - T_START))
                        HIT_COUNT=$(grep -c "^[0-9]" "${DAT_FILE}" 2>/dev/null || echo "0")
                        info "  [OK] turboSETI done in ${ELAPSED}s — ${HIT_COUNT} hits → ${DAT_FILE}"
                    } \
                    || warn "  turboSETI failed for ${TARGET}"
            fi
        else
            warn "  turbo_seti not available — skipping turboSETI step"
            warn "  Install: .venv/bin/pip install turbo_seti"
        fi
    fi

done

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "============================================================"
echo " Fetch Summary"
echo "   Targets processed: ${N_TARGETS}"
echo "   Downloaded:        ${DOWNLOAD_COUNT}"
echo "   Skipped (exist):   ${SKIP_COUNT}"
echo "   Failed:            ${FAIL_COUNT}"
echo ""
if [[ ${DISCOVER_ONLY} -eq 0 ]]; then
    DAT_COUNT=$(find "${OUT_DIR}" -name "*.dat" 2>/dev/null | wc -l | tr -d ' ')
    H5_COUNT_DONE=$(find "${OUT_DIR}" -name "*.h5" 2>/dev/null | wc -l | tr -d ' ')
    echo "   H5 files in ${OUT_DIR}: ${H5_COUNT_DONE}"
    echo "   .dat files in ${OUT_DIR}: ${DAT_COUNT}"
fi
echo ""
echo " Next steps after successful download:"
echo "   1. Create provenance sidecars for each .dat:"
echo "      for dat in ${OUT_DIR}/*.dat; do"
echo "        .venv/bin/python scripts/write_calibration_provenance.py \\"
echo "            --dat-file \"\$dat\" --approved"
echo "      done"
echo ""
echo "   2. Run calibration pipeline:"
echo "      caffeinate -i bash scripts/run_calibration_corpus_pipeline.sh \\"
echo "          ${OUT_DIR} --skip-turboseti"
echo ""
echo " Scientific guardrail: downloads are calibration aids only;"
echo " no result constitutes a detection claim."
echo "============================================================"
