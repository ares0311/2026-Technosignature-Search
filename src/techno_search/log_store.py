"""Top-level SQLite operational logs for background search workflows."""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION = "top_level_sqlite_logs_v1"
TOP_LEVEL_SQLITE_LOG_DISCLAIMER = (
    "Top-level SQLite logs are local workflow and provenance records only; "
    "they are not detections, discoveries, external validation, or external "
    "submission approval."
)
DEFAULT_SQLITE_LOG_PATH = Path("logs/techno_search.sqlite3")
DEFAULT_SQLITE_BACKUP_DIRNAME = "backups"
DEFAULT_SQLITE_SIZE_WARNING_BYTES = 100 * 1024 * 1024
REQUIRED_SQLITE_METADATA_KEYS = (
    "schema_version",
    "disclaimer",
    "created_at_utc",
    "code_commit",
    "config_version",
)
FORBIDDEN_SQLITE_LOG_SUFFIXES = (".sqlite", ".sqlite3", ".db")
FORBIDDEN_SQLITE_LOG_FILENAMES = ("-wal", "-shm")


def default_sqlite_log_path(project_root: Path | None = None) -> Path:
    """Return the default top-level SQLite log path."""

    root = project_root or Path.cwd()
    return root / DEFAULT_SQLITE_LOG_PATH


def init_sqlite_log_db(
    db_path: Path,
    *,
    code_commit: str = "not-recorded",
    config_version: str = "not-recorded",
) -> dict[str, object]:
    """Create or migrate the local SQLite operational log database."""

    resolved = Path(db_path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(resolved)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        _create_schema(connection)
        with connection:
            _upsert_metadata(
                connection,
                {
                    "schema_version": TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION,
                    "disclaimer": TOP_LEVEL_SQLITE_LOG_DISCLAIMER,
                    "created_at_utc": datetime.now(UTC).isoformat(),
                    "code_commit": code_commit,
                    "config_version": config_version,
                },
            )
    return sqlite_log_summary(resolved)


def append_background_run_to_sqlite(
    db_path: Path,
    *,
    ledger_entry: dict[str, Any],
    outcome_kind: str,
    outcome_entry: dict[str, Any],
) -> None:
    """Append one background run and exactly one outcome in a transaction."""

    if outcome_kind not in {"reviewed", "needs_follow_up"}:
        msg = f"Unsupported SQLite outcome kind: {outcome_kind!r}"
        raise ValueError(msg)

    resolved = Path(db_path)
    init_sqlite_log_db(
        resolved,
        code_commit=str(ledger_entry.get("code_commit", "not-recorded")),
        config_version=str(ledger_entry.get("config_version", "not-recorded")),
    )
    run_id = str(ledger_entry["run_id"])
    with closing(sqlite3.connect(resolved)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        if _run_has_any_outcome(connection, run_id):
            msg = f"SQLite log already contains an outcome for run_id {run_id!r}"
            raise ValueError(msg)
        with connection:
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
                    str(ledger_entry["target_id"]),
                    str(ledger_entry["track"]),
                    str(ledger_entry["status"]),
                    _json_text(ledger_entry.get("query_parameters", {})),
                    str(ledger_entry["started_at_utc"]),
                    str(ledger_entry["completed_at_utc"]),
                    str(ledger_entry["config_version"]),
                    str(ledger_entry["code_commit"]),
                    str(ledger_entry["cache_key"]),
                    int(ledger_entry.get("candidate_count", 0)),
                    _json_text(ledger_entry.get("recommended_pathways", [])),
                    _json_text(ledger_entry.get("blocking_issues", [])),
                    str(ledger_entry.get("execution_mode", "unspecified")),
                    _optional_float(ledger_entry.get("selected_priority_score")),
                    _json_text(ledger_entry.get("target_selection_rationale", [])),
                    _json_text(ledger_entry.get("candidate_packet_ids", [])),
                    int(bool(ledger_entry.get("negative_result_logged", False))),
                    int(bool(ledger_entry.get("requires_human_review", False))),
                    str(ledger_entry.get("reviewed_workflow_status", "unreviewed")),
                    0,
                ),
            )
            if outcome_kind == "reviewed":
                _insert_reviewed_outcome(connection, outcome_entry)
            else:
                _insert_needs_follow_up_outcome(connection, outcome_entry)


