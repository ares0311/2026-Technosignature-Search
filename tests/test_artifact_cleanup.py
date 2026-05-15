import json
from io import StringIO
from pathlib import Path

import pytest

from techno_search.artifact_cleanup import (
    ARTIFACT_CLEANUP_DISCLAIMER,
    ARTIFACT_CLEANUP_FORBIDDEN_ROOTS,
    ARTIFACT_CLEANUP_SCHEMA_VERSION,
    apply_artifact_cleanup,
    plan_artifact_cleanup,
)
from techno_search.cli import main


def _project(tmp_path: Path) -> Path:
    for forbidden in ARTIFACT_CLEANUP_FORBIDDEN_ROOTS:
        (tmp_path / forbidden).mkdir()
    return tmp_path


def test_plan_returns_empty_when_artifacts_dir_missing(tmp_path: Path) -> None:
    root = _project(tmp_path)

    plan = plan_artifact_cleanup(root / "artifacts", project_root=root)

    assert plan["ok"] is True
    assert plan["directory_exists"] is False
    assert plan["candidate_count"] == 0
    assert plan["disclaimer"] == ARTIFACT_CLEANUP_DISCLAIMER
    assert plan["schema_version"] == ARTIFACT_CLEANUP_SCHEMA_VERSION


def test_plan_lists_files_under_artifacts(tmp_path: Path) -> None:
    root = _project(tmp_path)
    artifacts = root / "artifacts" / "background_search_ledger"
    artifacts.mkdir(parents=True)
    (artifacts / "ledger.json").write_text("{}", encoding="utf-8")
    (artifacts / "outcome.json").write_text("{}", encoding="utf-8")

    plan = plan_artifact_cleanup(root / "artifacts", project_root=root)

    assert plan["candidate_count"] == 2
    assert plan["total_size_bytes"] == 4
    paths = sorted(entry["relative_path"] for entry in plan["candidates"])
    assert paths == [
        "artifacts/background_search_ledger/ledger.json",
        "artifacts/background_search_ledger/outcome.json",
    ]


@pytest.mark.parametrize("forbidden", ARTIFACT_CLEANUP_FORBIDDEN_ROOTS)
def test_plan_refuses_committed_roots(tmp_path: Path, forbidden: str) -> None:
    root = _project(tmp_path)
    target = root / forbidden
    target.mkdir(exist_ok=True)
    (target / "keep.txt").write_text("x", encoding="utf-8")

    plan = plan_artifact_cleanup(target, project_root=root)

    assert plan["ok"] is False
    assert plan["refused"] is True
    assert forbidden in plan["refusal_reason"]


def test_plan_refuses_paths_outside_project_root(tmp_path: Path) -> None:
    root = _project(tmp_path)
    outside = tmp_path.parent / "outside-target"
    outside.mkdir(exist_ok=True)

    plan = plan_artifact_cleanup(outside, project_root=root)

    assert plan["ok"] is False
    assert plan["refused"] is True


def test_apply_requires_acknowledgement(tmp_path: Path) -> None:
    root = _project(tmp_path)
    artifacts = root / "artifacts"
    artifacts.mkdir()
    (artifacts / "scratch.json").write_text("{}", encoding="utf-8")

    result = apply_artifact_cleanup(artifacts, project_root=root)

    assert result["applied"] is False
    assert result["apply_blocked"] is True
    assert (artifacts / "scratch.json").exists()


def test_apply_with_acknowledgement_deletes_only_under_artifacts(tmp_path: Path) -> None:
    root = _project(tmp_path)
    artifacts = root / "artifacts"
    artifacts.mkdir()
    (artifacts / "scratch.json").write_text("{}", encoding="utf-8")
    (root / "examples" / "keep.json").write_text("{}", encoding="utf-8")

    result = apply_artifact_cleanup(
        artifacts,
        project_root=root,
        acknowledge_local_apply=True,
    )

    assert result["applied"] is True
    assert result["deleted_count"] == 1
    assert not (artifacts / "scratch.json").exists()
    assert (root / "examples" / "keep.json").exists()


def test_cli_artifacts_cleanup_dry_run_default(tmp_path: Path) -> None:
    root = _project(tmp_path)
    artifacts = root / "artifacts"
    artifacts.mkdir()
    (artifacts / "scratch.json").write_text("{}", encoding="utf-8")
    stdout = StringIO()

    monkeypatched_root = root

    import techno_search.cli as cli

    original = cli.default_project_root
    cli.default_project_root = lambda: monkeypatched_root  # type: ignore[assignment]
    try:
        exit_code = main(
            ["artifacts-cleanup", "--artifacts-dir", str(artifacts)],
            stdout=stdout,
        )
    finally:
        cli.default_project_root = original  # type: ignore[assignment]
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["ok"] is True
    assert "applied" not in result
    assert (artifacts / "scratch.json").exists()


def test_cli_artifacts_cleanup_refuses_committed_root(tmp_path: Path) -> None:
    root = _project(tmp_path)
    stdout = StringIO()

    import techno_search.cli as cli

    original = cli.default_project_root
    cli.default_project_root = lambda: root  # type: ignore[assignment]
    try:
        exit_code = main(
            ["artifacts-cleanup", "--artifacts-dir", str(root / "examples")],
            stdout=stdout,
        )
    finally:
        cli.default_project_root = original  # type: ignore[assignment]
    result = json.loads(stdout.getvalue())

    assert exit_code == 1
    assert result["ok"] is False
    assert result["refused"] is True
