"""Tests for the tracked data-collection status manifest."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from techno_search.data_collection_status import (
    DATA_COLLECTION_STATUS_SCHEMA_VERSION,
    commit_and_push_status,
    record_and_publish_data_collection_status,
    update_data_collection_status,
)


def test_update_creates_manifest_with_disclaimer(tmp_path: Path) -> None:
    status_path = tmp_path / "docs" / "data_collection_status.json"

    manifest = update_data_collection_status(
        tmp_path, "example_script", {"downloaded": 3}, status_path=status_path
    )

    assert manifest["schema_version"] == DATA_COLLECTION_STATUS_SCHEMA_VERSION
    assert "disclaimer" in manifest
    assert manifest["runs"]["example_script"]["downloaded"] == 3
    assert "last_run_utc" in manifest["runs"]["example_script"]
    assert json.loads(status_path.read_text()) == manifest


def test_update_preserves_other_scripts_entries(tmp_path: Path) -> None:
    status_path = tmp_path / "docs" / "data_collection_status.json"

    update_data_collection_status(tmp_path, "script_a", {"downloaded": 1}, status_path=status_path)
    manifest = update_data_collection_status(
        tmp_path, "script_b", {"downloaded": 2}, status_path=status_path
    )

    assert manifest["runs"]["script_a"]["downloaded"] == 1
    assert manifest["runs"]["script_b"]["downloaded"] == 2


def test_update_overwrites_same_script_entry(tmp_path: Path) -> None:
    status_path = tmp_path / "docs" / "data_collection_status.json"

    update_data_collection_status(tmp_path, "script_a", {"downloaded": 1}, status_path=status_path)
    manifest = update_data_collection_status(
        tmp_path, "script_a", {"downloaded": 5}, status_path=status_path
    )

    assert manifest["runs"]["script_a"]["downloaded"] == 5


def test_commit_and_push_reports_error_without_raising_when_git_unavailable(
    tmp_path: Path, monkeypatch
) -> None:
    status_path = tmp_path / "docs" / "data_collection_status.json"
    status_path.parent.mkdir(parents=True)
    status_path.write_text("{}")

    def _fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if args[:2] == ["git", "branch"]:
            return subprocess.CompletedProcess(args, returncode=0, stdout="main\n", stderr="")
        return subprocess.CompletedProcess(args, returncode=1, stdout="", stderr="not a git repo")

    monkeypatch.setattr(subprocess, "run", _fake_run)

    result = commit_and_push_status(tmp_path, status_path=status_path, message="test")

    assert result["committed"] is False
    assert result["pushed"] is False
    assert result["error"] is not None


def test_commit_and_push_skips_auto_commit_when_not_on_main(
    tmp_path: Path, monkeypatch
) -> None:
    """Regression test: an earlier version of this function unconditionally ran
    `git commit`/`git push`, which meant *any* invocation of a script that
    calls this (including this project's own real integration tests that run
    the real bash download script end-to-end) would auto-commit and push to
    whatever branch happened to be checked out -- caught in this session when
    running the test suite auto-pushed a fake status entry to the agent's own
    branch. This must only ever fire on the user's real `main` branch."""

    status_path = tmp_path / "docs" / "data_collection_status.json"
    status_path.parent.mkdir(parents=True)
    status_path.write_text("{}")

    calls: list[list[str]] = []

    def _fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        if args[:2] == ["git", "branch"]:
            return subprocess.CompletedProcess(
                args, returncode=0, stdout="claude/general-session-Bb2dZ\n", stderr=""
            )
        raise AssertionError(f"git add/commit/push must not run off main: {args}")

    monkeypatch.setattr(subprocess, "run", _fake_run)

    result = commit_and_push_status(tmp_path, status_path=status_path, message="test")

    assert result["committed"] is False
    assert result["pushed"] is False
    assert "not 'main'" in result["error"]
    assert calls == [["git", "branch", "--show-current"]]


def test_record_and_publish_without_auto_commit_skips_git(tmp_path: Path) -> None:
    status_path = tmp_path / "docs" / "data_collection_status.json"

    result = record_and_publish_data_collection_status(
        tmp_path,
        "example_script",
        {"downloaded": 1},
        status_path=status_path,
        auto_commit=False,
    )

    assert result["git"] is None
    assert result["manifest"]["runs"]["example_script"]["downloaded"] == 1
