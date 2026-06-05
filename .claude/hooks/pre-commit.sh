#!/bin/bash
# Pre-commit hook: rejects commits that don't close a named production gap.
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
  "production alignment"
  "primary directive"
  "session-start"
  "gitignore"
  "hook"
)

MSG=$(git log -1 --format="%s %b" 2>/dev/null | tr '[:upper:]' '[:lower:]' || echo "")

for gap in "${TIER1_GAPS[@]}"; do
  if echo "$MSG" | grep -qi "$gap"; then
    exit 0
  fi
done

echo "PRIMARY DIRECTIVE VIOLATION: Commit does not reference a Tier 1 or Tier 2 production gap."
echo "Only work that gets this project to live production is permitted."
echo "See CLAUDE.md and docs/PRODUCTION_READINESS.md."
exit 1
