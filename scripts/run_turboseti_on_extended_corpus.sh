#!/usr/bin/env bash
# run_turboseti_on_extended_corpus.sh
#
# Run turboSETI FindDoppler on every HDF5 file in data/extended_corpus/
# that does not yet have a corresponding .dat hit table.  Idempotent.
#
# Parameters match bl_fetch.py run_turboseti():
#   max_drift = 4 Hz/s   (standard GBT L-band)
#   min_drift = 1e-4 Hz/s
#   snr       = 10        (lower threshold for sensitivity)
#
# Usage:
#   caffeinate -i bash scripts/run_turboseti_on_extended_corpus.sh \
#       [--corpus-dir PATH] [--dry-run]
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
DRY_RUN=false

info()  { echo "[$(date '+%H:%M:%S')] [INFO]  $*"; }
ok()    { echo "[$(date '+%H:%M:%S')] [OK]    $*"; }
warn()  { echo "[$(date '+%H:%M:%S')] [WARN]  $*" >&2; }
error() { echo "[$(date '+%H:%M:%S')] [ERROR] $*" >&2; }
step()  { echo ""; echo "[$(date '+%H:%M:%S')] === $* ==="; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --corpus-dir)  CORPUS_DIR="$2"; shift 2 ;;
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
info "Dry run:    ${DRY_RUN}"
echo ""

processed=0
skipped=0
failed=0

while IFS= read -r -d '' h5_file; do
    target_dir="$(dirname "${h5_file}")"
    target_name="$(basename "${target_dir}")"

    # Check if a .dat file already exists in this target directory
    existing_dat="$(find "${target_dir}" -maxdepth 1 -name "*.dat" | head -1)"
    if [[ -n "${existing_dat}" ]]; then
        info "[SKIP] ${target_name}: .dat already exists ($(basename "${existing_dat}"))"
        skipped=$((skipped + 1))
        continue
    fi

    info "[RUN]  ${target_name}: $(basename "${h5_file}")"

    if [[ "${DRY_RUN}" == "true" ]]; then
        info "[DRY]  Would run: ${VENV} ${BL_FETCH} run-turboseti ${h5_file} ${target_dir}"
        processed=$((processed + 1))
        continue
    fi

    if "${VENV}" "${BL_FETCH}" run-turboseti "${h5_file}" "${target_dir}"; then
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
