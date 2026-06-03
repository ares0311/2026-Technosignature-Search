"""Disabled authorization gate for future SQLite operational log adapters."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from techno_search.sqlite_operational_log_adapter_readiness_preflight import (
    sqlite_operational_log_adapter_readiness_preflight_summary,
)

SQLITE_OPERATIONAL_LOG_ADAPTER_AUTHORIZATION_GATE_SCHEMA_VERSION = (
    "sqlite_operational_log_adapter_authorization_gate_v1"
)

SQLITE_OPERATIONAL_LOG_ADAPTER_AUTHORIZATION_GATE_DISCLAIMER = (
    "SQLite operational log adapter authorization gates are local planning "
    "artifacts only. They keep future adapter implementation, database "
    "opening, SQL execution, fixture migration, mutation, live data access, "
    "and external submission blocked until a future reviewed change is added "
    "deliberately. They do not open databases, execute SQL, insert rows, "
    "create tables, migrate fixture records, mutate databases, ingest real "
    "observation data, authorize live data access, authorize external "
    "submission, or constitute detections, discoveries, or external validation."
)

BLOCKED_AUTHORIZATION_STATUS = "blocked_pending_explicit_operator_approval"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_gate_path() -> Path:
    return (
        _project_root()
        / "tests"
        / "fixtures"
        / "sqlite_operational_log_adapter_authorization_gate.json"
    )


def _schema_count(project_root: Path | None = None) -> int:
    root = project_root if project_root is not None else _project_root()
    return len(list((root / "schemas").glob("*.schema.json")))


def load_sqlite_operational_log_adapter_authorization_gate_expectations(
    path: Path | None = None,
) -> dict[str, Any]:
    gate_path = path if path is not None else _default_gate_path()
    raw = json.loads(gate_path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], raw["expected_gate"])


def sqlite_operational_log_adapter_authorization_gate_summary(
    path: Path | None = None,
    *,
    readiness_preflight_summary: dict[str, Any] | None = None,
    schema_count: int | None = None,
) -> dict[str, Any]:
    expected = load_sqlite_operational_log_adapter_authorization_gate_expectations(path)
    readiness = (
        readiness_preflight_summary
        if readiness_preflight_summary is not None
        else sqlite_operational_log_adapter_readiness_preflight_summary()
    )

    authorization_status = str(
        expected.get("authorization_status", BLOCKED_AUTHORIZATION_STATUS)
    )
    actual_schema_count = schema_count if schema_count is not None else _schema_count()
    readiness_ok = bool(readiness.get("ok", False))
    readiness_status = str(readiness.get("readiness_status", "unknown"))
    readiness_failed_gate_count = int(readiness.get("upstream_gate_failure_count", 0))
    readiness_schema_count = int(readiness.get("schema_count", 0))

    adapter_implementation_allowed = bool(
        expected.get("adapter_implementation_allowed", False)
    )
    database_open_allowed = bool(expected.get("database_open_allowed", False))
    execution_allowed = bool(expected.get("execution_allowed", False))
    fixture_migration_allowed = bool(expected.get("fixture_migration_allowed", False))
    mutation_allowed = bool(expected.get("mutation_allowed", False))
    live_data_authorized = bool(expected.get("live_data_authorized", False))
    external_submission_authorized = bool(
        expected.get("external_submission_authorized", False)
    )

    issues: list[str] = []
    if expected.get("require_readiness_preflight_ok", True) and not readiness_ok:
        issues.append("SQLite operational log adapter readiness preflight is not ok")
    if readiness_status != "preflight_only":
        issues.append("authorization gate requires readiness status preflight_only")
    if readiness_failed_gate_count != int(
        expected.get("expected_readiness_failed_gate_count", 0)
    ):
        issues.append(
            "authorization gate readiness failed-gate count "
            f"{readiness_failed_gate_count} != expected "
            f"{int(expected.get('expected_readiness_failed_gate_count', 0))}"
        )
    if readiness_schema_count != int(expected.get("expected_readiness_schema_count", 0)):
        issues.append(
            "authorization gate readiness schema count "
            f"{readiness_schema_count} != expected "
            f"{int(expected.get('expected_readiness_schema_count', 0))}"
        )
    if actual_schema_count != int(expected.get("expected_schema_count", 0)):
        issues.append(
            "authorization gate schema count "
            f"{actual_schema_count} != expected "
            f"{int(expected.get('expected_schema_count', 0))}"
        )
    if authorization_status != BLOCKED_AUTHORIZATION_STATUS:
        issues.append("authorization gate must remain blocked pending explicit approval")
    if adapter_implementation_allowed:
        issues.append("authorization gate must not allow adapter implementation")
    if database_open_allowed:
        issues.append("authorization gate must not allow opening databases")
    if execution_allowed:
        issues.append("authorization gate must remain non-executing")
    if fixture_migration_allowed:
        issues.append("authorization gate must not allow fixture migration")
    if mutation_allowed:
        issues.append("authorization gate must not authorize mutation")
    if live_data_authorized:
        issues.append("authorization gate must not authorize live data")
    if external_submission_authorized:
        issues.append("authorization gate must not authorize external submission")
    for readiness_flag in [
        "database_open_allowed",
        "execution_allowed",
        "mutation_allowed",
        "live_data_authorized",
        "external_submission_authorized",
    ]:
        if bool(readiness.get(readiness_flag, False)):
            issues.append(f"readiness preflight safety flag is enabled: {readiness_flag}")

    return {
        "schema_version": SQLITE_OPERATIONAL_LOG_ADAPTER_AUTHORIZATION_GATE_SCHEMA_VERSION,
        "disclaimer": SQLITE_OPERATIONAL_LOG_ADAPTER_AUTHORIZATION_GATE_DISCLAIMER,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "authorization_status": authorization_status,
        "readiness_preflight_ok": readiness_ok,
        "readiness_preflight_status": readiness_status,
        "readiness_preflight_failed_gate_count": readiness_failed_gate_count,
        "readiness_preflight_schema_count": readiness_schema_count,
        "schema_count": actual_schema_count,
        "adapter_implementation_allowed": adapter_implementation_allowed,
        "database_open_allowed": database_open_allowed,
        "execution_allowed": execution_allowed,
        "fixture_migration_allowed": fixture_migration_allowed,
        "mutation_allowed": mutation_allowed,
        "live_data_authorized": live_data_authorized,
        "external_submission_authorized": external_submission_authorized,
    }
