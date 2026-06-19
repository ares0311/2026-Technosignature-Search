#!/usr/bin/env bash
# run_production_scan.sh — compact production scan launcher
#
# Usage:
#   git pull origin main
#   caffeinate -i bash scripts/run_production_scan.sh
#
# Resume:
#   Run prod-runs, copy a real run_dir value, then pass that exact directory
#   to --resume-run-dir. Do not paste illustrative RUN-* shapes as commands.
#
# The Python CLI owns the workflow and terminal UX:
#   - spinner or compact progress while work is running
#   - one completed row per evaluated target
#   - full JSON artifacts under results/scans/RUN-*/
#
# Scientific guardrail:
#   No output constitutes a detection claim or authorizes external submission.
#   Results are local citizen-science scheduling aids only.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TECHNO_SEARCH="${REPO_ROOT}/.venv/bin/techno-search"
RESULTS_BASE="${REPO_ROOT}/results"
SCANS_DIR="${RESULTS_BASE}/scans"

if [[ ! -x "${TECHNO_SEARCH}" ]]; then
    echo "[ERROR] techno-search not found at ${TECHNO_SEARCH}" >&2
    echo "[ERROR] Run: ${REPO_ROOT}/.venv/bin/python -m pip install -e '.[dev]'" >&2
    exit 1
fi

exec "${TECHNO_SEARCH}" prod-scan \
    --results-dir "${RESULTS_BASE}" \
    --scans-dir "${SCANS_DIR}" \
    "$@"
