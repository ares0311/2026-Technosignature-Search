#!/usr/bin/env bash
# run_production_scan.sh — Single-command production anomaly scan
#
# Usage:
#   caffeinate -i bash scripts/run_production_scan.sh [--dat-dir PATH] [--workers N]
#
# Steps:
#   1. validate-all      — safety gate; aborts if any gate fails
#   2. scan-summary      — rank candidates from existing results/
#   3. cross-target-rfi-summary --results-dir  — flag cross-target RFI
#   4. escalation-gate-check  — check any candidate_review_packet manifests
#   5. review-dashboard  — operator scheduling summary
#   6. prod-write-outcomes — write run manifest, non-detections, follow-ups
#
# Scientific guardrail:
#   No output of this script constitutes a detection claim or authorizes
#   external submission. Results are local citizen-science scheduling aids only.
#   validate-all must pass before scanning proceeds.
#
# macOS long-run:
#   caffeinate -i bash scripts/run_production_scan.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TECHNO_SEARCH="${REPO_ROOT}/.venv/bin/techno-search"
RESULTS_BASE="${REPO_ROOT}/results"

info()  { echo "[$(date '+%H:%M:%S')] [INFO]  $*"; }
warn()  { echo "[$(date '+%H:%M:%S')] [WARN]  $*" >&2; }
error() { echo "[$(date '+%H:%M:%S')] [ERROR] $*" >&2; }
step()  { echo ""; echo "=== $* ==="; }

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------
if [[ ! -f "${TECHNO_SEARCH}" ]]; then
    error "techno-search not found at ${TECHNO_SEARCH}"
    error "Run: .venv/bin/python -m pip install -e '.[dev,science]'"
    exit 1
fi

STARTED_AT_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
RUN_ID_JSON=$("${TECHNO_SEARCH}" prod-run-id)
RUN_ID=$(echo "${RUN_ID_JSON}" | "${REPO_ROOT}/.venv/bin/python" \
    -c "import json,sys; print(json.load(sys.stdin)['run_id'])")
SCAN_DIR="${RESULTS_BASE}/scans/${RUN_ID}"
SCAN_SUMMARY_PATH="${SCAN_DIR}/${RUN_ID}_scan_summary.json"
REVIEW_DASHBOARD_PATH="${SCAN_DIR}/${RUN_ID}_review_dashboard.json"

mkdir -p "${SCAN_DIR}"

echo ""
echo "============================================================"
echo " PRODUCTION ANOMALY SCAN — ${RUN_ID}"
echo " Scientific guardrail: No result constitutes a detection"
echo " claim or authorizes external submission."
echo "============================================================"
echo ""
info "Run ID: ${RUN_ID}"
info "Scan output dir: ${SCAN_DIR}"

# ---------------------------------------------------------------------------
# Step 1: validate-all (abort on any failure)
# ---------------------------------------------------------------------------
step "Step 1/6: validate-all (safety gate)"
info "Running validate-all — scan will abort if any gate fails ..."

set +e
VALIDATE_JSON=$("${TECHNO_SEARCH}" validate-all 2>&1)
VALIDATE_EXIT=$?
set -e

echo "${VALIDATE_JSON}" | tee "${SCAN_DIR}/validate_all.json"

if [[ ${VALIDATE_EXIT} -ne 0 ]]; then
    error "validate-all FAILED — scan aborted."
    error "Fix all validation failures before running a production scan."
    echo '{"ok": false, "reason": "validate_all_failed", "run_id": "'"${RUN_ID}"'"}' \
        > "${SCAN_SUMMARY_PATH}"
    cp "${SCAN_SUMMARY_PATH}" "${SCAN_DIR}/scan_summary.json"
    exit 1
fi
info "validate-all: PASSED"

# ---------------------------------------------------------------------------
# Step 2: scan-summary (rank candidates from results/)
# ---------------------------------------------------------------------------
step "Step 2/6: scan-summary (rank candidates)"

if [[ -d "${RESULTS_BASE}" ]]; then
    info "Loading candidates from ${RESULTS_BASE} ..."
    set +e
    SCAN_JSON=$("${TECHNO_SEARCH}" scan-summary "${RESULTS_BASE}" 2>&1)
    SCAN_EXIT=$?
    set -e
    echo "${SCAN_JSON}" | tee "${SCAN_SUMMARY_PATH}"
    cp "${SCAN_SUMMARY_PATH}" "${SCAN_DIR}/scan_summary.json"
    if [[ ${SCAN_EXIT} -ne 0 ]]; then
        warn "scan-summary returned non-zero — continuing"
    else
        TOTAL=$(echo "${SCAN_JSON}" | "${REPO_ROOT}/.venv/bin/python" \
            -c "import json,sys; d=json.load(sys.stdin); print(d.get('total_candidates',0))" 2>/dev/null || echo "?")
        info "Total candidates ranked: ${TOTAL}"
    fi
else
    warn "No results/ directory found — skipping scan-summary"
    echo '{"ok": false, "reason": "no_results_dir", "total_candidates": 0}' \
        > "${SCAN_SUMMARY_PATH}"
    cp "${SCAN_SUMMARY_PATH}" "${SCAN_DIR}/scan_summary.json"
fi

# ---------------------------------------------------------------------------
# Step 3: cross-target-rfi-summary
# ---------------------------------------------------------------------------
step "Step 3/6: cross-target-rfi-summary (flag RFI across targets)"

set +e
RFI_JSON=$("${TECHNO_SEARCH}" cross-target-rfi-summary \
    --results-dir "${RESULTS_BASE}" 2>&1)
