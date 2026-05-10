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

    with closing(sqlite3.connect(resolved)) as connection:
        connection.row_factory = sqlite3.Row
        metadata = _metadata(connection)
        run_rows = connection.execute("SELECT * FROM background_runs").fetchall()
        reviewed_rows = connection.execute("SELECT * FROM reviewed_outcomes").fetchall()
        follow_up_rows = connection.execute(
            "SELECT * FROM needs_follow_up_outcomes"
        ).fetchall()

    run_ids = {str(row["run_id"]) for row in run_rows}
    reviewed_run_ids = {str(row["run_id"]) for row in reviewed_rows}
    follow_up_run_ids = {str(row["run_id"]) for row in follow_up_rows}
    outcome_run_ids = reviewed_run_ids | follow_up_run_ids
    multiple_outcome_run_ids = reviewed_run_ids & follow_up_run_ids

    return {
        "ok": not multiple_outcome_run_ids and run_ids <= outcome_run_ids,
        "db_path": str(resolved),
        "schema_version": metadata.get(
            "schema_version", TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION
        ),
        "disclaimer": metadata.get("disclaimer", TOP_LEVEL_SQLITE_LOG_DISCLAIMER),
        "database_exists": True,
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


def _json_text(value: object) -> str:
    return json.dumps(value, sort_keys=True)


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items()))
