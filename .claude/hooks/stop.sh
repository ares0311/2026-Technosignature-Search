#!/bin/bash
# Stop hook: blocks session end if recent git work doesn't close a production gap.
set -euo pipefail

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
)

# Read stdin (JSON from Claude Code)
INPUT=$(cat)
STOP_HOOK_ACTIVE=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('stop_hook_active', False))" 2>/dev/null || echo "False")

# Only enforce on non-hook-triggered stops
if [ "$STOP_HOOK_ACTIVE" = "True" ]; then
  exit 0
fi

# Check if there are any uncommitted or recently committed changes
RECENT_MSG=$(git log -1 --format="%s %b" 2>/dev/null | tr '[:upper:]' '[:lower:]' || echo "")
STAGED=$(git diff --cached --name-only 2>/dev/null || echo "")

if [ -z "$RECENT_MSG" ] && [ -z "$STAGED" ]; then
  exit 0
fi

COMBINED="$RECENT_MSG $STAGED"

for gap in "${TIER1_GAPS[@]}"; do
  if echo "$COMBINED" | grep -qi "$gap"; then
    exit 0
  fi
done

# If we have staged changes or a recent commit that doesn't reference a gap, warn
if [ -n "$STAGED" ]; then
  cat << 'WARNING'
{"decision": "block", "reason": "PRIMARY DIRECTIVE VIOLATION: Staged changes do not reference a Tier 1 or Tier 2 production gap. You are only permitted to commit work that gets this project to live production. Review CLAUDE.md and docs/PRODUCTION_READINESS.md before proceeding."}
WARNING
  exit 0
fi

exit 0
