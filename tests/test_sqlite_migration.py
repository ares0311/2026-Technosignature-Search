"""Tests for the guarded SQLite log migration from v1 to v2."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from io import StringIO
from pathlib import Path

from techno_search.cli import main
from techno_search.log_store import (
    SUPPORTED_SQLITE_LOG_MIGRATIONS,
    TOP_LEVEL_SQLITE_LOG_PREVIOUS_SCHEMA_VERSION,
    TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION,
    apply_sqlite_log_migration,
    init_sqlite_log_db,
    sqlite_log_integrity_summary,
    sqlite_log_migration_plan,
)


def _create_v1_database(db_path: Path) -> None:
    """Create a synthetic v1 database (without target_notes column)."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db_path)) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS background_runs (
                run_id TEXT PRIMARY KEY,
                target_id TEXT NOT NULL,
                track TEXT NOT NULL,
                status TEXT NOT NULL,
                query_parameters_json TEXT NOT NULL,
                started_at_utc TEXT NOT NULL,
                completed_at_utc TEXT NOT NULL,
                config_version TEXT NOT NULL,
                code_commit TEXT NOT NULL,
                cache_key TEXT NOT NULL,
                candidate_count INTEGER NOT NULL,
                recommended_pathways_json TEXT NOT NULL,
                blocking_issues_json TEXT NOT NULL,
                execution_mode TEXT NOT NULL,
                selected_priority_score REAL,
                target_selection_rationale_json TEXT NOT NULL,
                candidate_packet_ids_json TEXT NOT NULL,
                negative_result_logged INTEGER NOT NULL CHECK (negative_result_logged IN (0, 1)),
                requires_human_review INTEGER NOT NULL CHECK (requires_human_review IN (0, 1)),
                reviewed_workflow_status TEXT NOT NULL,
                network_access_allowed INTEGER NOT NULL DEFAULT 0
                    CHECK (network_access_allowed IN (0, 1))
            );
            """
        )
        with connection:
            connection.executemany(
                "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
                [
                    ("schema_version", "top_level_sqlite_logs_v1"),
                    ("disclaimer", "test"),
                    ("created_at_utc", "2026-05-15T00:00:00+00:00"),
                    ("code_commit", "test-commit"),
                    ("config_version", "scoring_v0"),
                ],
            )


def test_supported_migrations_includes_v1_to_v2():
    versions = [(m["from_version"], m["to_version"]) for m in SUPPORTED_SQLITE_LOG_MIGRATIONS]
    assert (
        TOP_LEVEL_SQLITE_LOG_PREVIOUS_SCHEMA_VERSION,
        TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION,
    ) in versions


def test_supported_migrations_includes_noop_at_current():
    noop = next(
        (m for m in SUPPORTED_SQLITE_LOG_MIGRATIONS if m["kind"] == "noop"),
        None,
    )
    assert noop is not None
    assert noop["to_version"] == TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION


def test_apply_migration_v1_to_v2_adds_target_notes_column(tmp_path):
    db_path = tmp_path / "test.sqlite3"
    _create_v1_database(db_path)

    result = apply_sqlite_log_migration(db_path)

    assert result["ok"] is True
    assert result["migration_applied"] is True
    assert result["schema_version"] == TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION

    with closing(sqlite3.connect(db_path)) as connection:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(background_runs)").fetchall()
        }
        assert "target_notes" in columns
        version_row = connection.execute(
            "SELECT value FROM metadata WHERE key = 'schema_version'"
        ).fetchone()
        assert version_row[0] == TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION


def test_apply_migration_is_idempotent(tmp_path):
    db_path = tmp_path / "test.sqlite3"
    _create_v1_database(db_path)

    result1 = apply_sqlite_log_migration(db_path)
    assert result1["migration_applied"] is True

    result2 = apply_sqlite_log_migration(db_path)
    assert result2["ok"] is True
    assert result2["already_at_target"] is True
    assert result2["migration_applied"] is False


def test_apply_migration_on_current_v2_database(tmp_path):
    db_path = tmp_path / "test.sqlite3"
    init_sqlite_log_db(db_path)

    result = apply_sqlite_log_migration(db_path)
    assert result["ok"] is True
    assert result["already_at_target"] is True


def test_migration_plan_shows_no_migration_required_on_v2(tmp_path):
    db_path = tmp_path / "test.sqlite3"
    init_sqlite_log_db(db_path)

    plan = sqlite_log_migration_plan(db_path)
    assert plan["migration_required"] is False
    assert plan["dry_run"] is True
    assert plan["destructive_steps_count"] == 0


def test_migration_plan_shows_migration_required_on_v1(tmp_path):
    db_path = tmp_path / "test.sqlite3"
    _create_v1_database(db_path)

    plan = sqlite_log_migration_plan(db_path)
    assert plan["migration_required"] is True
    assert plan["dry_run"] is True


def test_migration_guard_prevents_downgrade(tmp_path):
    """Migration from an unknown version returns an error, not a destructive change."""
    db_path = tmp_path / "test.sqlite3"
    init_sqlite_log_db(db_path)
    with closing(sqlite3.connect(db_path)) as connection, connection:
        connection.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES ('schema_version', 'future_v99')"
        )

    result = apply_sqlite_log_migration(db_path)
    assert result["ok"] is False
    assert "Cannot migrate" in result["error"]


def test_apply_migration_nonexistent_database_returns_error(tmp_path):
    db_path = tmp_path / "nonexistent.sqlite3"
    result = apply_sqlite_log_migration(db_path)
    assert result["ok"] is False
    assert "does not exist" in result["error"]


def test_full_v2_database_passes_integrity_check(tmp_path):
    """A v2 database initialised via init_sqlite_log_db passes integrity."""
    db_path = tmp_path / "test.sqlite3"
    init_sqlite_log_db(db_path)
    integrity = sqlite_log_integrity_summary(db_path)
    assert integrity["ok"] is True


def test_migrated_v1_database_has_correct_version_and_column(tmp_path):
    """After migration, schema version is v2 and target_notes column exists."""
    db_path = tmp_path / "test.sqlite3"
    _create_v1_database(db_path)
    apply_sqlite_log_migration(db_path)
    with closing(sqlite3.connect(db_path)) as connection:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(background_runs)").fetchall()
        }
        version_row = connection.execute(
            "SELECT value FROM metadata WHERE key = 'schema_version'"
        ).fetchone()
    assert "target_notes" in columns
    assert version_row[0] == TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION


def test_cli_sqlite_log_migrate_apply_on_v1_succeeds(tmp_path):
    db_path = tmp_path / "test.sqlite3"
    _create_v1_database(db_path)
    out = StringIO()
    ret = main(
        ["sqlite-log-migrate", "--db-path", str(db_path), "--apply"],
        stdout=out,
    )
    assert ret == 0
    data = json.loads(out.getvalue())
    assert data["ok"] is True
    assert data["migration_applied"] is True