def sqlite_log_summary(db_path: Path) -> dict[str, object]:
    """Summarize top-level SQLite operational logs."""

    resolved = Path(db_path)
    if not resolved.exists():
        return {
            "ok": False,
            "db_path": str(resolved),
            "schema_version": TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION,
            "disclaimer": TOP_LEVEL_SQLITE_LOG_DISCLAIMER,
            "database_exists": False,
            "run_count": 0,
            "outcome_count": 0,
        }

    try:
        with closing(sqlite3.connect(resolved)) as connection:
            connection.row_factory = sqlite3.Row
            metadata = _metadata(connection)
            run_rows = connection.execute("SELECT * FROM background_runs").fetchall()
            reviewed_rows = connection.execute(
                "SELECT * FROM reviewed_outcomes"
            ).fetchall()
            follow_up_rows = connection.execute(
                "SELECT * FROM needs_follow_up_outcomes"
            ).fetchall()
    except sqlite3.DatabaseError as exc:
        return {
            "ok": False,
            "db_path": str(resolved),
            "schema_version": None,
            "disclaimer": TOP_LEVEL_SQLITE_LOG_DISCLAIMER,
            "database_exists": True,
            "database_readable": False,
            "database_error": str(exc),
            "run_count": 0,
            "outcome_count": 0,
        }

    run_ids = {str(row["run_id"]) for row in run_rows}
    reviewed_run_ids = {str(row["run_id"]) for row in reviewed_rows}
    follow_up_run_ids = {str(row["run_id"]) for row in follow_up_rows}
    outcome_run_ids = reviewed_run_ids | follow_up_run_ids
    multiple_outcome_run_ids = reviewed_run_ids & follow_up_run_ids
    missing_metadata_keys = sorted(set(REQUIRED_SQLITE_METADATA_KEYS) - set(metadata))
    schema_version = metadata.get("schema_version")

    return {
        "ok": (
            not missing_metadata_keys
            and schema_version == TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION
            and not multiple_outcome_run_ids
            and run_ids <= outcome_run_ids
        ),
        "db_path": str(resolved),
        "schema_version": schema_version,
        "disclaimer": metadata.get("disclaimer", TOP_LEVEL_SQLITE_LOG_DISCLAIMER),
        "database_exists": True,
        "database_readable": True,
        "metadata_ok": not missing_metadata_keys,
        "metadata_missing_keys": missing_metadata_keys,
        "migration_required": schema_version != TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION,
        "run_count": len(run_rows),
        "outcome_count": len(reviewed_rows) + len(follow_up_rows),
        "reviewed_outcome_count": len(reviewed_rows),
        "needs_follow_up_outcome_count": len(follow_up_rows),
        "missing_outcome_run_ids": sorted(run_ids - outcome_run_ids),
        "multiple_outcome_run_ids": sorted(multiple_outcome_run_ids),
        "network_access_allowed_count": sum(
            int(row["network_access_allowed"]) for row in run_rows
        ),
        "external_submission_approved_count": _count_external_approvals(resolved),
        "by_track": _counter_to_dict(Counter(str(row["track"]) for row in run_rows)),
        "by_status": _counter_to_dict(Counter(str(row["status"]) for row in run_rows)),
        "run_ids": sorted(run_ids),
        "target_ids": sorted({str(row["target_id"]) for row in run_rows}),
    }


def sqlite_log_validation_errors(db_path: Path) -> tuple[str, ...]:
    """Return conservative validation errors for a SQLite operational log."""

    summary = sqlite_log_summary(db_path)
    errors: list[str] = []
    if not summary.get("database_exists", False):
        errors.append(f"SQLite log database does not exist: {db_path}")
        return tuple(errors)
    if not summary.get("database_readable", True):
        errors.append(f"SQLite log database cannot be read: {summary.get('database_error')}")
        return tuple(errors)
    if summary.get("metadata_missing_keys"):
        errors.append(
            "SQLite log metadata is missing required keys: "
            f"{summary['metadata_missing_keys']}"
        )
    if summary.get("schema_version") != TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION:
        errors.append("SQLite log schema version is unsupported")
    if summary.get("missing_outcome_run_ids"):
        errors.append(
            "SQLite log has background runs without exactly one outcome: "
            f"{summary['missing_outcome_run_ids']}"
        )
    if summary.get("multiple_outcome_run_ids"):
        errors.append(
            "SQLite log has background runs with multiple outcomes: "
            f"{summary['multiple_outcome_run_ids']}"
        )
    if int(str(summary.get("network_access_allowed_count", 0))) != 0:
        errors.append("SQLite log contains network-enabled background runs")
    if int(str(summary.get("external_submission_approved_count", 0))) != 0:
        errors.append("SQLite log contains external submission approvals")
    return tuple(errors)


