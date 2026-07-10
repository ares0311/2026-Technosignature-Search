#!/bin/bash
# Stop hook: non-blocking session-end reminder.
# This hook must not block read-only sessions or pre-existing staged work.
set -euo pipefail

INPUT=$(cat || true)

STOP_HOOK_ACTIVE=$(echo "$INPUT" | python3 -c '
import sys, json
try:
    d=json.load(sys.stdin)
    print(d.get("stop_hook_active", False))
except Exception:
    print(False)
' 2>/dev/null || echo "False")

if [ "$STOP_HOOK_ACTIVE" = "True" ]; then
  exit 0
fi

STAGED=$(git diff --cached --name-only 2>/dev/null || true)
UNSTAGED=$(git diff --name-only 2>/dev/null || true)
UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null || true)

if [ -n "$STAGED$UNSTAGED$UNTRACKED" ]; then
  cat >&2 <<'REMINDER'
Session ended with existing working-tree changes.

Before committing:
- confirm changes map to the current Phase 0-4 science roadmap
- confirm staged files are intentional
- do not commit unrelated local config/backups unless explicitly intended
REMINDER
fi

exit 0
