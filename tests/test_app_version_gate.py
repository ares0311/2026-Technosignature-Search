from __future__ import annotations

from pathlib import Path

import pytest
from scripts import check_app_version
from scripts.check_app_version import (
    module_version,
    project_version,
    readiness_version,
    release_relevant_paths,
    version_tuple,
)


def test_version_parsers_read_all_surfaces() -> None:
    assert project_version('[project]\nversion = "1.2.4"\n') == "1.2.4"
    assert module_version('__version__ = "1.2.4"\n') == "1.2.4"
    assert readiness_version("**Current app version:** 1.2.4\n") == "1.2.4"


def test_version_tuple_rejects_non_semver_values() -> None:
    with pytest.raises(ValueError, match="MAJOR.MINOR.PATCH"):
        version_tuple("1.2")


def test_release_relevant_paths_include_app_directives_and_science_code() -> None:
    assert release_relevant_paths(
        [
            "docs/notes.md",
            "AGENTS.md",
            "src/techno_search/cli.py",
            "scripts/download.py",
            "configs/scoring.json",
            "schemas/candidate.json",
        ]
    ) == [
        "AGENTS.md",
        "configs/scoring.json",
        "schemas/candidate.json",
        "scripts/download.py",
        "src/techno_search/cli.py",
    ]


def test_base_gate_rejects_relevant_change_without_increment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nversion = "1.2.3"\n', encoding="utf-8"
    )

    def fake_git(_repo_root: Path, *args: str) -> str:
        if args[:2] == ("diff", "--name-only"):
            return "src/techno_search/cli.py\n"
        if args[:1] == ("show",):
            return '[project]\nversion = "1.2.3"\n'
        raise AssertionError(args)

    monkeypatch.setattr(check_app_version, "_git", fake_git)

    errors = check_app_version.base_increment_errors(tmp_path, "origin/main")

    assert len(errors) == 1
    assert "require an app version greater than 1.2.3" in errors[0]


def test_base_gate_accepts_strict_increment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nversion = "1.2.4"\n', encoding="utf-8"
    )

    def fake_git(_repo_root: Path, *args: str) -> str:
        if args[:2] == ("diff", "--name-only"):
            return "AGENTS.md\n"
        if args[:1] == ("show",):
            return '[project]\nversion = "1.2.3"\n'
        raise AssertionError(args)

    monkeypatch.setattr(check_app_version, "_git", fake_git)

    assert check_app_version.base_increment_errors(tmp_path, "origin/main") == []
