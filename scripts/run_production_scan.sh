#!/usr/bin/env bash
# run_production_scan.sh — Continuous-loop production anomaly scan
#
# Usage:
#   caffeinate -i bash scripts/run_production_scan.sh \
#       --dat-dir data/bl_hits [--output-dir results/prod_scan_output] \
#       [--history-file results/scan_history.ndjson] \
#       [--workers N] [--continuous] [--force-rescan]
#
# What this script does:
#   1. validate-all         — safety gate; aborts if any gate fails
#   2. Show target queue    — ranked by selection score (new targets first)
#   3. LOOP until Ctrl+C:
#        a. Pick the highest-priority pending target (new > re-scan)
#        b. If re-scanning: show prior result and prompt for parent_run_id link
#        c. Run the pipeline on that target
#        d. Record the scan result in the history file
#        e. Print one-line result (scan index / stellar / score / escalation)
#        f. If queue exhausted: report + sleep-poll (--continuous) or exit
#   4. Post-scan summary    — scan-summary, cross-target-rfi, escalation gate,
#                             review-dashboard, prod-write-outcomes
#
# Scientific guardrail:
#   No output of this script constitutes a detection claim or authorizes
#   external submission. Results are local citizen-science scheduling aids only.
#   validate-all must pass before scanning proceeds.
#
# macOS long-run:
#   caffeinate -i bash scripts/run_production_scan.sh --dat-dir data/bl_hits

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TECHNO_SEARCH="${REPO_ROOT}/.venv/bin/techno-search"
PYTHON="${REPO_ROOT}/.venv/bin/python"
RESULTS_BASE="${REPO_ROOT}/results"
SCANS_DIR="${RESULTS_BASE}/scans"

info()  { echo "[$(date '+%H:%M:%S')] [INFO]  $*"; }
warn()  { echo "[$(date '+%H:%M:%S')] [WARN]  $*" >&2; }
error() { echo "[$(date '+%H:%M:%S')] [ERROR] $*" >&2; }
step()  { echo ""; echo "=== $* ==="; }

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
DAT_DIR=""
OUTPUT_DIR="${RESULTS_BASE}/prod_scan_output"
HISTORY_FILE="${RESULTS_BASE}/scan_history.ndjson"
WORKERS=1
CONTINUOUS=false
FORCE_RESCAN=false
POLL_INTERVAL=60  # seconds between queue-exhaustion polls

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dat-dir)        DAT_DIR="$2";        shift 2 ;;
        --output-dir)     OUTPUT_DIR="$2";     shift 2 ;;
        --history-file)   HISTORY_FILE="$2";   shift 2 ;;
        --workers)        WORKERS="$2";        shift 2 ;;
        --continuous)     CONTINUOUS=true;     shift   ;;
        --force-rescan)   FORCE_RESCAN=true;   shift   ;;
        --poll-interval)  POLL_INTERVAL="$2";  shift 2 ;;
        *)
            error "Unknown argument: $1"
            echo "Usage: bash $0 --dat-dir PATH [--output-dir PATH] [--history-file PATH]"
            echo "             [--workers N] [--continuous] [--force-rescan]"
            exit 1
            ;;
    esac
done

if [[ -z "${DAT_DIR}" ]]; then
    error "--dat-dir is required (path to directory containing turboSETI .dat files)"
    exit 1
fi

if [[ ! -d "${DAT_DIR}" ]]; then
    error "dat-dir not found: ${DAT_DIR}"
    exit 1
fi

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
RUN_ID=$(echo "${RUN_ID_JSON}" | "${PYTHON}" \
    -c "import json,sys; print(json.load(sys.stdin)['run_id'])")

SCAN_DIR="${RESULTS_BASE}/scans/${RUN_ID}"
SCAN_SUMMARY_PATH="${SCAN_DIR}/${RUN_ID}_scan_summary.json"
REVIEW_DASHBOARD_PATH="${SCAN_DIR}/${RUN_ID}_review_dashboard.json"
mkdir -p "${SCAN_DIR}" "${OUTPUT_DIR}"

