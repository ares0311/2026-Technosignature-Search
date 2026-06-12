#!/usr/bin/env bash
# download_calibration_corpus.sh
#
# Download pre-computed turboSETI hit tables from the Breakthrough Listen
# Open Data Archive (L-band survey) for use as calibration corpus inputs.
#
# Hit tables are small (KB–MB) pre-computed .dat files. No raw H5 files or
# turboSETI processing required.
#
# Usage:
#   caffeinate -i bash scripts/download_calibration_corpus.sh [OPTIONS]
#
# Options:
#   --out-dir DIR       Download destination (default: data/calibration_corpus)
#   --targets LIST      Comma-separated HIP target IDs
#                       (default: HIP99427,HIP17378,HIP45167,HIP65352,HIP74995)
#   --list-only         List URLs without downloading
#   --dry-run           Show what would be downloaded; do not download
#   --help              Show this help
#
# Archive:
#   https://blpd0.ssl.berkeley.edu/L_band_table/{TARGET}_hits.dat
#   (Enriquez et al. 2017 GBT L-band survey, publicly accessible, no auth)
#
# After downloading:
#   1. Create provenance sidecars (one per .dat):
#      for dat in data/calibration_corpus/*.dat; do
#        .venv/bin/python scripts/write_calibration_provenance.py \
#            --dat-file "$dat" --approved
#      done
#
#   2. Run the calibration gate:
#      .venv/bin/techno-search noise-threshold-calibration data/calibration_corpus/
#
# Scientific guardrail:
#   Downloaded hit tables are BL public archive data — calibration aids only.
#   No result constitutes a detection claim or authorizes external submission.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
OUT_DIR="${REPO_ROOT}/data/calibration_corpus"
# Targets from Enriquez et al. 2017 with known good hit counts
TARGETS="HIP99427,HIP17378,HIP45167,HIP65352,HIP74995"
LIST_ONLY=0
DRY_RUN=0

BL_BASE="https://blpd0.ssl.berkeley.edu/L_band_table"

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out-dir)  OUT_DIR="$2";   shift 2 ;;
        --targets)  TARGETS="$2";   shift 2 ;;
        --list-only) LIST_ONLY=1;   shift ;;
        --dry-run)  DRY_RUN=1;      shift ;;
        --help|-h)
            grep '^#' "$0" | head -35 | sed 's/^# \?//'
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

info()  { echo "[INFO]  $*"; }
warn()  { echo "[WARN]  $*" >&2; }
error() { echo "[ERROR] $*" >&2; }

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------
echo ""
echo "========================================================"
echo " BL CALIBRATION CORPUS DOWNLOAD"
echo " Source: ${BL_BASE}/"
echo " Scientific guardrail: downloads are calibration aids only."
echo " No result constitutes a detection claim."
echo "========================================================"
echo ""

# Test archive accessibility
info "Testing archive connectivity..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 \
    "${BL_BASE}/HIP99427_hits.dat" 2>/dev/null || echo "000")

if [[ "${HTTP_CODE}" == "200" ]]; then
    info "Archive reachable (HTTP 200)."
elif [[ "${HTTP_CODE}" == "000" ]]; then
    error "Cannot reach ${BL_BASE} — check network connectivity."
    exit 1
else
    warn "Unexpected HTTP ${HTTP_CODE} from archive preflight."
    warn "Will attempt downloads anyway; individual files may still succeed."
fi

if [[ "${LIST_ONLY}" -eq 0 && "${DRY_RUN}" -eq 0 ]]; then
    mkdir -p "${OUT_DIR}"
fi
info "Output directory: ${OUT_DIR}"
echo ""

# ---------------------------------------------------------------------------
# Download loop
# ---------------------------------------------------------------------------
IFS=',' read -ra TARGET_LIST <<< "${TARGETS}"
TOTAL_DOWNLOADED=0
TOTAL_SKIPPED=0
TOTAL_FAILED=0

