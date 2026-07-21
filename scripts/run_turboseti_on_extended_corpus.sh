#!/usr/bin/env bash
# run_turboseti_on_extended_corpus.sh
#
# Run turboSETI FindDoppler on every HDF5 file in data/extended_corpus/
# that does not yet have a corresponding .dat hit table.  Idempotent.
#
# Parameters are explicit for the approved coarse-resolution `.0002.h5` corpus;
# the generic bl_fetch.py helper retains its fine-resolution default.
#   max_drift = 10 Hz/s  (first nonzero bin for approved BL .0002 products)
#   min_drift = 1e-4 Hz/s
#   snr       = 10        (lower threshold for sensitivity)
#
# Usage:
#   caffeinate -i bash scripts/run_turboseti_on_extended_corpus.sh \
#       [--corpus-dir PATH] [--max-drift HZ_S] [--min-drift HZ_S] \
#       [--snr N] [--dry-run]
#
# Outputs:
#   .dat files are written alongside each H5 file in their target directory.
#   After this script succeeds, run:
#     caffeinate -i bash scripts/run_pipeline_on_bl_data.sh \
#         --dat-dir data/extended_corpus
#
# Scientific guardrail:
#   Hit tables produced here are local calibration and generalisation aids.
#   No hit table entry constitutes a technosignature detection or authorizes
#   external submission.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV="${REPO_ROOT}/.venv/bin/python"
BL_FETCH="${SCRIPT_DIR}/bl_fetch.py"

CORPUS_DIR="${REPO_ROOT}/data/extended_corpus"
MAX_DRIFT="10"
MIN_DRIFT="0.0001"
SNR_THRESHOLD="10"
DRY_RUN=false
SOURCE_URL=""
APPROVED_REAL_DATA=false

info()  { echo "[$(date '+%H:%M:%S')] [INFO]  $*"; }
ok()    { echo "[$(date '+%H:%M:%S')] [OK]    $*"; }
warn()  { echo "[$(date '+%H:%M:%S')] [WARN]  $*" >&2; }
error() { echo "[$(date '+%H:%M:%S')] [ERROR] $*" >&2; }
step()  { echo ""; echo "[$(date '+%H:%M:%S')] === $* ==="; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --corpus-dir)  CORPUS_DIR="$2"; shift 2 ;;
        --max-drift)   MAX_DRIFT="$2"; shift 2 ;;
        --min-drift)   MIN_DRIFT="$2"; shift 2 ;;
        --snr)         SNR_THRESHOLD="$2"; shift 2 ;;
        --source-url)  SOURCE_URL="$2"; shift 2 ;;
        --approved-real-data) APPROVED_REAL_DATA=true; shift ;;
        --dry-run)     DRY_RUN=true;   shift   ;;
        -h|--help)
            sed -n '2,30p' "$0" | grep '^#' | sed 's/^# \?//'
            exit 0
            ;;
        *) error "Unknown argument: $1"; exit 1 ;;
    esac
done

if [[ ! -d "${CORPUS_DIR}" ]]; then
    error "Corpus directory not found: ${CORPUS_DIR}"
    error "Run scripts/download_bl_extended_corpus.sh first."
    exit 1
fi

step "turboSETI extended corpus processing"
info "Corpus dir: ${CORPUS_DIR}"
info "Max drift: ${MAX_DRIFT} Hz/s"
info "Min drift: ${MIN_DRIFT} Hz/s"
info "SNR:       ${SNR_THRESHOLD}"
info "Dry run:    ${DRY_RUN}"
echo ""

processed=0
skipped=0
failed=0

dat_max_drift_rate() {
    local dat_file="$1"
    awk -F '\t' '
        /^#/ {
            for (i = 1; i <= NF; i++) {
                if ($i ~ /max_drift_rate:/) {
                    split($i, parts, ":")
                    gsub(/^[[:space:]]+|[[:space:]]+$/, "", parts[2])
                    print parts[2]
                    exit
                }
            }
        }
    ' "${dat_file}"
}

drift_ceiling_is_adequate() {
    local existing="$1"
    local required="$2"
    awk -v existing="${existing}" -v required="${required}" \
        'BEGIN { exit !((existing + 0) >= (required + 0)) }'
}

while IFS= read -r -d '' h5_file; do
    target_dir="$(dirname "${h5_file}")"
    target_name="$(basename "${target_dir}")"

    # Check if a .dat file already exists in this target directory
    existing_dat="$(find "${target_dir}" -maxdepth 1 -name "*.dat" | head -1)"
    if [[ -n "${existing_dat}" ]]; then
        existing_max_drift="$(dat_max_drift_rate "${existing_dat}")"
        if [[ -z "${existing_max_drift}" ]] || drift_ceiling_is_adequate "${existing_max_drift}" "${MAX_DRIFT}"; then
            info "[SKIP] ${target_name}: .dat already exists ($(basename "${existing_dat}"))"
            skipped=$((skipped + 1))
            continue
        fi
        warn "[REPROCESS] ${target_name}: existing .dat max drift ${existing_max_drift} Hz/s is below requested ${MAX_DRIFT} Hz/s"
    fi

    info "[RUN]  ${target_name}: $(basename "${h5_file}")"

    if [[ "${DRY_RUN}" == "true" ]]; then
        info "[DRY]  Would run: ${VENV} ${BL_FETCH} run-turboseti ${h5_file} ${target_dir} --max-drift ${MAX_DRIFT} --min-drift ${MIN_DRIFT} --snr ${SNR_THRESHOLD}"
        processed=$((processed + 1))
        continue
    fi

    provenance_args=()
    if [[ "${APPROVED_REAL_DATA}" == "true" ]]; then
        provenance_args+=(--approved-real-data --source-url "${SOURCE_URL}")
    fi
    if "${VENV}" "${BL_FETCH}" run-turboseti "${h5_file}" "${target_dir}" \
        --max-drift "${MAX_DRIFT}" \
        --min-drift "${MIN_DRIFT}" \
        --snr "${SNR_THRESHOLD}" \
        "${provenance_args[@]}"; then
        new_dat="$(find "${target_dir}" -maxdepth 1 -name "*.dat" | head -1)"
        if [[ -n "${new_dat}" ]]; then
            ok "${target_name}: produced $(basename "${new_dat}")"
            processed=$((processed + 1))
        else
            warn "${target_name}: turboSETI succeeded but no .dat found — zero hits?"
            processed=$((processed + 1))
        fi
    else
        error "${target_name}: turboSETI failed"
        failed=$((failed + 1))
    fi
done < <(find "${CORPUS_DIR}" -maxdepth 2 -name "*.h5" -print0 | sort -z)

echo ""
step "Summary"
info "Processed : ${processed}"
info "Skipped   : ${skipped} (already had .dat)"
info "Failed    : ${failed}"

if [[ "${failed}" -gt 0 ]]; then
    error "Some targets failed — see output above."
    exit 1
fi

echo ""
echo "Scientific guardrail:"
echo "  Hit tables produced here are local calibration and generalisation aids."
echo "  No hit table entry constitutes a technosignature detection or"
echo "  authorizes external submission."
echo ""

if [[ "${DRY_RUN}" == "false" && "${processed}" -gt 0 ]]; then
    echo "Next steps:"
    echo "  1. Build candidate reports from the new hit tables:"
    echo "       caffeinate -i bash scripts/run_pipeline_on_bl_data.sh \\"
    echo "           --dat-dir data/extended_corpus"
    echo "  2. Run the production scan over all extended corpus targets:"
    echo "       caffeinate -i bash scripts/run_production_scan.sh \\"
    echo "           --dat-dir data/extended_corpus"
fi