echo ""
echo "============================================================"
echo " PRODUCTION ANOMALY SCAN — ${RUN_ID}"
echo " Scientific guardrail: No result constitutes a detection"
echo " claim or authorizes external submission."
echo "============================================================"
echo ""
info "Run ID:       ${RUN_ID}"
info "dat-dir:      ${DAT_DIR}"
info "output-dir:   ${OUTPUT_DIR}"
info "history-file: ${HISTORY_FILE}"
info "Continuous:   ${CONTINUOUS}"
info "Force-rescan: ${FORCE_RESCAN}"
echo ""

# ---------------------------------------------------------------------------
# Step 1: validate-all (abort on failure)
# ---------------------------------------------------------------------------
step "Step 1: validate-all (safety gate)"
info "Running validate-all — scan will abort if any gate fails ..."

set +e
VALIDATE_JSON=$("${TECHNO_SEARCH}" validate-all 2>&1)
VALIDATE_EXIT=$?
set -e

echo "${VALIDATE_JSON}" | tee "${SCAN_DIR}/validate_all.json"

if [[ ${VALIDATE_EXIT} -ne 0 ]]; then
    error "validate-all FAILED — scan aborted."
    error "Fix all validation failures before running a production scan."
    exit 1
fi
info "validate-all: PASSED"

# ---------------------------------------------------------------------------
# Step 2: Show initial target queue
# ---------------------------------------------------------------------------
step "Step 2: Target queue (selection rationale)"

FORCE_ARG=""
if [[ "${FORCE_RESCAN}" == "true" ]]; then
    FORCE_ARG="--force"
fi

set +e
QUEUE_JSON=$("${TECHNO_SEARCH}" prod-target-queue \
    --dat-dir "${DAT_DIR}" \
    --history-file "${HISTORY_FILE}" \
    ${FORCE_ARG} 2>&1)
QUEUE_EXIT=$?
set -e

TOTAL_PENDING=$(echo "${QUEUE_JSON}" | "${PYTHON}" \
    -c "import json,sys; d=json.load(sys.stdin); print(d.get('pending_count',0))" 2>/dev/null || echo "?")

if [[ ${QUEUE_EXIT} -ne 0 ]]; then
    warn "prod-target-queue returned non-zero — continuing"
fi