for TARGET in "${TARGET_LIST[@]}"; do
    URL="${BL_BASE}/${TARGET}_hits.dat"
    OUT_FILE="${OUT_DIR}/${TARGET}_hits.dat"

    if [[ "${LIST_ONLY}" -eq 1 ]]; then
        echo "  ${URL}"
        echo "    → ${OUT_FILE}"
        continue
    fi

    if [[ "${DRY_RUN}" -eq 1 ]]; then
        echo "  [DRY-RUN] curl -L \"${URL}\" -o \"${OUT_FILE}\""
        continue
    fi

    # Skip if already present and looks valid (> 500 bytes, has a header line)
    if [[ -f "${OUT_FILE}" ]]; then
        SIZE=$(wc -c < "${OUT_FILE}" | tr -d ' ')
        if [[ "${SIZE}" -gt 500 ]] && grep -q "^# Source:" "${OUT_FILE}" 2>/dev/null; then
            info "${TARGET}: already present (${SIZE} bytes) — skipping."
            TOTAL_SKIPPED=$((TOTAL_SKIPPED + 1))
            continue
        else
            info "${TARGET}: file present but appears incomplete (${SIZE} bytes) — re-downloading."
        fi
    fi

    info "${TARGET}: downloading from ${URL}..."

    HTTP_CODE=$(curl -s -L \
        --connect-timeout 30 \
        --max-time 120 \
        -w "%{http_code}" \
        -o "${OUT_FILE}" \
        "${URL}" 2>/dev/null || echo "000")

    if [[ "${HTTP_CODE}" == "200" ]]; then
        SIZE=$(wc -c < "${OUT_FILE}" | tr -d ' ')
        if [[ "${SIZE}" -gt 500 ]] && grep -q "^# Source:" "${OUT_FILE}" 2>/dev/null; then
            info "${TARGET}: OK (${SIZE} bytes)"
            TOTAL_DOWNLOADED=$((TOTAL_DOWNLOADED + 1))
        else
            warn "${TARGET}: downloaded but file looks invalid (${SIZE} bytes, no header)"
            warn "  Expected: '# Source:${TARGET}' in first lines"
            warn "  Got first line: $(head -1 "${OUT_FILE}" 2>/dev/null | cat -v)"
            rm -f "${OUT_FILE}"
            TOTAL_FAILED=$((TOTAL_FAILED + 1))
        fi
    else
        warn "${TARGET}: HTTP ${HTTP_CODE} — file not available on this server."
        warn "  URL tried: ${URL}"
        rm -f "${OUT_FILE}" 2>/dev/null || true
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
    fi
done

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "========================================================"
echo " DOWNLOAD SUMMARY"
echo "  Targets attempted  : ${#TARGET_LIST[@]}"
echo "  Downloaded         : ${TOTAL_DOWNLOADED}"
echo "  Already present    : ${TOTAL_SKIPPED}"
echo "  Failed / not found : ${TOTAL_FAILED}"
echo "  Output directory   : ${OUT_DIR}"
echo "========================================================"
echo ""

if [[ "${LIST_ONLY}" -eq 1 || "${DRY_RUN}" -eq 1 ]]; then
    exit 0
fi

DAT_COUNT=$(find "${OUT_DIR}" -maxdepth 1 -name "*_hits.dat" 2>/dev/null | wc -l | tr -d ' ')
echo "Hit tables in ${OUT_DIR}: ${DAT_COUNT}"
echo ""

if [[ "${DAT_COUNT}" -ge 3 ]]; then
    echo "Next steps:"
    echo ""
    echo "  1. Create provenance sidecars (approves each file for local calibration):"
    echo "     for dat in ${OUT_DIR}/*.dat; do"
    echo "       .venv/bin/python scripts/write_calibration_provenance.py \\"
    echo "           --dat-file \"\$dat\" --approved"
    echo "     done"
    echo ""
    echo "  2. Run the calibration gate:"
    echo "     .venv/bin/techno-search noise-threshold-calibration ${OUT_DIR}"
    echo ""
    echo "  The gate needs >=3 cadences, >=3 targets, >=2 epochs, >=100 hits."
else
    echo "Downloaded ${DAT_COUNT} hit table(s). Need at least 3 for the calibration gate."
    echo ""
    echo "If downloads failed, try:"
    echo "  bash scripts/download_calibration_corpus.sh --list-only"
    echo ""
    echo "Or download manually:"
    for TARGET in "${TARGET_LIST[@]}"; do
        echo "  curl -L -o ${OUT_DIR}/${TARGET}_hits.dat ${BL_BASE}/${TARGET}_hits.dat"
    done
fi
