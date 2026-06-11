#!/usr/bin/env bash
# run_calibration_corpus_pipeline.sh
#
# End-to-end calibration corpus pipeline:
#   H5 directory → turboSETI (.dat files) → provenance JSON sidecars →
#   noise-threshold-calibration gate check → pass/fail report
#
# Usage:
#   bash scripts/run_calibration_corpus_pipeline.sh <H5_DIR> [OPTIONS]
#
# Arguments:
#   H5_DIR      Directory containing downloaded .h5 files from the BL archive.
#               Defaults to data/calibration_corpus/
#
# Options:
#   --workers N         Number of parallel turboSETI workers (default: 4)
#   --out-dir DIR       Directory for .dat output (default: H5_DIR)
#   --snr-min FLOAT     Minimum SNR for turboSETI hits (default: 10.0)
#   --max-drift FLOAT   Max drift rate Hz/s for turboSETI (default: 4.0)
#   --skip-turboseti    Skip turboSETI; use existing .dat files in OUT_DIR
#   --allow-dev         Pass --allow-development-fixtures to calibration CLI
#                       (development/testing only — skips human approval gate)
#   --dry-run           Print what would be done; do not execute
#   --help              Show this help
#
# Scientific guardrail:
#   Outputs of this script are local calibration aids only. Derived thresholds
#   must pass independent-method citizen-science review before pipeline use.
#   No result constitutes a detection claim or authorizes external submission.
#   Downloaded H5 files are Breakthrough Listen public archive data.
#   This script does NOT write or overwrite provenance sidecars automatically
#   for new targets — see PROVENANCE_TEMPLATE below and Item 3 of the
#   calibration corpus admission process.
#
# Provenance requirement:
#   Each .dat file must have a companion .dat.provenance.json sidecar before
#   the noise-threshold-calibration gate will admit it. For NEW targets
#   (not Voyager 1), you must create the sidecar manually or via the
#   write_provenance_sidecar() helper. Required fields are documented
#   in docs/CALIBRATION_CORPUS_ADMISSION.md.
#
# Example (macOS, long run):
#   caffeinate -i bash scripts/run_calibration_corpus_pipeline.sh \
#       data/calibration_corpus/ --workers 12

set -euo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON="${REPO_ROOT}/.venv/bin/python"
TECHNO_SEARCH="${REPO_ROOT}/.venv/bin/techno-search"

# Scientific disclaimer — echoed before any real processing
DISCLAIMER="CALIBRATION CORPUS PIPELINE — LOCAL CALIBRATION AID ONLY.
Outputs are not scored candidates, detection claims, or validated thresholds.
Calibrated thresholds require independent-method citizen-science review
before production use."

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
H5_DIR="${REPO_ROOT}/data/calibration_corpus"
OUT_DIR=""
WORKERS=4
SNR_MIN=10.0
MAX_DRIFT=4.0
SKIP_TURBOSETI=0
ALLOW_DEV=0
DRY_RUN=0

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --workers)       WORKERS="$2";       shift 2 ;;
        --out-dir)       OUT_DIR="$2";       shift 2 ;;
        --snr-min)       SNR_MIN="$2";       shift 2 ;;
        --max-drift)     MAX_DRIFT="$2";     shift 2 ;;
        --skip-turboseti) SKIP_TURBOSETI=1;  shift ;;
        --allow-dev)     ALLOW_DEV=1;        shift ;;
        --dry-run)       DRY_RUN=1;          shift ;;
        --help|-h)
            sed -n '/^# Usage:/,/^[^#]/p' "$0" | grep '^#' | sed 's/^# \?//'
            exit 0
            ;;
        -*)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
        *)
            H5_DIR="$1"
            shift
            ;;
    esac
done

# Resolve OUT_DIR default
if [[ -z "${OUT_DIR}" ]]; then
    OUT_DIR="${H5_DIR}"
fi

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
info()  { echo "[INFO]  $*"; }
warn()  { echo "[WARN]  $*" >&2; }
error() { echo "[ERROR] $*" >&2; }

run_or_dry() {
    if [[ "${DRY_RUN}" -eq 1 ]]; then
        echo "[DRY-RUN] $*"
    else
        "$@"
    fi
}

