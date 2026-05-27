from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from techno_search.top_level_sqlite_log_consistency import (
    load_top_level_sqlite_log_expectations,
    top_level_sqlite_log_consistency_summary,
)

FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "top_level_sqlite_log_consistency.json"
)


def _write_expected(path: Path, *, min_run_count: int = 1) -> Path:
    expected_path = path / "expected.json"
    expected_path.write_text(
        json.dumps(
            {
                "schema_version": "top_level_sqlite_log_consistency_v1",
                "expected_sqlite_log": {
                    "min_run_count": min_run_count,
                    "max_network_access_allowed_count": 0,
                    "max_external_submission_approved_count": 0,
                    "require_database_exists": True,
                    "require_database_readable": True,
                    "require_metadata_ok": True,
                    "require_validation_ok": True,
                    "require_integrity_ok": True,
                    "require_pragmas_ok": True,
                    "require_weekly_digest_ok": True,
                    "require_retention_ok": True,
                    "require_commit_guard_ok": True,
                    "require_no_migration_required": True,
                    "require_outcome_count_matches_run_count": True,
                },
            }
        ),
        encoding="utf-8",
    )
    return expected_path


def _snapshots() -> dict[str, dict[str, object]]:
    return {
        "sqlite_summary": {
            "db_path": "/tmp/techno_search.sqlite3",
            "database_exists": True,
            "database_readable": True,
            "metadata_ok": True,
            "run_count": 2,
            "outcome_count": 2,
            "network_access_allowed_count": 0,
            "external_submission_approved_count": 0,
        },
        "integrity_summary": {"ok": True},
        "migration_summary": {"migration_required": False},
        "migration_plan": {"migration_required": False},
        "weekly_digest": {"ok": True},
        "retention_summary": {"ok": True},
        "pragmas_summary": {"ok": True},
        "validation_summary": {"ok": True},
        "commit_guard": {"ok": True, "forbidden_path_count": 0},
    }


def _summary(expected_path: Path, snapshots: dict[str, dict[str, object]]) -> dict[str, object]:
    return top_level_sqlite_log_consistency_summary(
        expected_path,
        sqlite_summary=snapshots["sqlite_summary"],
        integrity_summary=snapshots["integrity_summary"],
        migration_summary=snapshots["migration_summary"],
        migration_plan=snapshots["migration_plan"],
        weekly_digest=snapshots["weekly_digest"],
        retention_summary=snapshots["retention_summary"],
        pragmas_summary=snapshots["pragmas_summary"],
        validation_summary=snapshots["validation_summary"],
        commit_guard=snapshots["commit_guard"],
    )


def test_load_top_level_sqlite_log_expectations_fixture() -> None:
    expected = load_top_level_sqlite_log_expectations(FIXTURE_PATH)

    assert expected["min_run_count"] == 0
    assert expected["max_network_access_allowed_count"] == 0
    assert expected["max_external_submission_approved_count"] == 0


def test_top_level_sqlite_log_consistency_custom_project_passes(
    tmp_path: Path,
) -> None:
    expected_path = _write_expected(tmp_path)

    summary = _summary(expected_path, _snapshots())

    assert summary["ok"] is True
    assert summary["issue_count"] == 0
    assert summary["run_count"] == 2
    assert summary["outcome_count"] == 2


def test_top_level_sqlite_log_consistency_detects_missing_database(
    tmp_path: Path,
) -> None:
    expected_path = _write_expected(tmp_path)
    snapshots = deepcopy(_snapshots())
    snapshots["sqlite_summary"]["database_exists"] = False

    summary = _summary(expected_path, snapshots)

    assert summary["ok"] is False
    assert any("does not exist" in issue for issue in summary["issues"])


def test_top_level_sqlite_log_consistency_detects_outcome_mismatch(
    tmp_path: Path,
) -> None:
    expected_path = _write_expected(tmp_path)
    snapshots = deepcopy(_snapshots())
    snapshots["sqlite_summary"]["outcome_count"] = 1

    summary = _summary(expected_path, snapshots)

    assert summary["ok"] is False
    assert any("outcome count 1 != run count 2" in issue for issue in summary["issues"])


def test_top_level_sqlite_log_consistency_detects_authorization_drift(
    tmp_path: Path,
) -> None:
    expected_path = _write_expected(tmp_path)
    snapshots = deepcopy(_snapshots())
    snapshots["sqlite_summary"]["network_access_allowed_count"] = 1
    snapshots["sqlite_summary"]["external_submission_approved_count"] = 1

    summary = _summary(expected_path, snapshots)

    assert summary["ok"] is False
    assert any("network access allowed count" in issue for issue in summary["issues"])
    assert any(
        "external submission approved count" in issue
        for issue in summary["issues"]
    )


def test_top_level_sqlite_log_consistency_detects_migration_drift(
    tmp_path: Path,
) -> None:
    expected_path = _write_expected(tmp_path)
    snapshots = deepcopy(_snapshots())
    snapshots["migration_plan"]["migration_required"] = True

    summary = _summary(expected_path, snapshots)

    assert summary["ok"] is False
    assert any("migration is required" in issue for issue in summary["issues"])


def test_top_level_sqlite_log_consistency_detects_commit_guard_drift(
    tmp_path: Path,
) -> None:
    expected_path = _write_expected(tmp_path)
    snapshots = deepcopy(_snapshots())
    snapshots["commit_guard"]["ok"] = False
    snapshots["commit_guard"]["forbidden_path_count"] = 1

    summary = _summary(expected_path, snapshots)

    assert summary["ok"] is False
    assert summary["forbidden_path_count"] == 1


def test_top_level_sqlite_log_consistency_default_project_passes() -> None:
    summary = top_level_sqlite_log_consistency_summary()

    assert summary["schema_version"] == "top_level_sqlite_log_consistency_v1"
    assert summary["ok"] is True
    assert summary["database_exists"] is True
    assert summary["validation_ok"] is True
    assert summary["network_access_allowed_count"] == 0
    assert summary["external_submission_approved_count"] == 0