info "Pending targets: ${TOTAL_PENDING}"
echo "${QUEUE_JSON}" | "${PYTHON}" -c "
import json, sys
d = json.load(sys.stdin)
for i, e in enumerate(d.get('queue', [])[:10]):
    mark = '*' if e['is_first_scan'] else ' '
    print(f\"  [{i+1:2d}]{mark} {e['target_stem']:<40} score={e['selection_score']:.4f}  ({e['rationale']})\")
if len(d.get('queue', [])) > 10:
    print(f\"  ... and {len(d['queue']) - 10} more\")
" 2>/dev/null || true

# ---------------------------------------------------------------------------
# Step 3: Continuous scan loop
# ---------------------------------------------------------------------------
step "Step 3: Scan loop (Ctrl+C to stop cleanly)"

STOPPING=0
TARGETS_SCANNED=0
TARGETS_FAILED=0
ESCALATIONS=0

# Trap SIGINT/SIGTERM — set flag; loop exits at top of next iteration.
trap 'STOPPING=1; echo ""; warn "Stop requested — finishing current target then exiting..."' INT TERM

while true; do
    if [[ "${STOPPING}" -eq 1 ]]; then
        info "Stopped by user."
        break
    fi

    # Rebuild queue every iteration so newly added .dat files are picked up.
    set +e
    QUEUE_JSON=$("${TECHNO_SEARCH}" prod-target-queue \
        --dat-dir "${DAT_DIR}" \
        --history-file "${HISTORY_FILE}" \
        ${FORCE_ARG} 2>/dev/null)
    QUEUE_EXIT=$?
    set -e

    PENDING=$(echo "${QUEUE_JSON}" | "${PYTHON}" \
        -c "import json,sys; d=json.load(sys.stdin); print(d.get('pending_count',0))" 2>/dev/null || echo "0")

    if [[ "${PENDING}" -eq 0 ]]; then
        if [[ "${CONTINUOUS}" == "true" ]]; then
            info "Queue exhausted. Polling for new targets every ${POLL_INTERVAL}s... (Ctrl+C to stop)"
            sleep "${POLL_INTERVAL}"
            continue
        else
            info "Queue exhausted — all ${TARGETS_SCANNED} target(s) scanned."
            break
        fi
    fi

    # Pick the top entry
    TARGET_STEM=$(echo "${QUEUE_JSON}" | "${PYTHON}" \
        -c "import json,sys; d=json.load(sys.stdin); print(d['queue'][0]['target_stem'])" 2>/dev/null)
    DAT_FILE=$(echo "${QUEUE_JSON}" | "${PYTHON}" \
        -c "import json,sys; d=json.load(sys.stdin); print(d['queue'][0]['dat_file'])" 2>/dev/null)
    RATIONALE=$(echo "${QUEUE_JSON}" | "${PYTHON}" \
        -c "import json,sys; d=json.load(sys.stdin); print(d['queue'][0]['rationale'])" 2>/dev/null)
    IS_FIRST=$(echo "${QUEUE_JSON}" | "${PYTHON}" \
        -c "import json,sys; d=json.load(sys.stdin); print(d['queue'][0]['is_first_scan'])" 2>/dev/null)
    LAST_SCORE=$(echo "${QUEUE_JSON}" | "${PYTHON}" \
        -c "import json,sys; d=json.load(sys.stdin); print(d['queue'][0].get('last_score') or '')" 2>/dev/null)
    LAST_PATHWAY=$(echo "${QUEUE_JSON}" | "${PYTHON}" \
        -c "import json,sys; d=json.load(sys.stdin); print(d['queue'][0].get('last_pathway') or '')" 2>/dev/null)

    echo ""
    info "--- Target: ${TARGET_STEM}"
    info "    Selection: ${RATIONALE}"

    # Re-scan: show prior result
    PARENT_RUN_ID_ARG=""
    if [[ "${IS_FIRST}" == "False" ]]; then
        info "    Previously scanned: score=${LAST_SCORE}  pathway=${LAST_PATHWAY}"
        info "    Linking this scan to prior run as parent_run_id=${RUN_ID}"
        PARENT_RUN_ID_ARG="--parent-run-id ${RUN_ID}"
    fi

    # Run the pipeline on this target
    TARGET_OUTPUT_DIR="${OUTPUT_DIR}/${TARGET_STEM}"
    mkdir -p "${TARGET_OUTPUT_DIR}"

    SCAN_START_TIME=$(date +%s)
    set +e
    PIPELINE_JSON=$("${TECHNO_SEARCH}" run-pipeline \
        "${DAT_FILE}" \
        --track radio \
        --output-dir "${TARGET_OUTPUT_DIR}" \
        --candidate-id "${TARGET_STEM}" 2>&1)
    PIPELINE_EXIT=$?
    set -e
    SCAN_END_TIME=$(date +%s)
    ELAPSED=$((SCAN_END_TIME - SCAN_START_TIME))

    # Extract score and pathway from the pipeline output JSON
    RESULT_JSON="${TARGET_OUTPUT_DIR}/${TARGET_STEM}.json"
    SCORE="0.0"
    PATHWAY="unknown"

    if [[ -f "${RESULT_JSON}" ]]; then
        SCORE=$(cat "${RESULT_JSON}" | "${PYTHON}" \
            -c "import json,sys; d=json.load(sys.stdin); print(d.get('scores',{}).get('signal_reality_confidence',0.0))" \
            2>/dev/null || echo "0.0")
        PATHWAY=$(cat "${RESULT_JSON}" | "${PYTHON}" \
            -c "import json,sys; d=json.load(sys.stdin); print(d.get('recommended_pathway','unknown'))" \
            2>/dev/null || echo "unknown")
    fi

    if [[ ${PIPELINE_EXIT} -ne 0 ]]; then
        warn "Pipeline failed for ${TARGET_STEM} (exit ${PIPELINE_EXIT}, ${ELAPSED}s)"
        TARGETS_FAILED=$((TARGETS_FAILED + 1))
        # Record failed scan so we don't retry endlessly
        "${TECHNO_SEARCH}" prod-record-scan \
            --target-stem "${TARGET_STEM}" \
            --run-id "${RUN_ID}" \
            --score 0.0 \
            --pathway "pipeline_failed" \
            --dat-file "${DAT_FILE}" \
            --history-file "${HISTORY_FILE}" \
            ${PARENT_RUN_ID_ARG} >/dev/null 2>&1 || true
        continue
    fi

    TARGETS_SCANNED=$((TARGETS_SCANNED + 1))

    # Check escalation
    ESC_FLAG=""
    if [[ -f "${RESULT_JSON}" ]]; then
        ESC_PASSES=$(cat "${RESULT_JSON}" | "${PYTHON}" \
            -c "
import json,sys
try:
    from techno_search.candidate_escalation import escalation_gate_check
    d=json.load(open('${RESULT_JSON}'))
    g=escalation_gate_check(d)
    print('YES' if g.get('passes') else 'no')
except Exception:
    print('no')
" 2>/dev/null || echo "no")
        if [[ "${ESC_PASSES}" == "YES" ]]; then
            ESC_FLAG=" *** ESCALATION ***"
            ESCALATIONS=$((ESCALATIONS + 1))
        fi
    fi

    # Print one-line result
    info "[OK] ${TARGET_STEM}  score=${SCORE}  pathway=${PATHWAY}  (${ELAPSED}s)${ESC_FLAG}"

    # Record scan in history
    "${TECHNO_SEARCH}" prod-record-scan \
        --target-stem "${TARGET_STEM}" \
        --run-id "${RUN_ID}" \
        --score "${SCORE}" \
        --pathway "${PATHWAY}" \
        --dat-file "${DAT_FILE}" \
        --history-file "${HISTORY_FILE}" \
        ${PARENT_RUN_ID_ARG} >/dev/null 2>&1 || \
        warn "Failed to record scan for ${TARGET_STEM}"
done

# ---------------------------------------------------------------------------
# Post-scan summary steps
# ---------------------------------------------------------------------------
step "Post-scan summary"

info "Targets scanned this run: ${TARGETS_SCANNED}"
info "Targets failed this run:  ${TARGETS_FAILED}"
info "Escalations flagged:      ${ESCALATIONS}"

if [[ "${TARGETS_SCANNED}" -eq 0 && "${TARGETS_FAILED}" -eq 0 ]]; then
    info "Nothing was scanned — skipping post-scan steps."
    exit 0
fi

# scan-summary across all results
if [[ -d "${RESULTS_BASE}" ]]; then
    info "Running scan-summary on ${RESULTS_BASE} ..."
    set +e
    SCAN_JSON=$("${TECHNO_SEARCH}" scan-summary "${RESULTS_BASE}" 2>&1)
    set -e
    echo "${SCAN_JSON}" | tee "${SCAN_SUMMARY_PATH}" >/dev/null
    TOTAL=$(echo "${SCAN_JSON}" | "${PYTHON}" \
        -c "import json,sys; d=json.load(sys.stdin); print(d.get('total_candidates',0))" 2>/dev/null || echo "?")
    info "Total candidates in results/: ${TOTAL}"
fi

# cross-target-rfi
set +e
RFI_JSON=$("${TECHNO_SEARCH}" cross-target-rfi-summary \
    --results-dir "${RESULTS_BASE}" 2>&1)
set -e
echo "${RFI_JSON}" | tee "${SCAN_DIR}/cross_target_rfi.json" >/dev/null
FLAGGED=$(echo "${RFI_JSON}" | "${PYTHON}" \
    -c "import json,sys; d=json.load(sys.stdin); print(d.get('flagged_count',0))" 2>/dev/null || echo "?")
info "Cross-target RFI flagged: ${FLAGGED}"

# review-dashboard
set +e
DASH_JSON=$("${TECHNO_SEARCH}" review-dashboard 2>&1)
set -e
echo "${DASH_JSON}" | tee "${REVIEW_DASHBOARD_PATH}" >/dev/null
NEEDS_ATTENTION=$(echo "${DASH_JSON}" | "${PYTHON}" \
    -c "import json,sys; d=json.load(sys.stdin); print(d.get('needs_attention', False))" 2>/dev/null || echo "False")
if [[ "${NEEDS_ATTENTION}" == "True" ]]; then
    warn "review-dashboard: NEEDS ATTENTION — check ${REVIEW_DASHBOARD_PATH}"
else
    info "review-dashboard: OK"
fi

# prod-write-outcomes
COMPLETED_AT_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
set +e
OUTCOME_JSON=$("${TECHNO_SEARCH}" prod-write-outcomes \
    --results-dir "${RESULTS_BASE}" \
    --run-dir "${SCAN_DIR}" \
    --run-id "${RUN_ID}" \
    --started-at-utc "${STARTED_AT_UTC}" \
    --scan-summary-path "${SCAN_SUMMARY_PATH}" 2>&1)
OUTCOME_EXIT=$?
set -e
echo "${OUTCOME_JSON}" | tee "${SCAN_DIR}/${RUN_ID}_outcome_summary.json" >/dev/null
if [[ ${OUTCOME_EXIT} -eq 0 ]]; then
    info "Production outcome ledgers written."
else
    warn "prod-write-outcomes returned non-zero — inspect outcome summary."
fi

# scan-history-summary
echo ""
info "Scan history summary:"
"${TECHNO_SEARCH}" scan-history-summary \
    --history-file "${HISTORY_FILE}" \
    --dat-dir "${DAT_DIR}" 2>/dev/null | "${PYTHON}" -c "
import json, sys
d = json.load(sys.stdin)
print(f\"  Total scans all-time: {d.get('total_scans',0)}\")
print(f\"  Unique targets:       {d.get('unique_targets_scanned',0)}\")
print(f\"  Re-scanned targets:   {d.get('re_scanned_targets',0)}\")
print(f\"  Still pending:        {d.get('pending_targets','?')}\")
" 2>/dev/null || true

# ---------------------------------------------------------------------------
# Final banner
# ---------------------------------------------------------------------------
echo ""
echo "============================================================"
echo " SCAN COMPLETE — ${RUN_ID}"
echo ""
echo " Scanned this run: ${TARGETS_SCANNED}"
echo " Failed this run:  ${TARGETS_FAILED}"
echo " Escalations:      ${ESCALATIONS}"
echo ""
echo " Scan output: ${SCAN_DIR}"
echo " Hit outputs: ${OUTPUT_DIR}"
echo " History:     ${HISTORY_FILE}"
echo ""
echo " NEXT STEP: Review ${RUN_ID}_follow_ups.json and"
echo " ${RUN_ID}_non_detections.json in ${SCAN_DIR}."
echo " Scientific guardrail: No result authorizes external"
echo " submission or constitutes a detection claim."
echo "============================================================"
echo ""

if [[ ${TARGETS_FAILED} -gt 0 ]]; then
    exit 1
fi
exit 0
