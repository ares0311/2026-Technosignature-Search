#!/usr/bin/env python3
"""Fail when Claude Code and Codex CLI would see divergent agent directives.

This project keeps one canonical directive file, ``AGENTS.md``. Codex CLI
reads it directly (its own documented repository-instructions convention).
Claude Code reads ``CLAUDE.md``, which must explicitly defer to ``AGENTS.md``
rather than duplicating or contradicting it. This script fails loudly if
either side of that arrangement drifts: if ``CLAUDE.md`` loses its deference
marker, or if ``AGENTS.md`` loses the required directive section headers.

This is intentionally a plain content check, not a semantic diff — the goal
is to catch *material drift* (a deleted or renamed section, a broken
deference statement) cheaply and deterministically, per this repository's
"do not build an elaborate directive-management framework" convention.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

CLAUDE_MD_REQUIRED_MARKERS = (
    "AGENTS.md is the single source of truth for all directives",
    "where anything below appears to conflict, `AGENTS.md` governs",
)

AGENTS_MD_REQUIRED_SECTIONS = (
    "## LLM MAINTENANCE DIRECTIVES",
    "### FAIL LOUDLY",
    "### NO FAKE COMPLETION",
    "### NO UNSUPPORTED COMPLETION CLAIMS",
    "### AGENT INSTRUCTION EXPOSURE",
)


def directive_parity_errors(repo_root: Path) -> list[str]:
    """Return a list of human-readable drift errors; empty means parity holds."""
    errors: list[str] = []

    claude_path = repo_root / "CLAUDE.md"
    agents_path = repo_root / "AGENTS.md"

    if not claude_path.is_file():
        errors.append(f"missing required file: {claude_path}")
    else:
        claude_text = claude_path.read_text(encoding="utf-8")
        for marker in CLAUDE_MD_REQUIRED_MARKERS:
            if marker not in claude_text:
                errors.append(
                    f"CLAUDE.md is missing its AGENTS.md deference marker: {marker!r}"
                )

    if not agents_path.is_file():
        errors.append(f"missing required file: {agents_path}")
    else:
        agents_text = agents_path.read_text(encoding="utf-8")
        for section in AGENTS_MD_REQUIRED_SECTIONS:
            if section not in agents_text:
                errors.append(
                    f"AGENTS.md is missing required directive section: {section!r}"
                )

    return errors


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root containing CLAUDE.md and AGENTS.md (default: this repo).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    errors = directive_parity_errors(args.repo_root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Directive parity gate passed: CLAUDE.md defers to AGENTS.md; "
          "required AGENTS.md sections present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
