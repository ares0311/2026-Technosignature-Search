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
    sqlite_log_backup,
    sqlite_log_export,
    sqlite_log_integrity_summary,
    sqlite_log_migration_summary,
    sqlite_log_pragmas,
    sqlite_log_retention_summary,
    sqlite_log_summary,
    sqlite_log_vacuum,
    sqlite_needs_follow_up,
    sqlite_recent_runs,
    validate_sqlite_log_commit_paths,
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


def test_sqlite_log_integrity_detects_missing_metadata(tmp_path: Path) -> None:
    db_path = tmp_path / "logs" / "techno_search.sqlite3"
    init_sqlite_log_db(db_path)

    with closing(sqlite3.connect(db_path)) as connection, connection:
        connection.execute("DELETE FROM metadata WHERE key = 'schema_version'")

    result = validate_sqlite_log_database(db_path)
    assert not result.ok
    assert "metadata is missing required keys" in result.errors[0]
    assert sqlite_log_integrity_summary(db_path)["metadata_ok"] is False


def test_sqlite_log_integrity_detects_run_without_outcome(tmp_path: Path) -> None:
    db_path = tmp_path / "logs" / "techno_search.sqlite3"
    init_sqlite_log_db(db_path)
    _insert_minimal_run(db_path, "missing-outcome-run")

    result = validate_sqlite_log_database(db_path)

    assert not result.ok
    assert "without exactly one outcome" in " ".join(result.errors)
    summary = sqlite_log_integrity_summary(db_path)
    assert summary["missing_outcome_run_ids"] == ["missing-outcome-run"]


