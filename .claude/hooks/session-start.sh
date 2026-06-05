#!/bin/bash
set -euo pipefail

# Install/verify dependencies
if [ "${CLAUDE_CODE_REMOTE:-}" = "true" ]; then
  cd "$CLAUDE_PROJECT_DIR"
  if [ ! -d ".venv" ]; then
    python3 -m venv .venv
  fi
  .venv/bin/pip install -e ".[dev]" --quiet
fi

# Emit mandatory reading reminder to stderr so it appears in the session
cat >&2 << 'REMINDER'
=============================================================
MANDATORY SESSION-START PROTOCOL
Before planning or executing anything, you must Read:
  1. AGENTS.md
  2. docs/PRODUCTION_READINESS.md
Do not rely on memory or prior context. These reads are
required before any plan or action is taken.
=============================================================
REMINDER
