"""Non-mutating readiness preflight for future SQLite operational log adapters."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from techno_search.sqlite_operational_log_adapter_contract import (
    sqlite_operational_log_adapter_contract_summary,
)
from techno_search.sqlite_operational_log_adapter_ddl_preview import (
    sqlite_operational_log_adapter_ddl_preview_summary,
)
from techno_search.sqlite_operational_log_adapter_dry_run_manifest import (
    sqlite_operational_log_adapter_dry_run_manifest_summary,
)
from techno_search.sqlite_operational_log_adapter_execution_preview import (
    sqlite_operational_log_adapter_execution_preview_summary,
)
from techno_search.sqlite_operational_log_adapter_insert_preview import (
    sqlite_operational_log_adapter_insert_preview_summary,
)
from techno_search.sqlite_operational_log_adapter_plan import (
    sqlite_operational_log_adapter_plan_summary,
)
from techno_search.sqlite_operational_log_adapter_row_preview import (
    sqlite_operational_log_adapter_row_preview_summary,
)
from techno_search.sqlite_operational_log_registry import (
    sqlite_operational_log_registry_summary,
)

SQLITE_OPERATIONAL_LOG_ADAPTER_READINESS_PREFLIGHT_SCHEMA_VERSION = (
    "sqlite_operational_log_adapter_readiness_preflight_v1"
)

SQLITE_OPERATIONAL_LOG_ADAPTER_READINESS_PREFLIGHT_DISCLAIMER = (
    "SQLite operational log adapter readiness preflights are local planning "
    "artifacts only. They reconcile registry, plan, contract, preview, and "
    "dry-run manifest gates before any future adapter implementation. They do "
    "not open databases, execute SQL, insert rows, create tables, migrate "
    "fixture records, mutate databases, ingest real observation data, "
    "authorize live data access, authorize external submission, or constitute "
    "detections, discoveries, or external validation."
)


@dataclass(frozen=True)
class SqliteOperationalLogAdapterReadinessGate:
    gate_name: str
    ok: bool


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_preflight_path() -> Path:
    return (
        _project_root()
        / "tests"
        / "fixtures"
        / "sqlite_operational_log_adapter_readiness_preflight.json"
    )


def _schema_count(project_root: Path | None = None) -> int:
    root = project_root if project_root is not None else _project_root()
    return len(list((root / "schemas").glob("*.schema.json")))


def load_sqlite_operational_log_adapter_readiness_preflight_expectations(
    path: Path | None = None,
) -> dict[str, Any]:
    preflight_path = path if path is not None else _default_preflight_path()
    raw = json.loads(preflight_path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], raw["expected_preflight"])


def _count(summary: dict[str, Any], *keys: str) -> int:
    for key in keys:
        if key in summary:
            return int(summary.get(key, 0))
    return 0


def sqlite_operational_log_adapter_readiness_preflight_summary(
    path: Path | None = None,
    *,
    registry_summary: dict[str, Any] | None = None,
    adapter_plan_summary: dict[str, Any] | None = None,
    adapter_contract_summary: dict[str, Any] | None = None,
    ddl_preview_summary: dict[str, Any] | None = None,
    row_preview_summary: dict[str, Any] | None = None,
    insert_preview_summary: dict[str, Any] | None = None,
    execution_preview_summary: dict[str, Any] | None = None,
    dry_run_manifest_summary: dict[str, Any] | None = None,
    schema_count: int | None = None,
) -> dict[str, Any]:
    expected = load_sqlite_operational_log_adapter_readiness_preflight_expectations(path)
    registry = (
        registry_summary
        if registry_summary is not None
        else sqlite_operational_log_registry_summary()
    )
    plan = (
        adapter_plan_summary
        if adapter_plan_summary is not None
        else sqlite_operational_log_adapter_plan_summary(registry_summary=registry)
    )
    contract = (
        adapter_contract_summary
        if adapter_contract_summary is not None
        else sqlite_operational_log_adapter_contract_summary(adapter_plan_summary=plan)
    )
    ddl_preview = (
        ddl_preview_summary
        if ddl_preview_summary is not None
        else sqlite_operational_log_adapter_ddl_preview_summary(
            adapter_contract_summary=contract
        )
    )
    row_preview = (
        row_preview_summary
        if row_preview_summary is not None
        else sqlite_operational_log_adapter_row_preview_summary(
            adapter_contract_summary=contract,
            adapter_plan_summary=plan,
            registry_summary=registry,
        )
    )
    insert_preview = (
        insert_preview_summary
        if insert_preview_summary is not None
        else sqlite_operational_log_adapter_insert_preview_summary(
            row_preview_summary=row_preview
        )
    )
    execution_preview = (
        execution_preview_summary
        if execution_preview_summary is not None
        else sqlite_operational_log_adapter_execution_preview_summary(
            insert_preview_summary=insert_preview
        )
    )
    dry_run = (
        dry_run_manifest_summary
        if dry_run_manifest_summary is not None
        else sqlite_operational_log_adapter_dry_run_manifest_summary(
            ddl_preview_summary=ddl_preview,
            execution_preview_summary=execution_preview,
        )
    )

    gates = [
        SqliteOperationalLogAdapterReadinessGate("registry", bool(registry.get("ok"))),
        SqliteOperationalLogAdapterReadinessGate("adapter_plan", bool(plan.get("ok"))),
        SqliteOperationalLogAdapterReadinessGate("adapter_contract", bool(contract.get("ok"))),
        SqliteOperationalLogAdapterReadinessGate("ddl_preview", bool(ddl_preview.get("ok"))),
        SqliteOperationalLogAdapterReadinessGate("row_preview", bool(row_preview.get("ok"))),
        SqliteOperationalLogAdapterReadinessGate("insert_preview", bool(insert_preview.get("ok"))),
        SqliteOperationalLogAdapterReadinessGate(
            "execution_preview", bool(execution_preview.get("ok"))
        ),
        SqliteOperationalLogAdapterReadinessGate("dry_run_manifest", bool(dry_run.get("ok"))),
    ]
    failed_gate_names = [gate.gate_name for gate in gates if not gate.ok]

    actual_schema_count = schema_count if schema_count is not None else _schema_count()
    registered_log_count = _count(registry, "registered_log_count", "registered_count")
    planned_count = _count(plan, "planned_log_count", "planned_count")
    phase_count = _count(plan, "phase_count")
    contract_phase_count = _count(contract, "phase_contract_count", "phase_count")
    ddl_statement_count = _count(ddl_preview, "ddl_statement_count")
    row_count = _count(row_preview, "row_count")
    insert_count = _count(insert_preview, "insert_count")
    execution_operation_count = _count(execution_preview, "operation_count")
    dry_run_phase_count = _count(dry_run, "phase_count")

    readiness_status = str(expected.get("readiness_status", "preflight_only"))
    database_open_allowed = bool(expected.get("database_open_allowed", False))
    execution_allowed = bool(expected.get("execution_allowed", False))
    mutation_allowed = bool(expected.get("mutation_allowed", False))
    live_data_authorized = bool(expected.get("live_data_authorized", False))
    external_submission_authorized = bool(
        expected.get("external_submission_authorized", False)
    )

    issues: list[str] = []
    if expected.get("require_all_upstream_gates_ok", True) and failed_gate_names:
        issues.append(
            "readiness preflight upstream gate failure(s): "
            + ", ".join(failed_gate_names)
        )
    for label, actual, key in [
        ("registered log count", registered_log_count, "expected_registered_log_count"),
        ("planned log count", planned_count, "expected_planned_count"),
        ("phase count", phase_count, "expected_phase_count"),
        ("contract phase count", contract_phase_count, "expected_phase_count"),
        ("DDL statement count", ddl_statement_count, "expected_ddl_statement_count"),
        ("row count", row_count, "expected_row_count"),
        ("insert count", insert_count, "expected_insert_count"),
        (
            "execution operation count",
            execution_operation_count,
            "expected_execution_operation_count",
        ),
        ("dry-run phase count", dry_run_phase_count, "expected_phase_count"),
        ("schema count", actual_schema_count, "expected_schema_count"),
    ]:
        expected_value = int(expected.get(key, 0))
        if actual != expected_value:
            issues.append(f"readiness preflight {label} {actual} != expected {expected_value}")
    if str(dry_run.get("manifest_status", "")) != "preview_only":
        issues.append("readiness preflight requires dry-run manifest status preview_only")
    if readiness_status != "preflight_only":
        issues.append("readiness preflight status must remain preflight_only")
    if database_open_allowed:
        issues.append("readiness preflight must not allow opening databases")
    if execution_allowed:
        issues.append("readiness preflight must remain non-executing")
    if mutation_allowed:
        issues.append("readiness preflight must not authorize mutation")
    if live_data_authorized:
        issues.append("readiness preflight must not authorize live data")
    if external_submission_authorized:
        issues.append("readiness preflight must not authorize external submission")

    return {
        "schema_version": SQLITE_OPERATIONAL_LOG_ADAPTER_READINESS_PREFLIGHT_SCHEMA_VERSION,
        "disclaimer": SQLITE_OPERATIONAL_LOG_ADAPTER_READINESS_PREFLIGHT_DISCLAIMER,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "readiness_status": readiness_status,
        "upstream_gate_count": len(gates),
        "upstream_gate_failure_count": len(failed_gate_names),
        "failed_upstream_gates": failed_gate_names,
        "registered_log_count": registered_log_count,
        "planned_count": planned_count,
        "phase_count": phase_count,
        "contract_phase_count": contract_phase_count,
        "ddl_statement_count": ddl_statement_count,
        "row_count": row_count,
        "insert_count": insert_count,
        "execution_operation_count": execution_operation_count,
        "dry_run_phase_count": dry_run_phase_count,
        "schema_count": actual_schema_count,
        "database_open_allowed": database_open_allowed,
        "execution_allowed": execution_allowed,
        "mutation_allowed": mutation_allowed,
        "live_data_authorized": live_data_authorized,
        "external_submission_authorized": external_submission_authorized,
        "upstream_gates": [gate.__dict__ for gate in gates],
    }