# ---------------------------------------------------------------------------
# Preflight checks
# ---------------------------------------------------------------------------
echo ""
echo "========================================================"
echo " ${DISCLAIMER}"
echo "========================================================"
echo ""

if [[ ! -f "${PYTHON}" ]]; then
    error "Python not found at ${PYTHON}. Run: python3 -m venv .venv && .venv/bin/pip install -e .[dev]"
    exit 1
fi

if [[ ! -f "${TECHNO_SEARCH}" ]]; then
    error "techno-search not found at ${TECHNO_SEARCH}."
    exit 1
fi

if [[ ! -d "${H5_DIR}" ]]; then
    if [[ "${SKIP_TURBOSETI}" -eq 1 ]]; then
        info "H5_DIR does not exist but --skip-turboseti given; proceeding with OUT_DIR only."
    else
        error "H5_DIR does not exist: ${H5_DIR}"
        error "Download H5 files first using scripts/download_bl_hits.sh or bl_fetch.py."
        error "See scripts/build_calibration_target_manifest.py for target list."
        exit 1
    fi
fi

# ---------------------------------------------------------------------------
# Step 1: Run turboSETI on each H5 file
# ---------------------------------------------------------------------------
if [[ "${SKIP_TURBOSETI}" -eq 0 ]]; then
    info "Step 1: Running turboSETI on H5 files in ${H5_DIR}"
    info "  Workers : ${WORKERS}"
    info "  SNR min : ${SNR_MIN}"
    info "  Max drift: ${MAX_DRIFT} Hz/s"
    info "  Output  : ${OUT_DIR}"
    echo ""

    H5_COUNT=$(find "${H5_DIR}" -maxdepth 1 -name "*.h5" 2>/dev/null | wc -l | tr -d ' ')
    if [[ "${H5_COUNT}" -eq 0 ]]; then
        warn "No .h5 files found in ${H5_DIR}."
        warn "Download H5 files first. Proceeding to calibration gate check with existing .dat files."
    else
        info "Found ${H5_COUNT} H5 file(s) to process."
        echo ""

        run_or_dry "${PYTHON}" "${SCRIPT_DIR}/bl_fetch.py" run-turboseti \
            --h5-dir "${H5_DIR}" \
            --out-dir "${OUT_DIR}" \
            --workers "${WORKERS}" \
            --snr-min "${SNR_MIN}" \
            --max-drift "${MAX_DRIFT}"
    fi
else
    info "Step 1: Skipped (--skip-turboseti). Using existing .dat files in ${OUT_DIR}."
fi

echo ""

# ---------------------------------------------------------------------------
# Step 2: Report provenance sidecar status
# ---------------------------------------------------------------------------
info "Step 2: Checking provenance sidecars in ${OUT_DIR}"

DAT_COUNT=$(find "${OUT_DIR}" -maxdepth 2 -name "*.dat" 2>/dev/null | wc -l | tr -d ' ')
PROV_COUNT=0
MISSING_PROV=()

if [[ "${DAT_COUNT}" -eq 0 ]]; then
    warn "No .dat files found in ${OUT_DIR}."
else
    while IFS= read -r dat_file; do
        prov_file="${dat_file}.provenance.json"
        if [[ -f "${prov_file}" ]]; then
            PROV_COUNT=$((PROV_COUNT + 1))
        else
            MISSING_PROV+=("$(basename "${dat_file}")")
        fi
    done < <(find "${OUT_DIR}" -maxdepth 2 -name "*.dat" 2>/dev/null | sort)

    info "  .dat files found        : ${DAT_COUNT}"
    info "  Provenance sidecars     : ${PROV_COUNT}"
    info "  Missing sidecars        : ${#MISSING_PROV[@]}"
    echo ""

    if [[ "${#MISSING_PROV[@]}" -gt 0 ]]; then
        warn "The following .dat files are missing provenance sidecars:"
        for f in "${MISSING_PROV[@]}"; do
            warn "  MISSING: ${f}.provenance.json"
        done
        echo ""
        warn "These files will be SKIPPED by the calibration gate."
        warn "To create sidecars, see docs/CALIBRATION_CORPUS_ADMISSION.md"
        warn "or use the admission helper:"
        warn "  .venv/bin/python scripts/write_calibration_provenance.py \\"
        warn "      --dat-file <file>.dat \\"
        warn "      --target-id <HIP_ID> \\"
        warn "      --cadence-id <gbt-HIP-mjdXXXXX-blcYY> \\"
        warn "      --epoch-utc <YYYY-MM-DD>"
        echo ""
    fi
