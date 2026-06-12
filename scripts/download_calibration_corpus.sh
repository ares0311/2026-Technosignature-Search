#!/usr/bin/env bash
# download_calibration_corpus.sh
#
# Download GBT H5 files from the Breakthrough Listen public archive for the
# calibration corpus. Designed to run from macOS with caffeinate.
#
# The script discovers available files by listing Apache directory listings
# on blpd0.ssl.berkeley.edu, then downloads H5 files resumably with curl.
#
# Usage:
#   caffeinate -i bash scripts/download_calibration_corpus.sh [OPTIONS]
#
# Options:
#   --out-dir DIR       Download destination (default: data/calibration_corpus)
#   --targets LIST      Comma-separated target IDs to download
#                       (default: HIP65803,HIP8102,HIP16537)
#   --files-per-target N  Max H5 files per target (default: 2)
#   --list-only         List discovered files without downloading
#   --dry-run           Show what would be downloaded; do not download
#   --skip-ssl          Skip SSL certificate verification (needed for blpd14)
#   --help              Show this help
#
# Archive access:
#   Primary: http://blpd0.ssl.berkeley.edu/{TARGET}/{NODE}/
#   Mirror:  https://blpd14.ssl.berkeley.edu/{TARGET}/{NODE}/
#
# NOTE: The BL archive is IP-restricted to U.S. academic networks from some
# access paths. Run this script from your local Mac, not a cloud environment.
# If you get 403 errors, the data may be accessible via VPN or by contacting
# the BL team at seti.berkeley.edu/opendata for alternative download access.
#
# After downloading:
#   caffeinate -i bash scripts/run_calibration_corpus_pipeline.sh data/calibration_corpus/
#
# Scientific guardrail:
#   Downloaded H5 files are Breakthrough Listen public archive observations.
#   They are calibration aids only and do not constitute detection claims.
#   Provenance sidecars must be created before the calibration gate admits files.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
OUT_DIR="${REPO_ROOT}/data/calibration_corpus"
TARGETS="HIP65803,HIP8102,HIP16537"
FILES_PER_TARGET=2
LIST_ONLY=0
DRY_RUN=0
SKIP_SSL=0
BL_BASE="http://blpd0.ssl.berkeley.edu"
BL_HTTPS_BASE="https://blpd14.ssl.berkeley.edu"

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out-dir)          OUT_DIR="$2";           shift 2 ;;
        --targets)          TARGETS="$2";           shift 2 ;;
        --files-per-target) FILES_PER_TARGET="$2";  shift 2 ;;
        --list-only)        LIST_ONLY=1;            shift ;;
        --dry-run)          DRY_RUN=1;              shift ;;
        --skip-ssl)         SKIP_SSL=1;             shift ;;
        --help|-h)
            grep '^#' "$0" | head -40 | sed 's/^# \?//'
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

CURL_OPTS=(-s --max-time 30)
if [[ "${SKIP_SSL}" -eq 1 ]]; then
    CURL_OPTS+=(-k)
fi

# ---------------------------------------------------------------------------
# Step 0: Preflight
# ---------------------------------------------------------------------------
echo ""
echo "========================================================"
echo " BL CALIBRATION CORPUS DOWNLOAD"
echo " Scientific guardrail: downloads are calibration aids only."
echo " No result constitutes a detection claim."
echo "========================================================"
echo ""

# Test archive accessibility
info "Testing archive accessibility..."
HTTP_CODE=$(curl "${CURL_OPTS[@]}" -o /dev/null -w "%{http_code}" \
    --max-time 10 "${BL_BASE}/" 2>/dev/null || echo "000")

if [[ "${HTTP_CODE}" == "200" || "${HTTP_CODE}" == "403" ]]; then
    info "Archive at ${BL_BASE} reachable (HTTP ${HTTP_CODE})."
    if [[ "${HTTP_CODE}" == "403" ]]; then
        warn "Got HTTP 403 — archive may be IP-restricted."
        warn "Trying target-specific paths (may still work for specific files)."
    fi