RFI_EXIT=$?
set -e

echo "${RFI_JSON}" | tee "${SCAN_DIR}/cross_target_rfi.json"

if [[ ${RFI_EXIT} -eq 0 ]]; then
    FLAGGED=$(echo "${RFI_JSON}" | "${REPO_ROOT}/.venv/bin/python" \
        -c "import json,sys; d=json.load(sys.stdin); print(d.get('flagged_count',0))" 2>/dev/null || echo "?")
    info "Cross-target RFI flagged: ${FLAGGED}"
else
    warn "cross-target-rfi-summary returned non-zero — continuing"
fi

# ---------------------------------------------------------------------------
# Step 4: escalation-gate-check on candidate_review_packet manifests
# ---------------------------------------------------------------------------
step "Step 4/6: escalation-gate-check (top candidates)"

ESCALATION_COUNT=0
ESCALATION_DIR="${SCAN_DIR}/escalations"
mkdir -p "${ESCALATION_DIR}"

# Find any candidate JSON reports that reached candidate_review_packet pathway
while IFS= read -r manifest_file; do
    # Only check manifests where recommended_pathway is candidate_review_packet
    PATHWAY=$("${REPO_ROOT}/.venv/bin/python" -c "
import json, sys
try:
    d = json.load(open('${manifest_file}'))
    print(d.get('recommended_pathway', ''))
except Exception:
    print('')
" 2>/dev/null || echo "")

    if [[ "${PATHWAY}" == "candidate_review_packet" ]]; then
        CANDIDATE_JSON="${manifest_file%.manifest.json}.json"
        if [[ -f "${CANDIDATE_JSON}" ]]; then
            CAND_ID=$(basename "${CANDIDATE_JSON}" .json)
            info "  Running escalation gate on: ${CAND_ID}"
            set +e
            ESC_JSON=$("${TECHNO_SEARCH}" escalation-gate-check "${CANDIDATE_JSON}" 2>&1)
            ESC_EXIT=$?
            set -e
            echo "${ESC_JSON}" > "${ESCALATION_DIR}/${CAND_ID}_escalation.json"
            ESCALATION_COUNT=$((ESCALATION_COUNT + 1))
        fi
    fi
done < <(find "${RESULTS_BASE}" -name "*.manifest.json" 2>/dev/null | sort)

if [[ ${ESCALATION_COUNT} -eq 0 ]]; then
    info "No candidate_review_packet candidates found — escalation gate skipped"
    echo '{"escalation_count": 0, "note": "no candidate_review_packet candidates"}' \
        > "${ESCALATION_DIR}/summary.json"
else
    info "Escalation gate checked: ${ESCALATION_COUNT} candidate(s)"
fi

# ---------------------------------------------------------------------------
# Step 5: review-dashboard
# ---------------------------------------------------------------------------
step "Step 5/6: review-dashboard (operator summary)"

set +e
DASH_JSON=$("${TECHNO_SEARCH}" review-dashboard 2>&1)
DASH_EXIT=$?
set -e

echo "${DASH_JSON}" | tee "${REVIEW_DASHBOARD_PATH}"
cp "${REVIEW_DASHBOARD_PATH}" "${SCAN_DIR}/review_dashboard.json"

NEEDS_ATTENTION=$(echo "${DASH_JSON}" | "${REPO_ROOT}/.venv/bin/python" \
    -c "import json,sys; d=json.load(sys.stdin); print(d.get('needs_attention', False))" 2>/dev/null || echo "False")

if [[ "${NEEDS_ATTENTION}" == "True" ]]; then
    warn "review-dashboard: NEEDS ATTENTION — check ${SCAN_DIR}/review_dashboard.json"
else
    info "review-dashboard: OK"
fi

# ---------------------------------------------------------------------------
# Step 6: production outcome ledgers
# ---------------------------------------------------------------------------
step "Step 6/6: prod-write-outcomes (run ledgers)"

set +e
OUTCOME_JSON=$("${TECHNO_SEARCH}" prod-write-outcomes \
    --results-dir "${RESULTS_BASE}" \
    --run-dir "${SCAN_DIR}" \
    --run-id "${RUN_ID}" \
    --started-at-utc "${STARTED_AT_UTC}" \
    --scan-summary-path "${SCAN_SUMMARY_PATH}" 2>&1)
OUTCOME_EXIT=$?
set -e

echo "${OUTCOME_JSON}" | tee "${SCAN_DIR}/${RUN_ID}_outcome_summary.json"

if [[ ${OUTCOME_EXIT} -eq 0 ]]; then
    info "Production outcome ledgers written"
else
    warn "prod-write-outcomes returned non-zero — inspect outcome summary"
fi

# ---------------------------------------------------------------------------
# Final summary
# ---------------------------------------------------------------------------
echo ""
echo "============================================================"
echo " SCAN COMPLETE — ${RUN_ID}"
echo ""
echo " Output directory: ${SCAN_DIR}"
echo "   validate_all.json"
echo "   ${RUN_ID}_manifest.json"
echo "   ${RUN_ID}_scan_summary.json"
echo "   ${RUN_ID}_non_detections.json"
echo "   ${RUN_ID}_follow_ups.json"
echo "   cross_target_rfi.json"
echo "   escalations/"
echo "   ${RUN_ID}_review_dashboard.json"
echo ""
echo " NEXT STEP: Review ${RUN_ID}_follow_ups.json and ${RUN_ID}_non_detections.json."
echo " Scientific guardrail: No result authorizes external"
echo " submission or constitutes a detection claim."
echo "============================================================"
echo ""
