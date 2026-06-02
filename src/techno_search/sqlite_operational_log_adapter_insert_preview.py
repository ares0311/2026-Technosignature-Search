"""Preview-only SQLite inserts for future operational log adapters."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from techno_search.sqlite_operational_log_adapter_row_preview import (
    sqlite_operational_log_adapter_row_preview_summary,
)

SQLITE_OPERATIONAL_LOG_ADAPTER_INSERT_PREVIEW_SCHEMA_VERSION = (
    "sqlite_operational_log_adapter_insert_preview_v1"
)

SQLITE_OPERATIONAL_LOG_ADAPTER_INSERT_PREVIEW_DISCLAIMER = (
    "SQLite operational log adapter insert previews are local planning "
    "artifacts only. They render deterministic parameterized INSERT statements "
    "and bound values for review without executing SQL, inserting rows, "
    "creating tables, migrating fixture records, mutating databases, ingesting "
    "real observation data, authorizing live data access, authorizing external "
    "submission, or constituting detections, discoveries, or external "
    "validation."
)


@dataclass(frozen=True)
class SqliteOperationalLogAdapterInsertPreviewRecord:
    log_id: str
    phase_id: str
    table_name: str
    insert_sql: str
    bound_values: tuple[str, ...]
    value_count: int
    execution_allowed: bool


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_preview_path() -> Path:
    return (
        _project_root()
        / "tests"
        / "fixtures"
        / "sqlite_operational_log_adapter_insert_preview.json"
    )


def load_sqlite_operational_log_adapter_insert_preview_expectations(
    path: Path | None = None,
) -> dict[str, Any]:
    preview_path = path if path is not None else _default_preview_path()
    raw = json.loads(preview_path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], raw["expected_preview"])


def _insert_sql(table_name: str, columns: list[str], placeholder: str) -> str:
    column_sql = ", ".join(columns)
    placeholder_sql = ", ".join(placeholder for _ in columns)
    return f"INSERT INTO {table_name} ({column_sql}) VALUES ({placeholder_sql});"


def sqlite_operational_log_adapter_insert_preview_summary(
    path: Path | None = None,
    *,
    row_preview_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    expected = load_sqlite_operational_log_adapter_insert_preview_expectations(path)
    row_preview = (
        row_preview_summary
        if row_preview_summary is not None
        else sqlite_operational_log_adapter_row_preview_summary()
    )
    execution_allowed = bool(expected.get("execution_allowed", False))
    required_columns = [str(column) for column in expected.get("required_columns", [])]
    placeholder = str(expected.get("parameter_placeholder", "?"))
    expected_value_count = int(
        expected.get("expected_bound_value_count", len(required_columns))
    )

    records: list[SqliteOperationalLogAdapterInsertPreviewRecord] = []
    missing_value_pairs: list[str] = []
    for row in row_preview.get("records", []):
        if not isinstance(row, dict):
            continue
        log_id = str(row.get("log_id", ""))
        values = tuple(str(row.get(column, "")) for column in required_columns)
        missing_value_pairs.extend(
            f"{log_id}:{column}"
            for column, value in zip(required_columns, values, strict=True)
            if not value
        )
        records.append(
            SqliteOperationalLogAdapterInsertPreviewRecord(
                log_id=log_id,
                phase_id=str(row.get("phase_id", "")),
                table_name=str(row.get("table_name", "")),
                insert_sql=_insert_sql(
                    str(row.get("table_name", "")),
                    required_columns,
                    placeholder,
                ),
                bound_values=values,
                value_count=len(values),
                execution_allowed=execution_allowed,
            )
        )

    insert_statements = [record.insert_sql for record in records]
    phase_ids = sorted({record.phase_id for record in records if record.phase_id})
    missing_table_log_ids = [
        record.log_id for record in records if record.log_id and not record.table_name
    ]
    value_count_mismatch_log_ids = [
        record.log_id
        for record in records
        if record.value_count != expected_value_count
    ]
    placeholder_mismatch_log_ids = [
        record.log_id
        for record in records
        if record.insert_sql.count(placeholder) != expected_value_count
    ]
    non_parameterized_log_ids = [
        record.log_id
        for record in records
        if any(
            value and value in record.insert_sql.partition("VALUES")[2]
            for value in record.bound_values
        )
    ]

    issues: list[str] = []
    if expected.get("require_row_preview_ok", True) and not bool(
        row_preview.get("ok", False)
    ):
        issues.append("SQLite operational log adapter row preview is not ok")
    if len(records) != int(expected.get("expected_insert_count", 0)):
        issues.append(
            f"insert preview count {len(records)} != expected "
            f"{int(expected.get('expected_insert_count', 0))}"
        )
    if len(phase_ids) != int(expected.get("expected_phase_count", 0)):
        issues.append(
            f"insert preview phase count {len(phase_ids)} != expected "
            f"{int(expected.get('expected_phase_count', 0))}"
        )
    if expected.get("require_table_names", True) and missing_table_log_ids:
        issues.append("missing insert table name(s): " + ", ".join(missing_table_log_ids))
    if expected.get("require_bound_values", True) and missing_value_pairs:
        issues.append("missing insert bound value(s): " + ", ".join(missing_value_pairs))
    if expected.get("require_bound_value_count", True) and value_count_mismatch_log_ids:
        issues.append(
            "insert value count mismatch(es): "
            + ", ".join(value_count_mismatch_log_ids)
        )
    if expected.get("require_parameterized_sql", True) and placeholder_mismatch_log_ids:
        issues.append(
            "insert placeholder count mismatch(es): "
            + ", ".join(placeholder_mismatch_log_ids)
        )
    if expected.get("forbid_inline_values", True) and non_parameterized_log_ids:
        issues.append(
            "insert SQL contains inline bound value(s): "
            + ", ".join(non_parameterized_log_ids)
        )
    if execution_allowed:
        issues.append("insert preview must remain non-executing")

    return {
        "schema_version": SQLITE_OPERATIONAL_LOG_ADAPTER_INSERT_PREVIEW_SCHEMA_VERSION,
        "disclaimer": SQLITE_OPERATIONAL_LOG_ADAPTER_INSERT_PREVIEW_DISCLAIMER,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "expected_insert_count": int(expected.get("expected_insert_count", 0)),
        "insert_count": len(records),
        "expected_phase_count": int(expected.get("expected_phase_count", 0)),
        "phase_count": len(phase_ids),
        "required_columns": required_columns,
        "missing_table_name_count": len(missing_table_log_ids),
        "missing_bound_value_count": len(missing_value_pairs),
        "value_count_mismatch_count": len(value_count_mismatch_log_ids),
        "placeholder_mismatch_count": len(placeholder_mismatch_log_ids),
        "non_parameterized_count": len(non_parameterized_log_ids),
        "execution_allowed": execution_allowed,
        "records": [record.__dict__ for record in records],
        "insert_statements": insert_statements,
    }
