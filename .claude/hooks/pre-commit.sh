#!/bin/bash
# Pre-commit hook: rejects git commits that don't close a named production gap.
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

TIER1_GAPS=(
  "real observation data"
  "real labeled dataset"
  "calibrated scoring threshold"
  "real site-specific rfi"
  "peer review"
  "real data ingestion"
  "real turboSETI"
  "real gaia"
  "real wise"
  "simbad cross-match"
  "learned scoring model"
  "multi-epoch"
  "ingest"
  "threshold tuning"
  "expert label"
  "production alignment"
  "primary directive"
  "session-start"
  "gitignore"
  "hook"
  "production gap"
  "tier 1"
  "tier 2"
)

for gap in "${TIER1_GAPS[@]}"; do
  if echo "$MSG" | grep -qi "$gap"; then
    exit 0
  fi
done

echo '{"decision": "block", "reason": "PRIMARY DIRECTIVE VIOLATION: Commit message does not reference a Tier 1 or Tier 2 production gap. Only work that gets this project to live production is permitted. See CLAUDE.md and docs/PRODUCTION_READINESS.md."}'
exit 0
