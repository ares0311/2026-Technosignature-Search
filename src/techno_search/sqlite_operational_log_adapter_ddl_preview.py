"""Preview-only SQLite DDL for future operational log adapters."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from techno_search.sqlite_operational_log_adapter_contract import (
    sqlite_operational_log_adapter_contract_summary,
)

SQLITE_OPERATIONAL_LOG_ADAPTER_DDL_PREVIEW_SCHEMA_VERSION = (
    "sqlite_operational_log_adapter_ddl_preview_v1"
)

SQLITE_OPERATIONAL_LOG_ADAPTER_DDL_PREVIEW_DISCLAIMER = (
    "SQLite operational log adapter DDL previews are local planning artifacts "
    "only. They render deterministic SQL text for review without executing SQL, "
    "creating tables, migrating fixture records, mutating databases, ingesting "
    "real observation data, authorizing live data access, authorizing external "
    "submission, or constituting detections, discoveries, or external validation."
)


@dataclass(frozen=True)
class SqliteOperationalLogAdapterDdlPreviewRecord:
    phase_id: str
    table_name: str
    ddl_sql: str
    statement_count: int
    execution_allowed: bool


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_preview_path() -> Path:
    return (
        _project_root()
        / "tests"
        / "fixtures"
        / "sqlite_operational_log_adapter_ddl_preview.json"
    )


def load_sqlite_operational_log_adapter_ddl_preview_expectations(
    path: Path | None = None,
) -> dict[str, Any]:
    preview_path = path if path is not None else _default_preview_path()
    raw = json.loads(preview_path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], raw["expected_preview"])


def _ddl_for_table(table_name: str, columns: list[str]) -> str:
    column_lines = ",\n  ".join(f"{column} TEXT NOT NULL" for column in columns)
    return f"CREATE TABLE IF NOT EXISTS {table_name} (\n  {column_lines}\n);"


def sqlite_operational_log_adapter_ddl_preview_summary(
    path: Path | None = None,
    *,
    adapter_contract_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    expected = load_sqlite_operational_log_adapter_ddl_preview_expectations(path)
    contract = (
        adapter_contract_summary
        if adapter_contract_summary is not None
        else sqlite_operational_log_adapter_contract_summary()
    )
    execution_allowed = bool(expected.get("execution_allowed", False))
    expected_statement_count = int(expected.get("expected_statement_count", 0))
    required_clauses = [str(clause) for clause in expected.get("required_clauses", [])]
    records: list[SqliteOperationalLogAdapterDdlPreviewRecord] = []
    for record in contract.get("records", []):
        if not isinstance(record, dict):
            continue
        table_name = str(record.get("table_name", ""))
        columns = [str(column) for column in record.get("required_columns", [])]
        records.append(
            SqliteOperationalLogAdapterDdlPreviewRecord(
                phase_id=str(record.get("phase_id", "")),
                table_name=table_name,
                ddl_sql=_ddl_for_table(table_name, columns),
                statement_count=1,
                execution_allowed=execution_allowed,
            )
        )

    ddl_statements = [record.ddl_sql for record in records]
    missing_clause_pairs = [
        f"{record.table_name}:{clause}"
        for record in records
        for clause in required_clauses
        if clause not in record.ddl_sql
    ]
    issues: list[str] = []
    if expected.get("require_adapter_contract_ok", True) and not bool(
        contract.get("ok", False)
    ):
        issues.append("SQLite operational log adapter contract is not ok")
    if len(ddl_statements) != expected_statement_count:
        issues.append(
            f"DDL statement count {len(ddl_statements)} != expected "
            f"{expected_statement_count}"
        )
    if expected.get("require_required_clauses", True) and missing_clause_pairs:
        issues.append("missing DDL required clause(s): " + ", ".join(missing_clause_pairs))
    if execution_allowed:
        issues.append("DDL preview must remain non-executing")

    return {
        "schema_version": SQLITE_OPERATIONAL_LOG_ADAPTER_DDL_PREVIEW_SCHEMA_VERSION,
        "disclaimer": SQLITE_OPERATIONAL_LOG_ADAPTER_DDL_PREVIEW_DISCLAIMER,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "expected_statement_count": expected_statement_count,
        "ddl_statement_count": len(ddl_statements),
        "missing_clause_count": len(missing_clause_pairs),
        "execution_allowed": execution_allowed,
        "records": [record.__dict__ for record in records],
        "ddl_statements": ddl_statements,
    }
