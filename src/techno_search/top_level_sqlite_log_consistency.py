"""Consistency checks for top-level SQLite workflow logs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from techno_search.log_store import (
    default_sqlite_log_path,
    sqlite_log_integrity_summary,
    sqlite_log_migration_plan,
    sqlite_log_migration_summary,
    sqlite_log_pragmas,
    sqlite_log_retention_summary,
    sqlite_log_summary,
    sqlite_log_weekly_digest,
    validate_sqlite_log_commit_paths,
)
from techno_search.validation import validate_sqlite_log_database

TOP_LEVEL_SQLITE_LOG_CONSISTENCY_SCHEMA_VERSION = (
    "top_level_sqlite_log_consistency_v1"
)

TOP_LEVEL_SQLITE_LOG_CONSISTENCY_DISCLAIMER = (
    "Top-level SQLite log consistency checks are local workflow and provenance "
    "visibility gates only. They verify SQLite log health, migration state, "
    "run/outcome alignment, retention/pragmas, commit-guard state, and disabled "
    "network/external authorization counts. They are not detections, "
    "discoveries, external validation, or external submission approval."
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_expected_path() -> Path:
    return (
        _project_root()
        / "tests"
        / "fixtures"
        / "top_level_sqlite_log_consistency.json"
    )


def load_top_level_sqlite_log_expectations(
    path: Path | None = None,
) -> dict[str, Any]:
    expectation_path = path if path is not None else _default_expected_path()
    raw = json.loads(expectation_path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], raw["expected_sqlite_log"])


def _count(summary: dict[str, Any], key: str) -> int:
    return int(summary.get(key, 0))


def _bool(summary: dict[str, Any], key: str) -> bool:
    return bool(summary.get(key, False))


def top_level_sqlite_log_consistency_summary(
    expected_path: Path | None = None,
    *,
    db_path: Path | None = None,
    sqlite_summary: dict[str, Any] | None = None,
    integrity_summary: dict[str, Any] | None = None,
    migration_summary: dict[str, Any] | None = None,
    migration_plan: dict[str, Any] | None = None,
    weekly_digest: dict[str, Any] | None = None,
    retention_summary: dict[str, Any] | None = None,
    pragmas_summary: dict[str, Any] | None = None,
    validation_summary: dict[str, Any] | None = None,
    commit_guard: dict[str, Any] | None = None,
) -> dict[str, Any]:
    expected = load_top_level_sqlite_log_expectations(expected_path)
    resolved_db_path = db_path if db_path is not None else default_sqlite_log_path()

    sqlite_logs = (
        sqlite_summary
        if sqlite_summary is not None
        else sqlite_log_summary(resolved_db_path)
    )
    integrity = (
        integrity_summary
        if integrity_summary is not None
        else sqlite_log_integrity_summary(resolved_db_path)
    )
    migration = (
        migration_summary
        if migration_summary is not None
        else sqlite_log_migration_summary(resolved_db_path)
    )
    plan = (
        migration_plan
        if migration_plan is not None
        else sqlite_log_migration_plan(resolved_db_path)
    )
    digest = (
        weekly_digest
        if weekly_digest is not None
        else sqlite_log_weekly_digest(resolved_db_path)
    )
    retention = (
        retention_summary
        if retention_summary is not None
        else sqlite_log_retention_summary(resolved_db_path)
    )
    pragmas = (
        pragmas_summary
        if pragmas_summary is not None
        else sqlite_log_pragmas(resolved_db_path)
    )
    validation = (
        validation_summary
        if validation_summary is not None
        else validate_sqlite_log_database(resolved_db_path).as_dict()
    )
    guard = (
        commit_guard
        if commit_guard is not None
        else validate_sqlite_log_commit_paths([], project_root=_project_root())
    )

    run_count = _count(sqlite_logs, "run_count")
    outcome_count = _count(sqlite_logs, "outcome_count")
    network_count = _count(sqlite_logs, "network_access_allowed_count")
    external_count = _count(sqlite_logs, "external_submission_approved_count")
    forbidden_path_count = _count(guard, "forbidden_path_count")
    min_run_count = int(expected.get("min_run_count", 0))
    max_network_count = int(expected.get("max_network_access_allowed_count", 0))
    max_external_count = int(
        expected.get("max_external_submission_approved_count", 0)
    )

    issues: list[str] = []
    if run_count < min_run_count:
        issues.append(f"run count {run_count} < minimum {min_run_count}")
    if (
        bool(expected.get("require_database_exists", True))
        and not _bool(sqlite_logs, "database_exists")
    ):
        issues.append("SQLite log database does not exist")
    if (
        bool(expected.get("require_database_readable", True))
        and not _bool(sqlite_logs, "database_readable")
    ):
        issues.append("SQLite log database is not readable")
    if bool(expected.get("require_metadata_ok", True)) and not _bool(
        sqlite_logs,
        "metadata_ok",
    ):
        issues.append("SQLite log metadata is incomplete")
    if bool(expected.get("require_validation_ok", True)) and not _bool(
        validation,
        "ok",
    ):
        issues.append("SQLite log validation is not ok")
    if bool(expected.get("require_integrity_ok", True)) and not _bool(
        integrity,
        "ok",
    ):
        issues.append("SQLite log integrity is not ok")
    if bool(expected.get("require_pragmas_ok", True)) and not _bool(pragmas, "ok"):
        issues.append("SQLite log PRAGMA checks are not ok")
    if bool(expected.get("require_weekly_digest_ok", True)) and not _bool(
        digest,
        "ok",
    ):
        issues.append("SQLite log weekly digest is not ok")
    if bool(expected.get("require_retention_ok", True)) and not _bool(
        retention,
        "ok",
    ):
        issues.append("SQLite log retention summary is not ok")
    if bool(expected.get("require_commit_guard_ok", True)) and not _bool(
        guard,
        "ok",
    ):
        issues.append("SQLite log commit guard is not ok")
    if bool(expected.get("require_no_migration_required", True)) and (
        _bool(migration, "migration_required") or _bool(plan, "migration_required")
    ):
        issues.append("SQLite log migration is required")
    if (
        bool(expected.get("require_outcome_count_matches_run_count", True))
        and outcome_count != run_count
    ):
        issues.append(f"outcome count {outcome_count} != run count {run_count}")
    if network_count > max_network_count:
        issues.append(
            "network access allowed count "
            f"{network_count} > maximum {max_network_count}"
        )
    if external_count > max_external_count:
        issues.append(
            "external submission approved count "
            f"{external_count} > maximum {max_external_count}"
        )
    if forbidden_path_count:
        issues.append(f"{forbidden_path_count} forbidden SQLite log path(s) found")

    return {
        "schema_version": TOP_LEVEL_SQLITE_LOG_CONSISTENCY_SCHEMA_VERSION,
        "disclaimer": TOP_LEVEL_SQLITE_LOG_CONSISTENCY_DISCLAIMER,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "db_path": str(sqlite_logs.get("db_path", resolved_db_path)),
        "database_exists": _bool(sqlite_logs, "database_exists"),
        "database_readable": _bool(sqlite_logs, "database_readable"),
        "metadata_ok": _bool(sqlite_logs, "metadata_ok"),
        "validation_ok": _bool(validation, "ok"),
        "integrity_ok": _bool(integrity, "ok"),
        "pragmas_ok": _bool(pragmas, "ok"),
        "weekly_digest_ok": _bool(digest, "ok"),
        "retention_ok": _bool(retention, "ok"),
        "commit_guard_ok": _bool(guard, "ok"),
        "migration_required": _bool(migration, "migration_required"),
        "migration_plan_required": _bool(plan, "migration_required"),
        "run_count": run_count,
        "outcome_count": outcome_count,
        "min_run_count": min_run_count,
        "network_access_allowed_count": network_count,
        "external_submission_approved_count": external_count,
        "forbidden_path_count": forbidden_path_count,
    }
