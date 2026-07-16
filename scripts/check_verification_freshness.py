#!/usr/bin/env python3
"""Fail when a verification claim would be stale.

A prior passing test/lint/validate-all run is not evidence about the
*current* repository state once relevant files change. This script is the
lightweight, git-native check for that: no provenance database, no content
hashing beyond what Git already tracks.

Two independent signals, either of which fails the gate:

1. Uncommitted changes under the watched paths. If ``git status --porcelain``
   shows changes to ``src/``, ``tests/``, ``scripts/``, ``AGENTS.md``, or
   ``CLAUDE.md``, any previously-recorded verification pass predates the
   current working tree and cannot be treated as current.
2. A stale verification marker. ``record_verification_pass()`` writes the
   tested commit SHA to ``artifacts/verification_last_pass.json`` (an
   already-ignored local path, see ``.gitignore``) after a successful full
   validation run. If that marker's commit differs from HEAD *and* a
   watched path changed in between, the recorded pass no longer applies.

Absence of a marker is reported as a note, not a failure — a repository
that has simply never run full validation yet is not "stale," it is
"unverified," which is a different, non-fatal state this script does not
gate on by itself.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WATCHED_PATHS = ("src", "tests", "scripts", "AGENTS.md", "CLAUDE.md")
MARKER_PATH = "artifacts/verification_last_pass.json"


def _git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _uncommitted_changes(repo_root: Path, watched_paths: Sequence[str]) -> list[str]:
    existing = [p for p in watched_paths if (repo_root / p).exists()]
    if not existing:
        return []
    output = _git(repo_root, "status", "--porcelain", "--", *existing)
    return [line for line in output.splitlines() if line.strip()]


def _read_marker(repo_root: Path) -> dict[str, object] | None:
    marker_path = repo_root / MARKER_PATH
    if not marker_path.is_file():
        return None
    try:
        data = json.loads(marker_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or "commit_sha" not in data:
        return None
    return data


def verification_freshness_errors(
    repo_root: Path,
    watched_paths: Sequence[str] = DEFAULT_WATCHED_PATHS,
) -> tuple[list[str], list[str]]:
    """Return (errors, notes). Non-empty errors means verification is stale."""
    errors: list[str] = []
    notes: list[str] = []

    try:
        dirty = _uncommitted_changes(repo_root, watched_paths)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        return (
            [
                f"Cannot determine git status at {repo_root}: not a usable git "
                f"repository, or git is unavailable ({exc}). Verification freshness "
                "cannot be established without a working git repository."
            ],
            [],
        )
    if dirty:
        sample = ", ".join(line.strip() for line in dirty[:8])
        errors.append(
            "VERIFICATION STALE: uncommitted changes exist under watched paths "
            f"({', '.join(watched_paths)}); any prior verification result predates "
            f"the current working tree. Changed: {sample}"
        )

    marker = _read_marker(repo_root)
    if marker is None:
        notes.append(
            f"No verification marker at {MARKER_PATH}: this repository has not yet "
            "recorded a full successful verification pass. This is 'unverified', "
            "not 'stale' — it is not treated as an error by itself."
        )
    else:
        marker_sha = str(marker.get("commit_sha", ""))
        try:
            head_sha = _git(repo_root, "rev-parse", "HEAD")
        except (subprocess.CalledProcessError, FileNotFoundError):
            head_sha = ""
        if marker_sha and head_sha and marker_sha != head_sha:
            try:
                changed = _git(
                    repo_root, "diff", "--name-only", marker_sha, head_sha
                ).splitlines()
            except subprocess.CalledProcessError:
                changed = []
            relevant = [
                path
                for path in changed
                if any(path == w or path.startswith(w.rstrip("/") + "/") for w in watched_paths)
            ]
            if relevant:
                sample = ", ".join(relevant[:8])
                errors.append(
                    f"VERIFICATION STALE: last recorded pass was at commit {marker_sha[:12]}, "
                    f"but HEAD is now {head_sha[:12]} with relevant changes since then: {sample}"
                )
            else:
                notes.append(
                    f"Verification marker is at an older commit ({marker_sha[:12]}) than "
                    f"HEAD ({head_sha[:12]}), but no watched paths changed since — still current."
                )

    return errors, notes


def record_verification_pass(repo_root: Path) -> Path:
    """Write the current commit SHA as the last successful verification marker."""
    marker_path = repo_root / MARKER_PATH
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        commit_sha = _git(repo_root, "rev-parse", "HEAD")
    except (subprocess.CalledProcessError, FileNotFoundError):
        commit_sha = "unknown"
    marker_path.write_text(
        json.dumps(
            {
                "commit_sha": commit_sha,
                "recorded_at_utc": datetime.now(UTC).isoformat(),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return marker_path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--record-pass",
        action="store_true",
        help="Write the current commit SHA as the last-verified marker and exit.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.record_pass:
        marker_path = record_verification_pass(args.repo_root)
        print(f"Recorded verification pass at {marker_path}.")
        return 0
    errors, notes = verification_freshness_errors(args.repo_root)
    for note in notes:
        print(f"NOTE: {note}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Verification freshness gate passed: no uncommitted changes, no stale marker.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
