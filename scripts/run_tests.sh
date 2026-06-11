#!/usr/bin/env bash
# scripts/run_tests.sh — stoppable, resumable test runner
#
# Stop at any time with Ctrl+C. Progress is saved per test file.
# Re-run to pick up exactly where you left off.
#
# Usage:
#   caffeinate -i bash scripts/run_tests.sh              # run all, skip already-passed
#   caffeinate -i bash scripts/run_tests.sh --reset      # clear progress and run all
#   caffeinate -i bash scripts/run_tests.sh --failed     # rerun only previous failures
#   caffeinate -i bash scripts/run_tests.sh --reset --failed  # clear and run failures
#
# State is stored in .test_progress/ (gitignored).

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${REPO_ROOT}/.venv/bin/python"
PROGRESS_DIR="${REPO_ROOT}/.test_progress"
PASSED_DIR="${PROGRESS_DIR}/passed"
FAILED_FILE="${PROGRESS_DIR}/failed.txt"

# ── Argument parsing ──────────────────────────────────────────────────────────
RESET=0
FAILED_ONLY=0
EXTRA_ARGS=()

for arg in "$@"; do
    case "$arg" in
        --reset)  RESET=1 ;;
        --failed) FAILED_ONLY=1 ;;
        *)        EXTRA_ARGS+=("$arg") ;;
    esac
done

# ── Reset ─────────────────────────────────────────────────────────────────────
if [[ $RESET -eq 1 ]]; then
    echo "Clearing test progress..."
    rm -rf "$PROGRESS_DIR"
fi

mkdir -p "$PASSED_DIR"
[[ -f "$FAILED_FILE" ]] || touch "$FAILED_FILE"

# ── Interrupt handler ─────────────────────────────────────────────────────────
trap 'echo -e "\n\nStopped. Progress saved — re-run to continue from here." ; exit 130' INT TERM

# ── Collect files ─────────────────────────────────────────────────────────────
mapfile -t ALL_TESTS < <(find "${REPO_ROOT}/tests" -name "test_*.py" | sort)

if [[ $FAILED_ONLY -eq 1 ]]; then
    if [[ ! -s "$FAILED_FILE" ]]; then
        echo "No failures recorded. Run without --failed first."
        exit 0
    fi
    mapfile -t TEST_FILES < "$FAILED_FILE"
    echo "=== Rerunning ${#TEST_FILES[@]} previously failed file(s) ==="
    echo ""
else
    TEST_FILES=("${ALL_TESTS[@]}")
    total_files=${#TEST_FILES[@]}
    already_passed=$(find "$PASSED_DIR" -name "*.pass" 2>/dev/null | wc -l | tr -d ' ')
    remaining=$((total_files - already_passed))
    echo "=== Resumable Test Runner ==="
    printf "    %d total files, %d already passed, %d to run\n" \
        "$total_files" "$already_passed" "$remaining"
    echo ""
fi

# Clear failed file — will repopulate during this run
> "$FAILED_FILE"

# ── Run ───────────────────────────────────────────────────────────────────────
passed=0
failed=0
skipped=0

for test_file in "${TEST_FILES[@]}"; do
    key="${test_file#${REPO_ROOT}/}"
    key="${key//\//_}"
    pass_marker="${PASSED_DIR}/${key}.pass"

    if [[ -f "$pass_marker" ]] && [[ $FAILED_ONLY -eq 0 ]]; then
        ((skipped++)) || true
        continue
    fi

    rel="${test_file#${REPO_ROOT}/}"
    printf "  %-65s " "$rel"

    if "$PYTHON" -m pytest "$test_file" -q --tb=short \
           --no-header "${EXTRA_ARGS[@]}" > /tmp/_ts_test_out 2>&1; then
        touch "$pass_marker"
        ((passed++)) || true
        # Show the pytest summary line (e.g. "5 passed in 0.12s")
        tail -1 /tmp/_ts_test_out | tr -d '\n'
        echo ""
    else
        rm -f "$pass_marker"
        echo "$test_file" >> "$FAILED_FILE"
        ((failed++)) || true
        echo "FAILED"
        echo ""
        cat /tmp/_ts_test_out
        echo ""
    fi
done

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════"
printf "  Passed:  %d\n" "$passed"
printf "  Failed:  %d\n" "$failed"
printf "  Skipped (already passed): %d\n" "$skipped"
echo "════════════════════════════════════════"

if [[ $failed -gt 0 ]]; then
    echo ""
    echo "Rerun failures:  caffeinate -i bash scripts/run_tests.sh --failed"
    exit 1
fi
