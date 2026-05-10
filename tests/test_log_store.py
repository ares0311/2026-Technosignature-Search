from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from techno_search.background_search import run_local_background_search_once
from techno_search.log_store import (
    TOP_LEVEL_SQLITE_LOG_DISCLAIMER,
    TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION,
    init_sqlite_log_db,
    sqlite_log_summary,
)
from techno_search.validation import validate_sqlite_log_database


def test_init_sqlite_log_db_creates_top_level_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "logs" / "techno_search.sqlite3"

    summary = init_sqlite_log_db(
        db_path,
        code_commit="test-commit",
        config_version="background_priority_v0",
    )

    assert summary["database_exists"] is True
    assert summary["schema_version"] == TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION
    assert summary["disclaimer"] == TOP_LEVEL_SQLITE_LOG_DISCLAIMER
    assert summary["run_count"] == 0
    with closing(sqlite3.connect(db_path)) as connection:
        table_names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert {
        "metadata",
        "background_runs",
        "reviewed_outcomes",
        "needs_follow_up_outcomes",
        "draft_reports",
        "user_decisions",
        "validation_events",
    } <= table_names


def test_local_background_run_appends_to_sqlite_log(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    db_path = tmp_path / "logs" / "techno_search.sqlite3"

    result = run_local_background_search_once(
        artifact_dir / "background_search_ledger.json",
        reviewed_log_path=artifact_dir / "background_reviewed_log.json",
        needs_follow_up_log_path=artifact_dir / "background_needs_follow_up_log.json",
        sqlite_log_path=db_path,
        run_id="sqlite-background-run-001",
        code_commit="test-commit",
        opt_in=True,
    )

    assert result["ok"] is True
    assert result["sqlite_log_path"] == str(db_path)
    summary = sqlite_log_summary(db_path)
    assert summary["run_count"] == 1
    assert summary["outcome_count"] == 1
    assert summary["missing_outcome_run_ids"] == []
    assert summary["multiple_outcome_run_ids"] == []
    assert summary["network_access_allowed_count"] == 0
    assert summary["external_submission_approved_count"] == 0
    assert validate_sqlite_log_database(db_path).ok


def test_sqlite_log_rejects_duplicate_run_ids(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    db_path = tmp_path / "logs" / "techno_search.sqlite3"

    run_local_background_search_once(
        artifact_dir / "background_search_ledger.json",
        reviewed_log_path=artifact_dir / "background_reviewed_log.json",
        needs_follow_up_log_path=artifact_dir / "background_needs_follow_up_log.json",
        sqlite_log_path=db_path,
        run_id="duplicate-sqlite-run",
        code_commit="test-commit",
        opt_in=True,
    )

    with pytest.raises(ValueError, match="already contains an outcome"):
        run_local_background_search_once(
            artifact_dir / "background_search_ledger.json",
            reviewed_log_path=artifact_dir / "background_reviewed_log.json",
            needs_follow_up_log_path=artifact_dir / "background_needs_follow_up_log.json",
            sqlite_log_path=db_path,
            run_id="duplicate-sqlite-run",
            code_commit="test-commit",
            opt_in=True,
        )
