#!/usr/bin/env python3
"""Fail when release-relevant changes do not advance the app version."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tomllib
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION_PATTERN = re.compile(r'^__version__\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)
READINESS_PATTERN = re.compile(r"^\*\*Current app version:\*\*\s*(\S+)", re.MULTILINE)
RELEASE_RELEVANT_PREFIXES = (
    "src/techno_search/",
    "scripts/",
    "configs/",
    "schemas/",
)
RELEASE_RELEVANT_FILES = frozenset(
    {
        "AGENTS.md",
        "CLAUDE.md",
        "docs/PRODUCTION_READINESS.md",
        "docs/PRODUCTION_SCAN_RUNBOOK.md",
        "docs/ROADMAP.md",
        "docs/SYSTEMATIC_SEARCH_PLAN.md",
    }
)


def version_tuple(version: str) -> tuple[int, int, int]:
    """Parse the project's strict MAJOR.MINOR.PATCH version form."""
    parts = version.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise ValueError(f"app version must be MAJOR.MINOR.PATCH, got {version!r}")
    return tuple(int(part) for part in parts)  # type: ignore[return-value]


def project_version(pyproject_text: str) -> str:
    """Read the project version from pyproject TOML text."""
    value = tomllib.loads(pyproject_text)["project"]["version"]
    return str(value)


def module_version(init_text: str) -> str:
    """Read the package version without importing the working tree."""
    match = VERSION_PATTERN.search(init_text)
    if match is None:
        raise ValueError("src/techno_search/__init__.py has no __version__ assignment")
    return match.group(1)


def readiness_version(readiness_text: str) -> str:
    """Read the operator-visible app version from production readiness."""
    match = READINESS_PATTERN.search(readiness_text)
    if match is None:
        raise ValueError("docs/PRODUCTION_READINESS.md has no current app version")
    return match.group(1)


def release_relevant_paths(paths: Sequence[str]) -> list[str]:
    """Return paths whose change requires a version increment."""
    return sorted(
        {
            path
            for path in paths
            if path in RELEASE_RELEVANT_FILES
            or path.startswith(RELEASE_RELEVANT_PREFIXES)
        }
    )


def current_surface_errors(repo_root: Path = REPO_ROOT) -> list[str]:
    """Return disagreements among the three version sources of truth."""
    pyproject = project_version((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    package = module_version(
        (repo_root / "src/techno_search/__init__.py").read_text(encoding="utf-8")
    )
    readiness = readiness_version(
        (repo_root / "docs/PRODUCTION_READINESS.md").read_text(encoding="utf-8")
    )
    errors: list[str] = []
    for name, value in (("package", package), ("production readiness", readiness)):
        if value != pyproject:
            errors.append(f"{name} version {value} does not match project version {pyproject}")
    try:
        version_tuple(pyproject)
    except ValueError as exc:
        errors.append(str(exc))
    return errors


def _git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout


def _resolve_base_ref(repo_root: Path, base_ref: str) -> str:
    """Resolve the base locally, fetching only its tip in shallow GitHub CI."""
    verify = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{base_ref}^{{commit}}"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if verify.returncode == 0:
        return base_ref
    github_base = os.environ.get("GITHUB_BASE_REF")
    if os.environ.get("GITHUB_ACTIONS") == "true" and github_base:
        _git(repo_root, "fetch", "--no-tags", "--depth=1", "origin", github_base)
        return "FETCH_HEAD"
    raise RuntimeError(f"base ref {base_ref!r} is unavailable")


def base_increment_errors(repo_root: Path, base_ref: str) -> list[str]:
    """Require a strict version increase when app/directive surfaces changed."""
    resolved_base = _resolve_base_ref(repo_root, base_ref)
    changed_paths = _git(
        repo_root, "diff", "--name-only", resolved_base, "HEAD"
    ).splitlines()
    relevant = release_relevant_paths(changed_paths)
    if not relevant:
        return []
    current = project_version((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    base = project_version(_git(repo_root, "show", f"{resolved_base}:pyproject.toml"))
    if version_tuple(current) > version_tuple(base):
        return []
    sample = ", ".join(relevant[:8])
    return [
        f"release-relevant changes require an app version greater than {base}; "
        f"current is {current}. Changed paths: {sample}"
    ]


def _default_base_ref() -> str:
    github_base = os.environ.get("GITHUB_BASE_REF")
    return f"origin/{github_base}" if github_base else "origin/main"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-ref",
        default=_default_base_ref(),
        help="Git base used to detect release-relevant changes (default: origin/main).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        errors = [
            *current_surface_errors(REPO_ROOT),
            *base_increment_errors(REPO_ROOT, args.base_ref),
        ]
    except (KeyError, OSError, RuntimeError, ValueError, tomllib.TOMLDecodeError) as exc:
        errors = [str(exc)]
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    current = project_version((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    print(f"App version gate passed: {current} > {args.base_ref} when required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
