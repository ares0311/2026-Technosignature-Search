from __future__ import annotations

import json
from pathlib import Path

from techno_search.sqlite_operational_log_adapter_ddl_preview import (
    SQLITE_OPERATIONAL_LOG_ADAPTER_DDL_PREVIEW_SCHEMA_VERSION,
    load_sqlite_operational_log_adapter_ddl_preview_expectations,
    sqlite_operational_log_adapter_ddl_preview_summary,
)

FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "sqlite_operational_log_adapter_ddl_preview.json"
)
REQUIRED_COLUMNS = [
    "log_id",
    "phase_id",
    "event_payload_json",
    "recorded_at_utc",
    "source_fixture_path",
    "sqlite_policy",
    "provenance_hash",
]


def _contract(
    *,
    ok: bool = True,
    table_name: str = "operational_log_candidate_and_review",
    columns: list[str] | None = None,
) -> dict[str, object]:
    return {
        "ok": ok,
        "records": [
            {
                "phase_id": "candidate_and_review",
                "table_name": table_name,
                "required_columns": columns if columns is not None else REQUIRED_COLUMNS,
            }
        ],
    }


def _write_preview(
    path: Path,
    *,
    expected_statement_count: int = 1,
    required_clauses: list[str] | None = None,
    execution_allowed: bool = False,
) -> Path:
    preview_path = path / "preview.json"
    preview_path.write_text(
        json.dumps(
            {
                "schema_version": SQLITE_OPERATIONAL_LOG_ADAPTER_DDL_PREVIEW_SCHEMA_VERSION,
                "expected_preview": {
                    "expected_statement_count": expected_statement_count,
                    "required_clauses": required_clauses
                    if required_clauses is not None
                    else ["CREATE TABLE IF NOT EXISTS"],
                    "require_adapter_contract_ok": True,
                    "require_required_clauses": True,
                    "execution_allowed": execution_allowed,
                },
            }
        ),
        encoding="utf-8",
    )
    return preview_path


def test_load_fixture_expectations() -> None:
    expected = load_sqlite_operational_log_adapter_ddl_preview_expectations(FIXTURE_PATH)

    assert expected["expected_statement_count"] == 0
    assert expected["execution_allowed"] is False


def test_default_project_ddl_preview_passes() -> None:
    summary = sqlite_operational_log_adapter_ddl_preview_summary()

    assert summary["schema_version"] == SQLITE_OPERATIONAL_LOG_ADAPTER_DDL_PREVIEW_SCHEMA_VERSION
    assert summary["ok"] is True
    assert summary["ddl_statement_count"] == 0
    assert summary["missing_clause_count"] == 0
    assert summary["execution_allowed"] is False
    assert summary["ddl_statements"] == []


def test_custom_contract_passes(tmp_path: Path) -> None:
    preview_path = _write_preview(tmp_path)

    summary = sqlite_operational_log_adapter_ddl_preview_summary(
        preview_path,
        adapter_contract_summary=_contract(),
    )

    assert summary["ok"] is True
    assert summary["ddl_statement_count"] == 1


def test_detects_contract_not_ok(tmp_path: Path) -> None:
    preview_path = _write_preview(tmp_path)

    summary = sqlite_operational_log_adapter_ddl_preview_summary(
        preview_path,
        adapter_contract_summary=_contract(ok=False),
    )

    assert summary["ok"] is False
    assert any("adapter contract is not ok" in issue for issue in summary["issues"])


def test_detects_statement_count_mismatch(tmp_path: Path) -> None:
    preview_path = _write_preview(tmp_path, expected_statement_count=2)

    summary = sqlite_operational_log_adapter_ddl_preview_summary(
        preview_path,
        adapter_contract_summary=_contract(),
    )

    assert summary["ok"] is False
    assert any("statement count 1 != expected 2" in issue for issue in summary["issues"])


def test_detects_missing_required_clause(tmp_path: Path) -> None:
    preview_path = _write_preview(tmp_path, required_clauses=["missing clause"])

    summary = sqlite_operational_log_adapter_ddl_preview_summary(
        preview_path,
        adapter_contract_summary=_contract(),
    )

    assert summary["ok"] is False
    assert summary["missing_clause_count"] == 1


def test_detects_execution_allowed(tmp_path: Path) -> None:
    preview_path = _write_preview(tmp_path, execution_allowed=True)

    summary = sqlite_operational_log_adapter_ddl_preview_summary(
        preview_path,
        adapter_contract_summary=_contract(),
    )

    assert summary["ok"] is False
    assert summary["execution_allowed"] is True