elif [[ "${HTTP_CODE}" == "000" ]]; then
    error "Cannot reach ${BL_BASE} — check network connectivity."
    error "If running from a cloud environment, try running from your local Mac."
    exit 1
else
    warn "Unexpected HTTP ${HTTP_CODE} from ${BL_BASE}."
fi

mkdir -p "${OUT_DIR}"
info "Output directory: ${OUT_DIR}"
echo ""

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

# List compute node directories for a target (blc07, blc17, etc.)
discover_nodes() {
    local target="$1"
    local url="${BL_BASE}/${target}/"
    curl "${CURL_OPTS[@]}" "${url}" 2>/dev/null \
        | grep -oE 'blc[0-9]+' \
        | sort -u \
        | head -5
}

# List H5 files in a node directory
discover_h5_files() {
    local target="$1"
    local node="$2"
    local url="${BL_BASE}/${target}/${node}/"
    curl "${CURL_OPTS[@]}" "${url}" 2>/dev/null \
        | grep -oE 'guppi_[0-9]+_[0-9]+_[^"]+\.h5' \
        | sort -u
}

# Download a single H5 file resumably
download_h5() {
    local url="$1"
    local out_file="$2"
    local filename
    filename="$(basename "${out_file}")"

    if [[ -f "${out_file}" ]]; then
        local existing_size
        existing_size=$(wc -c < "${out_file}" | tr -d ' ')
        info "  Resuming ${filename} (${existing_size} bytes already downloaded)..."
    else
        info "  Downloading ${filename}..."
    fi

    if [[ "${DRY_RUN}" -eq 1 ]]; then
        echo "    [DRY-RUN] curl -C - -L \"${url}\" -o \"${out_file}\""
        return 0
    fi

    local http_code
    http_code=$(curl "${CURL_OPTS[@]}" -C - -L \
        --connect-timeout 30 \
        --max-time 3600 \
        -w "%{http_code}" \
        "${url}" \
        -o "${out_file}" \
        2>/dev/null)

    if [[ "${http_code}" == "200" || "${http_code}" == "206" ]]; then
        local final_size
        final_size=$(wc -c < "${out_file}" | tr -d ' ')
        info "  OK — ${filename} (${final_size} bytes, HTTP ${http_code})"
        return 0
    else
        warn "  Download failed for ${filename}: HTTP ${http_code}"
        return 1
    fi
}

# ---------------------------------------------------------------------------
# Main discovery + download loop
# ---------------------------------------------------------------------------
IFS=',' read -ra TARGET_LIST <<< "${TARGETS}"
TOTAL_DOWNLOADED=0
TOTAL_SKIPPED=0
TOTAL_FAILED=0
DISCOVERED_TARGETS=()