fi

echo ""

# ---------------------------------------------------------------------------
# Step 3: Run noise-threshold-calibration gate
# ---------------------------------------------------------------------------
info "Step 3: Running noise-threshold-calibration gate on ${OUT_DIR}"

CAL_FLAGS=""
if [[ "${ALLOW_DEV}" -eq 1 ]]; then
    CAL_FLAGS="--allow-development-fixtures"
    warn "Using --allow-development-fixtures: bypasses human approval gate (dev/test only)"
fi

GATE_RESULT_FILE="${OUT_DIR}/calibration_gate_result.json"

if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "[DRY-RUN] ${TECHNO_SEARCH} noise-threshold-calibration ${OUT_DIR} ${CAL_FLAGS}"
    echo "[DRY-RUN] Gate result would be written to: ${GATE_RESULT_FILE}"
    exit 0
fi

if [[ "${DAT_COUNT}" -eq 0 && "${SKIP_TURBOSETI}" -eq 0 ]]; then
    error "No .dat files to analyze. Aborting calibration gate."
    exit 1
fi

set +e
GATE_JSON=$(${TECHNO_SEARCH} noise-threshold-calibration "${OUT_DIR}" ${CAL_FLAGS} 2>&1)
GATE_EXIT=$?
set -e

echo "${GATE_JSON}" | tee "${GATE_RESULT_FILE}"
echo ""

# ---------------------------------------------------------------------------
# Step 4: Parse and report gate results
# ---------------------------------------------------------------------------
info "Step 4: Gate result summary"
echo ""

CALIBRATION_READY=$(echo "${GATE_JSON}" | "${PYTHON}" -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print('yes' if d.get('calibration_ready') else 'no')
except Exception:
    print('parse_error')
" 2>/dev/null)

GATES_PASSED=$(echo "${GATE_JSON}" | "${PYTHON}" -c "
import json, sys
try:
    d = json.load(sys.stdin)
    gates = d.get('acceptance_gates', {})
    passed = sum(1 for g in gates.values() if g.get('passed'))
    total = len(gates)
    print(f'{passed}/{total}')
except Exception:
    print('?')
" 2>/dev/null)

echo "  Calibration ready : ${CALIBRATION_READY}"
echo "  Gates passed      : ${GATES_PASSED}"
echo "  Result file       : ${GATE_RESULT_FILE}"
echo ""

if [[ "${CALIBRATION_READY}" == "yes" ]]; then
    echo "========================================================"
    echo " ALL CALIBRATION GATES PASSED."
    echo " Next step: citizen-science review of derived thresholds."
    echo " See docs/PRODUCTION_READINESS.md Tier 1 gap (calibrated"
    echo " scoring thresholds) for review requirements."
    echo "========================================================"
    echo ""
    exit 0
else
    echo "========================================================"
    echo " CALIBRATION GATES NOT YET PASSED (${GATES_PASSED})."
    echo ""
    echo " Common causes:"
    echo "   - Fewer than 3 cadences (need 3+ distinct H5/dat files)"
    echo "   - Fewer than 3 targets  (need 3+ different stellar targets)"
    echo "   - Fewer than 2 epochs   (need observations from 2+ dates)"
    echo "   - Fewer than 100 hits   (need more L-band turboSETI output)"
    echo "   - Missing provenance sidecars (see Step 2 warnings above)"
    echo "   - Provenance not fully approved (human review required)"
    echo ""
    echo " Download more H5 files:"
    echo "   .venv/bin/python scripts/build_calibration_target_manifest.py --list-targets"
    echo "   See scripts/download_bl_hits.sh for one-file examples."
    echo "========================================================"
    echo ""
    exit 1
fi
