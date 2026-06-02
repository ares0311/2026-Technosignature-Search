"""Non-mutating SQLite adapter contract checks for operational logs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from techno_search.sqlite_operational_log_adapter_plan import (
    PHASE_ORDER,
    sqlite_operational_log_adapter_plan_summary,
)

SQLITE_OPERATIONAL_LOG_ADAPTER_CONTRACT_SCHEMA_VERSION = (
    "sqlite_operational_log_adapter_contract_v1"
)

SQLITE_OPERATIONAL_LOG_ADAPTER_CONTRACT_DISCLAIMER = (
    "SQLite operational log adapter contracts are local planning checks only. "
    "They define expected phase tables and provenance columns for future "
    "adapters without creating tables, migrating fixture records, mutating "
    "databases, ingesting real observation data, authorizing live data access, "
    "authorizing external submission, or constituting detections, discoveries, "
    "or external validation."
)


@dataclass(frozen=True)
class SqliteOperationalLogAdapterContractRecord:
    phase_id: str
    table_name: str
    required_columns: tuple[str, ...]
    planned_log_count: int
    mutation_allowed: bool


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_contract_path() -> Path:
    return (
        _project_root()
        / "tests"
        / "fixtures"
        / "sqlite_operational_log_adapter_contract.json"
    )


def load_sqlite_operational_log_adapter_contract_expectations(
    path: Path | None = None,
) -> dict[str, Any]:
    contract_path = path if path is not None else _default_contract_path()
    raw = json.loads(contract_path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], raw["expected_contract"])


def sqlite_operational_log_adapter_contract_summary(
    path: Path | None = None,
    *,
    adapter_plan_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    expected = load_sqlite_operational_log_adapter_contract_expectations(path)
    adapter_plan = (
        adapter_plan_summary
        if adapter_plan_summary is not None
        else sqlite_operational_log_adapter_plan_summary()
    )
    phase_contracts = {
        str(contract.get("phase_id", "")): contract
        for contract in expected.get("phase_contracts", [])
        if isinstance(contract, dict)
    }
    required_columns = [
        str(column) for column in expected.get("required_columns", [])
    ]
    by_phase = {
        str(phase): int(count)
        for phase, count in dict(adapter_plan.get("by_phase", {})).items()
    }
    mutation_allowed = bool(expected.get("mutation_allowed", False))
    required_phases = [str(phase) for phase in expected.get("required_phase_ids", [])]
    missing_table_phases = [
        phase for phase in required_phases if not phase_contracts.get(phase, {}).get("table_name")
    ]
    missing_column_pairs = [
        f"{phase}:{column}"
        for phase in required_phases
        for column in required_columns
        if column
        not in {
            str(value)
            for value in phase_contracts.get(phase, {}).get("required_columns", [])
        }
    ]
    count_mismatches = [
        phase
        for phase in required_phases
        if int(phase_contracts.get(phase, {}).get("planned_log_count", -1))
        != by_phase.get(phase, -1)
    ]
    records = [
        SqliteOperationalLogAdapterContractRecord(
            phase_id=phase,
            table_name=str(phase_contracts.get(phase, {}).get("table_name", "")),
            required_columns=tuple(
                str(column)
                for column in phase_contracts.get(phase, {}).get(
                    "required_columns", []
                )
            ),
            planned_log_count=int(
                phase_contracts.get(phase, {}).get("planned_log_count", 0)
            ),
            mutation_allowed=mutation_allowed,
        )
        for phase in PHASE_ORDER
        if phase in required_phases
    ]

    issues: list[str] = []
    if expected.get("require_adapter_plan_ok", True) and not bool(
        adapter_plan.get("ok", False)
    ):
        issues.append("SQLite operational log adapter plan is not ok")
    if len(required_phases) != int(expected.get("expected_phase_count", len(required_phases))):
        issues.append("adapter contract required phase count drift")
    if int(adapter_plan.get("planned_log_count", 0)) != int(
        expected.get("expected_planned_log_count", 0)
    ):
        issues.append("adapter contract planned log count drift")
    if expected.get("require_all_phase_tables", True) and missing_table_phases:
        issues.append("missing adapter table plan(s): " + ", ".join(missing_table_phases))
    if expected.get("require_required_columns", True) and missing_column_pairs:
        issues.append("missing adapter required column(s): " + ", ".join(missing_column_pairs))
    if expected.get("require_phase_log_counts", True) and count_mismatches:
        issues.append("adapter phase count mismatch(es): " + ", ".join(count_mismatches))
    if mutation_allowed:
        issues.append("adapter contract must remain non-mutating")

    return {
        "schema_version": SQLITE_OPERATIONAL_LOG_ADAPTER_CONTRACT_SCHEMA_VERSION,
        "disclaimer": SQLITE_OPERATIONAL_LOG_ADAPTER_CONTRACT_DISCLAIMER,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "expected_phase_count": int(expected.get("expected_phase_count", 0)),
        "phase_contract_count": len(phase_contracts),
        "expected_planned_log_count": int(
            expected.get("expected_planned_log_count", 0)
        ),
        "planned_log_count": int(adapter_plan.get("planned_log_count", 0)),
        "missing_table_plan_count": len(missing_table_phases),
        "missing_required_column_count": len(missing_column_pairs),
        "phase_count_mismatch_count": len(count_mismatches),
        "mutation_allowed": mutation_allowed,
        "records": [record.__dict__ for record in records],
    }