def sqlite_log_integrity_summary(db_path: Path) -> dict[str, object]:
    """Return scheduler-friendly SQLite log health checks."""

    summary = sqlite_log_summary(db_path)
    errors = sqlite_log_validation_errors(db_path)
    resolved = Path(db_path)
    database_size_bytes = resolved.stat().st_size if resolved.exists() else 0
    warnings = []
    if database_size_bytes > DEFAULT_SQLITE_SIZE_WARNING_BYTES:
        warnings.append(
            "SQLite log database exceeds the default local size warning threshold"
        )
    return {
        "ok": not errors,
        "db_path": str(db_path),
        "schema_version": summary.get("schema_version"),
        "expected_schema_version": TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION,
        "migration_required": bool(summary.get("migration_required", False)),
        "metadata_ok": bool(summary.get("metadata_ok", False)),
        "database_readable": bool(summary.get("database_readable", False)),
        "run_count": int(str(summary.get("run_count", 0))),
        "outcome_count": int(str(summary.get("outcome_count", 0))),
        "missing_outcome_run_ids": _object_string_list(
            summary.get("missing_outcome_run_ids", [])
        ),
        "multiple_outcome_run_ids": _object_string_list(
            summary.get("multiple_outcome_run_ids", [])
        ),
        "network_access_allowed_count": int(
            str(summary.get("network_access_allowed_count", 0))
        ),
        "external_submission_approved_count": int(
            str(summary.get("external_submission_approved_count", 0))
        ),
        "database_size_bytes": database_size_bytes,
        "size_warning_threshold_bytes": DEFAULT_SQLITE_SIZE_WARNING_BYTES,
        "warnings": warnings,
        "errors": list(errors),
        "disclaimer": TOP_LEVEL_SQLITE_LOG_DISCLAIMER,
    }


