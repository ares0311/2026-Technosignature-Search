from __future__ import annotations

import tomllib
from pathlib import Path

import techno_search


def _version_tuple(version: str) -> tuple[int, int, int]:
    parts = version.split(".")
    assert len(parts) == 3
    return tuple(int(part) for part in parts)


def test_package_version_matches_project_metadata() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert techno_search.__version__ == pyproject["project"]["version"]


def test_package_version_is_monotonic_after_pilot_release() -> None:
    assert _version_tuple(techno_search.__version__) >= (1, 1, 0)
