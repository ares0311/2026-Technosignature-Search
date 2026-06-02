"""Preview-only SQLite execution plan for future operational log adapters."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from techno_search.sqlite_operational_log_adapter_insert_preview import (
    sqlite_operational_log_adapter_insert_preview_summary,
)

SQLITE_OPERATIONAL_LOG_ADAPTER_EXECUTION_PREVIEW_SCHEMA_VERSION = (
    "sqlite_operational_log_adapter_execution_preview_v1"
)

SQLITE_OPERATIONAL_LOG_ADAPTER_EXECUTION_PREVIEW_DISCLAIMER = (
    "SQLite operational log adapter execution previews are local planning "
    "artifacts only. They render deterministic transaction ordering for "
    "review without opening databases, executing SQL, inserting rows, "
    "creating tables, migrating fixture records, mutating databases, ingesting "
    "real observation data, authorizing live data access, authorizing external "
    "submission, or constituting detections, discoveries, or external "
    "validation."
)


@dataclass(frozen=True)
class SqliteOperationalLogAdapterExecutionPhasePreview:
    phase_id: str
    table_name: str
    begin_statement: str
    insert_count: int
    commit_statement: str
    operation_count: int
    execution_allowed: bool
    mutation_allowed: bool


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_preview_path() -> Path:
    return (
        _project_root()
        / "tests"
        / "fixtures"
        / "sqlite_operational_log_adapter_execution_preview.json"
    )


def load_sqlite_operational_log_adapter_execution_preview_expectations(
    path: Path | None = None,
) -> dict[str, Any]:
    preview_path = path if path is not None else _default_preview_path()
    raw = json.loads(preview_path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], raw["expected_preview"])


def sqlite_operational_log_adapter_execution_preview_summary(
    path: Path | None = None,
    *,
    insert_preview_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    expected = load_sqlite_operational_log_adapter_execution_preview_expectations(path)
    insert_preview = (
        insert_preview_summary
        if insert_preview_summary is not None
        else sqlite_operational_log_adapter_insert_preview_summary()
    )
    begin_statement = str(expected.get("begin_statement", "BEGIN IMMEDIATE;"))
    commit_statement = str(expected.get("commit_statement", "COMMIT;"))
    execution_allowed = bool(expected.get("execution_allowed", False))
    mutation_allowed = bool(expected.get("mutation_allowed", False))

    records = [
        record
        for record in insert_preview.get("records", [])
        if isinstance(record, dict)
    ]
    phase_order = []
    for record in records:
        phase_id = str(record.get("phase_id", ""))
        if phase_id and phase_id not in phase_order:
            phase_order.append(phase_id)

    phase_previews: list[SqliteOperationalLogAdapterExecutionPhasePreview] = []
    missing_transaction_phase_ids: list[str] = []
    for phase_id in phase_order:
        phase_records = [
            record for record in records if str(record.get("phase_id", "")) == phase_id
        ]
        table_names = sorted(
            {str(record.get("table_name", "")) for record in phase_records}
        )
        table_name = table_names[0] if len(table_names) == 1 else ""
        if not begin_statement or not commit_statement:
            missing_transaction_phase_ids.append(phase_id)
        phase_previews.append(
            SqliteOperationalLogAdapterExecutionPhasePreview(
                phase_id=phase_id,
                table_name=table_name,
                begin_statement=begin_statement,
                insert_count=len(phase_records),
                commit_statement=commit_statement,
                operation_count=len(phase_records) + 2,
                execution_allowed=execution_allowed,
                mutation_allowed=mutation_allowed,
            )
        )

    operation_count = sum(phase.operation_count for phase in phase_previews)
    phase_without_insert_ids = [
        phase.phase_id for phase in phase_previews if phase.insert_count == 0
    ]
    missing_table_phase_ids = [
        phase.phase_id for phase in phase_previews if not phase.table_name
    ]
    issues: list[str] = []
    if expected.get("require_insert_preview_ok", True) and not bool(
        insert_preview.get("ok", False)
    ):
        issues.append("SQLite operational log adapter insert preview is not ok")
    if len(records) != int(expected.get("expected_insert_count", 0)):
        issues.append(
            f"execution preview insert count {len(records)} != expected "
            f"{int(expected.get('expected_insert_count', 0))}"
        )
    if len(phase_previews) != int(expected.get("expected_phase_count", 0)):
        issues.append(
            f"execution preview phase count {len(phase_previews)} != expected "
            f"{int(expected.get('expected_phase_count', 0))}"
        )
    if operation_count != int(expected.get("expected_operation_count", 0)):
        issues.append(
            f"execution preview operation count {operation_count} != expected "
            f"{int(expected.get('expected_operation_count', 0))}"
        )
    if expected.get("require_transaction_markers", True) and missing_transaction_phase_ids:
        issues.append(
            "missing transaction marker(s): "
            + ", ".join(missing_transaction_phase_ids)
        )
    if expected.get("require_phase_tables", True) and missing_table_phase_ids:
        issues.append(
            "missing or ambiguous phase table(s): " + ", ".join(missing_table_phase_ids)
        )
    if expected.get("require_phase_inserts", True) and phase_without_insert_ids:
        issues.append("phase without insert(s): " + ", ".join(phase_without_insert_ids))
    if execution_allowed:
        issues.append("execution preview must remain non-executing")
    if mutation_allowed:
        issues.append("execution preview must not authorize mutation")

    return {
        "schema_version": SQLITE_OPERATIONAL_LOG_ADAPTER_EXECUTION_PREVIEW_SCHEMA_VERSION,
        "disclaimer": SQLITE_OPERATIONAL_LOG_ADAPTER_EXECUTION_PREVIEW_DISCLAIMER,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "expected_insert_count": int(expected.get("expected_insert_count", 0)),
        "insert_count": len(records),
        "expected_phase_count": int(expected.get("expected_phase_count", 0)),
        "phase_count": len(phase_previews),
        "expected_operation_count": int(expected.get("expected_operation_count", 0)),
        "operation_count": operation_count,
        "begin_statement": begin_statement,
        "commit_statement": commit_statement,
        "missing_transaction_marker_count": len(missing_transaction_phase_ids),
        "phase_without_insert_count": len(phase_without_insert_ids),
        "missing_phase_table_count": len(missing_table_phase_ids),
        "execution_allowed": execution_allowed,
        "mutation_allowed": mutation_allowed,
        "phase_previews": [phase.__dict__ for phase in phase_previews],
    }