for TARGET in "${TARGET_LIST[@]}"; do
    echo "--- Target: ${TARGET} ---"
    info "Discovering compute nodes for ${TARGET}..."

    NODES=$(discover_nodes "${TARGET}" 2>/dev/null || true)
    if [[ -z "${NODES}" ]]; then
        warn "No compute nodes found for ${TARGET} at ${BL_BASE}/${TARGET}/"
        warn "Possible causes: target directory name differs, or IP restriction."
        warn "Try listing manually: curl '${BL_BASE}/${TARGET}/'"
        echo ""
        TOTAL_SKIPPED=$((TOTAL_SKIPPED + 1))
        continue
    fi

    info "Found nodes: $(echo "${NODES}" | tr '\n' ' ')"
    DISCOVERED_TARGETS+=("${TARGET}")
    FILES_THIS_TARGET=0

    for NODE in ${NODES}; do
        [[ "${FILES_THIS_TARGET}" -ge "${FILES_PER_TARGET}" ]] && break

        info "Listing ${TARGET}/${NODE}/..."
        H5_FILES=$(discover_h5_files "${TARGET}" "${NODE}" 2>/dev/null || true)

        if [[ -z "${H5_FILES}" ]]; then
            warn "  No H5 files found in ${TARGET}/${NODE}/"
            continue
        fi

        for H5_FILE in ${H5_FILES}; do
            [[ "${FILES_THIS_TARGET}" -ge "${FILES_PER_TARGET}" ]] && break

            H5_URL="${BL_BASE}/${TARGET}/${NODE}/${H5_FILE}"
            OUT_FILE="${OUT_DIR}/${TARGET}_${NODE}_${H5_FILE}"

            if [[ "${LIST_ONLY}" -eq 1 ]]; then
                echo "  FOUND: ${H5_URL}"
                echo "    → ${OUT_FILE}"
                FILES_THIS_TARGET=$((FILES_THIS_TARGET + 1))
                continue
            fi

            if [[ -f "${OUT_FILE}" ]]; then
                EXISTING=$(wc -c < "${OUT_FILE}" | tr -d ' ')
                if [[ "${EXISTING}" -gt 10000000 ]]; then
                    info "  Already have ${H5_FILE} (${EXISTING} bytes) — skipping."
                    FILES_THIS_TARGET=$((FILES_THIS_TARGET + 1))
                    TOTAL_SKIPPED=$((TOTAL_SKIPPED + 1))
                    continue
                fi
            fi

            if download_h5 "${H5_URL}" "${OUT_FILE}"; then
                FILES_THIS_TARGET=$((FILES_THIS_TARGET + 1))
                TOTAL_DOWNLOADED=$((TOTAL_DOWNLOADED + 1))
            else
                TOTAL_FAILED=$((TOTAL_FAILED + 1))
                warn "  Failed. Try: curl -v '${H5_URL}'"
            fi
        done
    done

    echo ""
done

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo "========================================================"
echo " DOWNLOAD SUMMARY"
echo "  Targets processed : ${#TARGET_LIST[@]}"
echo "  Files downloaded  : ${TOTAL_DOWNLOADED}"
echo "  Already present   : ${TOTAL_SKIPPED}"
echo "  Failed            : ${TOTAL_FAILED}"
echo "  Output directory  : ${OUT_DIR}"
echo "========================================================"
echo ""

if [[ "${LIST_ONLY}" -eq 1 ]]; then
    echo "List-only mode — no files downloaded."
    exit 0
fi

if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "Dry-run mode — no files downloaded."
    exit 0
fi

H5_COUNT=$(find "${OUT_DIR}" -maxdepth 1 -name "*.h5" 2>/dev/null | wc -l | tr -d ' ')
echo "H5 files now in ${OUT_DIR}: ${H5_COUNT}"
echo ""

if [[ "${H5_COUNT}" -ge 3 ]]; then
    echo "Next steps:"
    echo "  1. Run turboSETI + calibration gate:"
    echo "     caffeinate -i bash scripts/run_calibration_corpus_pipeline.sh ${OUT_DIR}"
    echo ""
    echo "  2. After turboSETI produces .dat files, create provenance sidecars:"
    echo "     for dat in ${OUT_DIR}/*.dat; do"
    echo "       .venv/bin/python scripts/write_calibration_provenance.py \\"
    echo "           --dat-file \"\$dat\" --approved"
    echo "     done"
    echo ""
    echo "  3. Re-run the calibration gate to check admission:"
    echo "     .venv/bin/techno-search noise-threshold-calibration ${OUT_DIR}"
else
    echo "Need at least 3 H5 files for calibration corpus (have ${H5_COUNT})."
    echo "Add more targets with --targets or --files-per-target."
    echo ""
    echo "Available BL targets (L-band survey):"
    echo "  HIP65803  (70 Virginis)       — multi-epoch, recommended"
    echo "  HIP8102   (tau Ceti)           — classic SETI target, multi-epoch"
    echo "  HIP16537  (epsilon Eridani)    — debris disk, multi-epoch"
    echo "  HIP99427  (ALREADY INGESTED)   — skip unless reprovisioning"
    echo ""
    echo "If 403 errors prevent download, the archive may require:"
    echo "  - Access from a U.S. university network (not VPN/cloud)"
    echo "  - Contacting: seti.berkeley.edu/opendata"
fi