def test_sqlite_log_integrity_detects_conflicting_outcomes(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    db_path = tmp_path / "logs" / "techno_search.sqlite3"
    run_local_background_search_once(
        artifact_dir / "background_search_ledger.json",
        reviewed_log_path=artifact_dir / "background_reviewed_log.json",
        needs_follow_up_log_path=artifact_dir / "background_needs_follow_up_log.json",
        sqlite_log_path=db_path,
        run_id="conflicting-outcome-run",
        code_commit="test-commit",
        opt_in=True,
    )
    with closing(sqlite3.connect(db_path)) as connection, connection:
        connection.execute(
            """
            INSERT INTO reviewed_outcomes (
                review_id, run_id, target_id, track, outcome_status,
                reviewed_at_utc, reason_codes_json, negative_evidence_json,
                blocking_issues_json, recommended_next_action,
                network_access_allowed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "review-conflict",
                "conflicting-outcome-run",
                "target-radio-clean-drift",
                "radio",
                "reviewed_no_follow_up",
                "2026-05-09T00:00:00+00:00",
                "[]",
                '["conflicting test outcome inserted"]',
                "[]",
                "retain_in_reviewed_log",
                0,
            ),
        )

    result = validate_sqlite_log_database(db_path)

    assert not result.ok
    assert "multiple outcomes" in " ".join(result.errors)
    assert sqlite_log_summary(db_path)["multiple_outcome_run_ids"] == [
        "conflicting-outcome-run"
    ]


def test_sqlite_export_preserves_review_safe_context(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    db_path = tmp_path / "logs" / "techno_search.sqlite3"
    run_local_background_search_once(
        artifact_dir / "background_search_ledger.json",
        reviewed_log_path=artifact_dir / "background_reviewed_log.json",
        needs_follow_up_log_path=artifact_dir / "background_needs_follow_up_log.json",
        sqlite_log_path=db_path,
        run_id="export-sqlite-run",
        code_commit="test-commit",
        opt_in=True,
    )

    recent = sqlite_recent_runs(db_path)
    follow_up = sqlite_needs_follow_up(db_path)
    export = sqlite_log_export(db_path)

    assert recent["runs"][0]["blocking_issues"]
    assert recent["runs"][0]["target_selection_rationale"]
    assert recent["runs"][0]["uncertainty_notes"]
    assert follow_up["needs_follow_up"][0]["negative_evidence"]
    assert follow_up["needs_follow_up"][0]["blocking_issues"]
    assert follow_up["needs_follow_up"][0]["uncertainty_notes"]
    assert export["integrity"]["ok"] is True
    assert export["migration"]["migration_required"] is False
    assert "not a detection" in export["uncertainty_and_limitations"][1]


def test_sqlite_migration_summary_flags_unsupported_schema(tmp_path: Path) -> None:
    db_path = tmp_path / "logs" / "techno_search.sqlite3"
    init_sqlite_log_db(db_path)
    with closing(sqlite3.connect(db_path)) as connection, connection:
        connection.execute(
            "UPDATE metadata SET value = ? WHERE key = 'schema_version'",
            ("future_schema_v2",),
        )

    summary = sqlite_log_migration_summary(db_path)

    assert summary["current_schema_version"] == "future_schema_v2"
    assert summary["expected_schema_version"] == TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION
    assert summary["migration_required"] is True


def test_sqlite_commit_path_guard_rejects_generated_top_level_logs(
    tmp_path: Path,
) -> None:
    result = validate_sqlite_log_commit_paths(
        [
            tmp_path / "logs" / "README.md",
            tmp_path / "logs" / "techno_search.sqlite3",
            tmp_path / "logs" / "techno_search.sqlite3-wal",
            tmp_path / "logs" / "backups" / "techno_search.sqlite3",
            tmp_path / "artifacts" / "temporary.sqlite3",
        ],
        project_root=tmp_path,
    )

    assert not result["ok"]
    assert result["forbidden_paths"] == [
        "logs/backups/techno_search.sqlite3",
        "logs/techno_search.sqlite3",
        "logs/techno_search.sqlite3-wal",
    ]


def test_sqlite_backup_retention_vacuum_and_pragmas(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    db_path = tmp_path / "logs" / "techno_search.sqlite3"
    run_local_background_search_once(
        artifact_dir / "background_search_ledger.json",
        reviewed_log_path=artifact_dir / "background_reviewed_log.json",
        needs_follow_up_log_path=artifact_dir / "background_needs_follow_up_log.json",
        sqlite_log_path=db_path,
        run_id="maintenance-sqlite-run",
        code_commit="test-commit",
        opt_in=True,
    )

    backup = sqlite_log_backup(db_path)
    retention = sqlite_log_retention_summary(db_path)
    pragmas = sqlite_log_pragmas(db_path)
    vacuum = sqlite_log_vacuum(db_path)

    assert backup["ok"] is True
    assert Path(str(backup["backup_path"])).exists()
    assert retention["ok"] is True
    assert retention["backup_count"] >= 1
    assert retention["backup_total_size_bytes"] >= backup["backup_size_bytes"]
    assert pragmas["ok"] is True
    assert pragmas["foreign_keys"] == 1
    assert pragmas["integrity_check"] == "ok"
    assert vacuum["ok"] is True
    assert vacuum["after_size_bytes"] <= vacuum["before_size_bytes"]


def _insert_minimal_run(db_path: Path, run_id: str) -> None:
    with closing(sqlite3.connect(db_path)) as connection, connection:
        connection.execute(
            """
            INSERT INTO background_runs (
                run_id, target_id, track, status, query_parameters_json,
                started_at_utc, completed_at_utc, config_version, code_commit,
                cache_key, candidate_count, recommended_pathways_json,
                blocking_issues_json, execution_mode, selected_priority_score,
                target_selection_rationale_json, candidate_packet_ids_json,
                negative_result_logged, requires_human_review,
                reviewed_workflow_status, network_access_allowed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                "target-radio-clean-drift",
                "radio",
                "needs_follow_up_logged",
                "{}",
                "2026-05-09T00:00:00+00:00",
                "2026-05-09T00:00:00+00:00",
                "background_priority_v0",
                "test-commit",
                "cache-key",
                0,
                "[]",
                "[]",
                "local_non_network_fixture_runner",
                0.1,
                "[]",
                "[]",
                0,
                1,
                "needs_follow_up_required",
                0,
            ),
        )
