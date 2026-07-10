#!/bin/bash
# Pre-commit hook: rejects git commits that don't advance a named science phase.
set -euo pipefail

# Only intercept git commit commands
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input', {}).get('command', ''))" 2>/dev/null || echo "")

# Only intercept direct git commit commands (not rebase --exec, amend-only, or maintenance ops)
if ! echo "$COMMAND" | grep -qE "^git commit|git commit -m|git commit --message"; then
  exit 0
fi

# Allow amend-only operations (author fixes, metadata corrections)
if echo "$COMMAND" | grep -q "\-\-no-edit"; then
  exit 0
fi

# Extract the commit message from the command
MSG=$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]')

# Allowed commit categories — must reference science phase work or maintenance
ALLOWED_PATTERNS=(
  # Science phases
  "phase 0"
  "phase 1"
  "phase 2"
  "phase 3"
  "phase 4"
  "phase 5"
  # Scientific capability keywords
  "rfi rejection"
  "on/off cadence"
  "abacab"
  "turboseti"
  "meerkat"
  "semisupervised"
  "lightkurve"
  "tess"
  "kepler"
  "wise"
  "dyson"
  "jwst"
  "spectroscopy"
  "transit"
  "photometry"
  "infrared"
  "radio"
  "candidate"
  "technosignature"
  "real data"
  "real corpus"
  "adversarial"
  "multi-modal"
  # Infrastructure directly supporting science
  "delete"
  "remove"
  "strip"
  "clean"
  "runbook"
  "pipeline"
  "ingest"
  "download"
  "hook"
  "gitignore"
  "production"
  "primary directive"
  "session-start"
  "agents.md"
  "claude.md"
  "production_readiness"
  "stratified"
  "sampling"
  # Bug fixes
  "fix"
  "bug"
  "repair"
  "correct"
  "update"
  "rewrite"
  # Test and validation
  "test"
  "validate"
  "ci"
)

for pattern in "${ALLOWED_PATTERNS[@]}"; do
  if echo "$MSG" | grep -qi "$pattern"; then
    exit 0
  fi
done

python3 - <<'PYJSON'
import json

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": (
            "PRIMARY DIRECTIVE VIOLATION: Commit does not advance multi-modal "
            "technosignature search (Phases 0-5). See AGENTS.md PRIMARY DIRECTIVE "
            "and FIVE-PHASE SCIENCE ROADMAP. Every commit must implement scientific "
            "capability, fix a real bug blocking science, or delete misaligned code."
        )
    }
}))
PYJSON
exit 0