def sqlite_log_pragmas(db_path: Path) -> dict[str, object]:
    """Return SQLite PRAGMA diagnostics for local operator checks."""

    resolved = Path(db_path)
    if not resolved.exists():
        return {
            "ok": False,
            "db_path": str(resolved),
            "database_exists": False,
            "disclaimer": TOP_LEVEL_SQLITE_LOG_DISCLAIMER,
        }
    with closing(sqlite3.connect(resolved)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        foreign_keys = int(connection.execute("PRAGMA foreign_keys").fetchone()[0])
        journal_mode = str(connection.execute("PRAGMA journal_mode").fetchone()[0])
        integrity_check = str(
            connection.execute("PRAGMA integrity_check").fetchone()[0]
        )
        page_count = int(connection.execute("PRAGMA page_count").fetchone()[0])
        page_size = int(connection.execute("PRAGMA page_size").fetchone()[0])
    return {
        "ok": foreign_keys == 1 and integrity_check == "ok",
        "db_path": str(resolved),
        "database_exists": True,
        "foreign_keys": foreign_keys,
        "journal_mode": journal_mode,
        "integrity_check": integrity_check,
        "page_count": page_count,
        "page_size": page_size,
        "estimated_size_bytes": page_count * page_size,
        "disclaimer": TOP_LEVEL_SQLITE_LOG_DISCLAIMER,
    }


def sqlite_log_backup(
    db_path: Path,
    *,
    backup_dir: Path | None = None,
) -> dict[str, object]:
    """Create a timestamped local backup under ignored top-level logs."""

    resolved = Path(db_path)
    destination_dir = backup_dir or resolved.parent / DEFAULT_SQLITE_BACKUP_DIRNAME
    if not resolved.exists():
        return {
            "ok": False,
            "db_path": str(resolved),
            "backup_path": None,
            "error": "SQLite log database does not exist",
            "disclaimer": TOP_LEVEL_SQLITE_LOG_DISCLAIMER,
        }
    destination_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    backup_path = destination_dir / f"{resolved.stem}-{timestamp}.sqlite3"
    with (
        closing(sqlite3.connect(resolved)) as source,
        closing(sqlite3.connect(backup_path)) as destination,
    ):
        source.backup(destination)
    return {
        "ok": True,
        "db_path": str(resolved),
        "backup_path": str(backup_path),
        "backup_size_bytes": backup_path.stat().st_size,
        "backup_dir": str(destination_dir),
        "disclaimer": TOP_LEVEL_SQLITE_LOG_DISCLAIMER,
    }


def sqlite_log_vacuum(db_path: Path) -> dict[str, object]:
    """Compact a local SQLite log database with VACUUM."""

    resolved = Path(db_path)
    if not resolved.exists():
        return {
            "ok": False,
            "db_path": str(resolved),
            "error": "SQLite log database does not exist",
            "disclaimer": TOP_LEVEL_SQLITE_LOG_DISCLAIMER,
        }
    before_size = resolved.stat().st_size
    with closing(sqlite3.connect(resolved)) as connection:
        connection.execute("VACUUM")
    after_size = resolved.stat().st_size
    return {
        "ok": True,
        "db_path": str(resolved),
        "before_size_bytes": before_size,
        "after_size_bytes": after_size,
        "bytes_reclaimed": max(0, before_size - after_size),
        "disclaimer": TOP_LEVEL_SQLITE_LOG_DISCLAIMER,
    }


def sqlite_log_retention_summary(
    db_path: Path,
    *,
    backup_dir: Path | None = None,
) -> dict[str, object]:
    """Report database age, size, and ignored backup coverage."""

    resolved = Path(db_path)
    destination_dir = backup_dir or resolved.parent / DEFAULT_SQLITE_BACKUP_DIRNAME
    backup_paths = sorted(destination_dir.glob("*.sqlite3"))
    now = datetime.now(UTC)
    database_mtime = (
        datetime.fromtimestamp(resolved.stat().st_mtime, UTC)
        if resolved.exists()
        else None
    )
    oldest_backup_mtime = (
        datetime.fromtimestamp(min(path.stat().st_mtime for path in backup_paths), UTC)
        if backup_paths
        else None
    )
    return {
        "ok": resolved.exists(),
        "db_path": str(resolved),
        "database_exists": resolved.exists(),
        "database_size_bytes": resolved.stat().st_size if resolved.exists() else 0,
        "database_age_seconds": (
            round((now - database_mtime).total_seconds(), 6)
            if database_mtime is not None
            else None
        ),
        "backup_dir": str(destination_dir),
        "backup_count": len(backup_paths),
        "backup_total_size_bytes": sum(path.stat().st_size for path in backup_paths),
        "oldest_backup_age_seconds": (
            round((now - oldest_backup_mtime).total_seconds(), 6)
            if oldest_backup_mtime is not None
            else None
        ),
        "backup_paths": [str(path) for path in backup_paths[-5:]],
        "retention_policy": (
            "Generated SQLite logs and backups are local-only artifacts under logs/."
        ),
        "disclaimer": TOP_LEVEL_SQLITE_LOG_DISCLAIMER,
    }


def sqlite_log_migration_summary(db_path: Path) -> dict[str, object]:
    """Return current SQLite schema-version compatibility status."""

    summary = sqlite_log_summary(db_path)
    return {
        "db_path": str(db_path),
        "current_schema_version": summary.get("schema_version"),
        "expected_schema_version": TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION,
        "migration_required": summary.get("schema_version")
        != TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION,
        "supported_migrations": [],
        "disclaimer": TOP_LEVEL_SQLITE_LOG_DISCLAIMER,
    }


def sqlite_recent_runs(db_path: Path, *, limit: int = 10) -> dict[str, object]:
    """Return recent background runs from the SQLite operational log."""

    rows = _fetch_rows(
        db_path,
        """
        SELECT *
        FROM background_runs
        ORDER BY completed_at_utc DESC, run_id DESC
        LIMIT ?
        """,
        (max(1, limit),),
    )
    return {
        "db_path": str(db_path),
        "schema_version": TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION,
        "disclaimer": TOP_LEVEL_SQLITE_LOG_DISCLAIMER,
        "run_count": len(rows),
        "runs": [_run_row_to_mapping(row) for row in rows],
    }


def sqlite_needs_follow_up(db_path: Path, *, limit: int = 10) -> dict[str, object]:
    """Return recent needs-follow-up outcomes from SQLite."""

    rows = _fetch_rows(
        db_path,
        """
        SELECT *
        FROM needs_follow_up_outcomes
        ORDER BY created_at_utc DESC, follow_up_id DESC
        LIMIT ?
        """,
        (max(1, limit),),
    )
    return {
        "db_path": str(db_path),
        "schema_version": TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION,
        "disclaimer": TOP_LEVEL_SQLITE_LOG_DISCLAIMER,
        "needs_follow_up_count": len(rows),
        "needs_follow_up": [_needs_follow_up_row_to_mapping(row) for row in rows],
    }


def sqlite_log_export(db_path: Path, *, limit: int = 10) -> dict[str, object]:
    """Export a small review-safe JSON summary from SQLite logs."""

    return {
        "db_path": str(db_path),
        "schema_version": TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION,
        "disclaimer": TOP_LEVEL_SQLITE_LOG_DISCLAIMER,
        "export_scope": "review_safe_summary",
        "summary": sqlite_log_summary(db_path),
        "integrity": sqlite_log_integrity_summary(db_path),
        "migration": sqlite_log_migration_summary(db_path),
        "recent_runs": sqlite_recent_runs(db_path, limit=limit)["runs"],
        "needs_follow_up": sqlite_needs_follow_up(db_path, limit=limit)[
            "needs_follow_up"
        ],
        "uncertainty_and_limitations": [
            "SQLite exports are local workflow summaries only.",
            "A logged run is not a detection, discovery, or external validation.",
            "Needs-follow-up outcomes require human review and mandatory local tests.",
        ],
    }


def validate_sqlite_log_commit_paths(
    paths: list[Path] | tuple[Path, ...],
    *,
    project_root: Path | None = None,
) -> dict[str, object]:
    """Reject generated top-level SQLite log databases in tracked/staged paths."""

    root = project_root or Path.cwd()
    forbidden: list[str] = []
    for path in paths:
        resolved = Path(path)
        rel = _relative_path(resolved, root)
        if _is_forbidden_top_level_sqlite_log(rel):
            forbidden.append(rel.as_posix())
    return {
        "ok": not forbidden,
        "project_root": str(root),
        "forbidden_path_count": len(forbidden),
        "forbidden_paths": sorted(forbidden),
        "forbidden_patterns": [
            "logs/*.sqlite",
            "logs/*.sqlite3",
            "logs/*.db",
            "logs/*-wal",
            "logs/*-shm",
        ],
        "disclaimer": TOP_LEVEL_SQLITE_LOG_DISCLAIMER,
    }


def _create_schema(connection: sqlite3.Connection) -> None:
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

        CREATE TABLE IF NOT EXISTS reviewed_outcomes (
            review_id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL UNIQUE REFERENCES background_runs(run_id),
            target_id TEXT NOT NULL,
            track TEXT NOT NULL,
            outcome_status TEXT NOT NULL,
            reviewed_at_utc TEXT NOT NULL,
            reason_codes_json TEXT NOT NULL,
            negative_evidence_json TEXT NOT NULL,
            blocking_issues_json TEXT NOT NULL,
            recommended_next_action TEXT NOT NULL,
            network_access_allowed INTEGER NOT NULL CHECK (network_access_allowed IN (0, 1))
        );

        CREATE TABLE IF NOT EXISTS needs_follow_up_outcomes (
            follow_up_id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL UNIQUE REFERENCES background_runs(run_id),
            target_id TEXT NOT NULL,
            track TEXT NOT NULL,
            follow_up_status TEXT NOT NULL,
            created_at_utc TEXT NOT NULL,
            trigger_types_json TEXT NOT NULL,
            reason_codes_json TEXT NOT NULL,
            required_tests_json TEXT NOT NULL,
            blocking_issues_json TEXT NOT NULL,
            report_required INTEGER NOT NULL CHECK (report_required IN (0, 1)),
            human_review_required INTEGER NOT NULL CHECK (human_review_required IN (0, 1)),
            submission_requires_user_approval INTEGER NOT NULL
                CHECK (submission_requires_user_approval IN (0, 1)),
            network_access_allowed INTEGER NOT NULL CHECK (network_access_allowed IN (0, 1))
        );

        CREATE TABLE IF NOT EXISTS draft_reports (
            draft_id TEXT PRIMARY KEY,
            run_id TEXT,
            target_id TEXT NOT NULL,
            track TEXT NOT NULL,
            draft_status TEXT NOT NULL,
            markdown_path TEXT NOT NULL,
            external_submission_allowed INTEGER NOT NULL
                CHECK (external_submission_allowed IN (0, 1)),
            network_access_allowed INTEGER NOT NULL CHECK (network_access_allowed IN (0, 1))
        );

        CREATE TABLE IF NOT EXISTS user_decisions (
            decision_id TEXT PRIMARY KEY,
            run_id TEXT,
            target_id TEXT NOT NULL,
            track TEXT NOT NULL,
            decision TEXT NOT NULL,
            rationale TEXT NOT NULL,
            external_submission_approved INTEGER NOT NULL
                CHECK (external_submission_approved IN (0, 1)),
            network_access_allowed INTEGER NOT NULL CHECK (network_access_allowed IN (0, 1))
        );

        CREATE TABLE IF NOT EXISTS validation_events (
            validation_id TEXT PRIMARY KEY,
            created_at_utc TEXT NOT NULL,
            command TEXT NOT NULL,
            ok INTEGER NOT NULL CHECK (ok IN (0, 1)),
            errors_json TEXT NOT NULL,
            warnings_json TEXT NOT NULL
        );
        """
    )


def _insert_reviewed_outcome(
    connection: sqlite3.Connection,
    outcome: dict[str, Any],
) -> None:
    connection.execute(
        """
        INSERT INTO reviewed_outcomes (
            review_id, run_id, target_id, track, outcome_status, reviewed_at_utc,
            reason_codes_json, negative_evidence_json, blocking_issues_json,
            recommended_next_action, network_access_allowed
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(outcome["review_id"]),
            str(outcome["run_id"]),
            str(outcome["target_id"]),
            str(outcome["track"]),
            str(outcome["outcome_status"]),
            str(outcome["reviewed_at_utc"]),
            _json_text(outcome.get("reason_codes", [])),
            _json_text(outcome.get("negative_evidence", [])),
            _json_text(outcome.get("blocking_issues", [])),
            str(outcome["recommended_next_action"]),
            int(bool(outcome.get("network_access_allowed", False))),
        ),
    )


