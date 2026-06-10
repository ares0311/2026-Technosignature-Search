#!/usr/bin/env bash
# run_pipeline_on_bl_data.sh — run the techno-search pipeline on downloaded BL hit tables
#
# Prerequisites:
#   1. Run scripts/setup_data_dirs.sh
#   2. Run scripts/download_bl_hits.sh (or manually place .dat files in ~/technosignature-data/bl_hits/)
#
# Run (macOS — use caffeinate to prevent sleep during long pipeline run):
#   git pull origin main
#   caffeinate -i bash scripts/run_pipeline_on_bl_data.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_ROOT="${TECHNO_DATA_DIR:-$HOME/technosignature-data}"
BL_HITS_DIR="$DATA_ROOT/bl_hits"
PIPELINE_OUT="$DATA_ROOT/pipeline_out"

VENV_CLI="$REPO_ROOT/.venv/bin/techno-search"
VENV_PYTHON="$REPO_ROOT/.venv/bin/python"

if [[ ! -f "$VENV_CLI" ]]; then
    echo "ERROR: techno-search CLI not found at $VENV_CLI"
    echo "Sync main, activate .venv, and install the project before retrying."
    exit 1
fi

AUDIT_JSON=$(
    "$VENV_PYTHON" "$REPO_ROOT/scripts/audit_bl_observation_artifacts.py" \
        "$BL_HITS_DIR" --require-approved
) || {
    echo "ERROR: No human-approved real observation hit tables are available."
    echo "Synthetic, invalid, and unverified files are excluded from production runs."
    echo "Review docs/REAL_OBSERVATION_INTAKE.md and complete Human Gate 1."
    exit 1
}

DAT_FILES=()
while IFS= read -r approved_path; do
    [[ -n "$approved_path" ]] && DAT_FILES+=("$approved_path")
done < <(
    printf '%s' "$AUDIT_JSON" |
        "$VENV_PYTHON" -c \
            'import json,sys; data=json.load(sys.stdin); print("\n".join(a["path"] for a in data["artifacts"] if a["approved_for_pipeline"]))'
)

echo "Running pipeline on BL hit tables in: $BL_HITS_DIR"
echo "Output directory: $PIPELINE_OUT"
echo ""

mkdir -p "$PIPELINE_OUT"

CADENCE_MANIFEST="$REPO_ROOT/configs/gbt_hip99427_cadence_v1.json"
CADENCE_ID=$(
    "$VENV_PYTHON" -c \
        'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["cadence_id"])' \
        "$CADENCE_MANIFEST"
)
CADENCE_CSV="$BL_HITS_DIR/$CADENCE_ID.csv"

if [[ -f "$CADENCE_CSV" ]]; then
    "$VENV_PYTHON" -c \
        'import sys; from pathlib import Path; from techno_search.gbt_cadence import cadence_candidate_context; cadence_candidate_context(Path(sys.argv[1]))' \
        "$CADENCE_CSV"
    CADENCE_OUT="$PIPELINE_OUT/$CADENCE_ID"
    echo "--- Processing approved cadence: $CADENCE_ID ---"
    mkdir -p "$CADENCE_OUT"
    "$VENV_CLI" run-pipeline \
        "$CADENCE_CSV" \
        --track radio \
        --output-dir "$CADENCE_OUT" \
        --candidate-id "$CADENCE_ID"
    echo ""
    echo "Pipeline run complete: approved cadence report in $CADENCE_OUT"
    exit 0
fi

SUCCESS=0
FAILED=0

for DAT_FILE in "${DAT_FILES[@]}"; do
    BASENAME=$(basename "$DAT_FILE" .dat)
    OUT_DIR="$PIPELINE_OUT/$BASENAME"

    echo "--- Processing: $BASENAME ---"
    mkdir -p "$OUT_DIR"

    if "$VENV_CLI" run-pipeline \
        "$DAT_FILE" \
        --track radio \
        --output-dir "$OUT_DIR" 2>&1; then
        echo "  OK: output in $OUT_DIR"
        SUCCESS=$((SUCCESS + 1))
    else
        echo "  FAILED (see above for error)"
        FAILED=$((FAILED + 1))
    fi
    echo ""
done

echo "Pipeline run complete: $SUCCESS succeeded, $FAILED failed"
echo ""

if [[ $SUCCESS -gt 0 ]]; then
    echo "Review output reports:"
    find "$PIPELINE_OUT" -name "*.md" | head -10
fi