def _insert_needs_follow_up_outcome(
    connection: sqlite3.Connection,
    outcome: dict[str, Any],
) -> None:
    connection.execute(
        """
        INSERT INTO needs_follow_up_outcomes (
            follow_up_id, run_id, target_id, track, follow_up_status, created_at_utc,
            trigger_types_json, reason_codes_json, required_tests_json,
            blocking_issues_json, report_required, human_review_required,
            submission_requires_user_approval, network_access_allowed
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(outcome["follow_up_id"]),
            str(outcome["run_id"]),
            str(outcome["target_id"]),
            str(outcome["track"]),
            str(outcome["follow_up_status"]),
            str(outcome["created_at_utc"]),
            _json_text(outcome.get("trigger_types", [])),
            _json_text(outcome.get("reason_codes", [])),
            _json_text(outcome.get("required_tests", [])),
            _json_text(outcome.get("blocking_issues", [])),
            int(bool(outcome.get("report_required", False))),
            int(bool(outcome.get("human_review_required", False))),
            int(bool(outcome.get("submission_requires_user_approval", False))),
            int(bool(outcome.get("network_access_allowed", False))),
        ),
    )


def _run_has_any_outcome(connection: sqlite3.Connection, run_id: str) -> bool:
    reviewed = connection.execute(
        "SELECT 1 FROM reviewed_outcomes WHERE run_id = ?",
        (run_id,),
    ).fetchone()
    follow_up = connection.execute(
        "SELECT 1 FROM needs_follow_up_outcomes WHERE run_id = ?",
        (run_id,),
    ).fetchone()
    return reviewed is not None or follow_up is not None


def _metadata(connection: sqlite3.Connection) -> dict[str, str]:
    try:
        rows = connection.execute("SELECT key, value FROM metadata").fetchall()
    except sqlite3.OperationalError:
        return {}
    return {str(row["key"]): str(row["value"]) for row in rows}


def _upsert_metadata(
    connection: sqlite3.Connection,
    values: dict[str, str],
) -> None:
    connection.executemany(
        "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
        tuple(sorted(values.items())),
    )


def _count_external_approvals(db_path: Path) -> int:
    with closing(sqlite3.connect(db_path)) as connection:
        try:
            row = connection.execute(
                """
                SELECT COALESCE(SUM(external_submission_approved), 0)
                FROM user_decisions
                """
            ).fetchone()
        except sqlite3.OperationalError:
            return 0
    return int(row[0]) if row is not None else 0


def _fetch_rows(
    db_path: Path,
    query: str,
    parameters: tuple[object, ...] = (),
) -> list[sqlite3.Row]:
    if not Path(db_path).exists():
        return []
    with closing(sqlite3.connect(db_path)) as connection:
        connection.row_factory = sqlite3.Row
        try:
            return list(connection.execute(query, parameters).fetchall())
        except sqlite3.DatabaseError:
            return []


def _run_row_to_mapping(row: sqlite3.Row) -> dict[str, object]:
    return {
        "run_id": str(row["run_id"]),
        "target_id": str(row["target_id"]),
        "track": str(row["track"]),
        "status": str(row["status"]),
        "started_at_utc": str(row["started_at_utc"]),
        "completed_at_utc": str(row["completed_at_utc"]),
        "config_version": str(row["config_version"]),
        "code_commit": str(row["code_commit"]),
        "candidate_count": int(row["candidate_count"]),
        "execution_mode": str(row["execution_mode"]),
        "selected_priority_score": row["selected_priority_score"],
        "recommended_pathways": _json_list(row["recommended_pathways_json"]),
        "blocking_issues": _json_list(row["blocking_issues_json"]),
        "target_selection_rationale": _json_list(
            row["target_selection_rationale_json"]
        ),
        "negative_result_logged": bool(row["negative_result_logged"]),
        "requires_human_review": bool(row["requires_human_review"]),
        "reviewed_workflow_status": str(row["reviewed_workflow_status"]),
        "network_access_allowed": bool(row["network_access_allowed"]),
        "uncertainty_notes": [
            "Run records describe local workflow state only.",
            "Target-priority and scheduler scores are not candidate evidence.",
        ],
    }


def _needs_follow_up_row_to_mapping(row: sqlite3.Row) -> dict[str, object]:
    return {
        "follow_up_id": str(row["follow_up_id"]),
        "run_id": str(row["run_id"]),
        "target_id": str(row["target_id"]),
        "track": str(row["track"]),
        "follow_up_status": str(row["follow_up_status"]),
        "created_at_utc": str(row["created_at_utc"]),
        "trigger_types": _json_list(row["trigger_types_json"]),
        "reason_codes": _json_list(row["reason_codes_json"]),
        "required_tests": _json_list(row["required_tests_json"]),
        "blocking_issues": _json_list(row["blocking_issues_json"]),
        "report_required": bool(row["report_required"]),
        "human_review_required": bool(row["human_review_required"]),
        "submission_requires_user_approval": bool(
            row["submission_requires_user_approval"]
        ),
        "network_access_allowed": bool(row["network_access_allowed"]),
        "negative_evidence": [
            "Needs-follow-up is not a detection or external validation.",
            "False-positive explanations remain the default hypothesis.",
        ],
        "uncertainty_notes": [
            "Mandatory local tests and human review are still required.",
            "External submission remains blocked unless directly approved by the user.",
        ],
    }


def _json_list(value: object) -> list[str]:
    data = json.loads(str(value))
    if not isinstance(data, list):
        return []
    return [str(item) for item in data]


def _object_string_list(value: object) -> list[str]:
    if not isinstance(value, list | tuple):
        return []
    return [str(item) for item in value]


def _relative_path(path: Path, root: Path) -> Path:
    try:
        return path.resolve().relative_to(root.resolve())
    except ValueError:
        return path


def _is_forbidden_top_level_sqlite_log(path: Path) -> bool:
    parts = path.parts
    if len(parts) < 2 or parts[0] != "logs":
        return False
    if len(parts) > 2 and parts[1] != DEFAULT_SQLITE_BACKUP_DIRNAME:
        return False
    name = parts[-1]
    return (
        path.suffix in FORBIDDEN_SQLITE_LOG_SUFFIXES
        or name.endswith(FORBIDDEN_SQLITE_LOG_FILENAMES)
    )


def _json_text(value: object) -> str:
    return json.dumps(value, sort_keys=True)


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items()))
