from __future__ import annotations

import json
from pathlib import Path

from techno_search.sqlite_operational_log_adapter_execution_preview import (
    SQLITE_OPERATIONAL_LOG_ADAPTER_EXECUTION_PREVIEW_SCHEMA_VERSION,
    load_sqlite_operational_log_adapter_execution_preview_expectations,
    sqlite_operational_log_adapter_execution_preview_summary,
)

FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "sqlite_operational_log_adapter_execution_preview.json"
)
RECORD = {
    "log_id": "candidate_alert_log",
    "phase_id": "candidate_and_review",
    "table_name": "operational_log_candidate_and_review",
    "insert_sql": "INSERT INTO operational_log_candidate_and_review "
    "(log_id) VALUES (?);",
    "bound_values": ("candidate_alert_log",),
    "value_count": 1,
    "execution_allowed": False,
}


def _insert_preview(
    *,
    ok: bool = True,
    records: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    preview_records = records if records is not None else [RECORD]
    return {
        "ok": ok,
        "insert_count": len(preview_records),
        "phase_count": len(
            {str(record.get("phase_id", "")) for record in preview_records}
        ),
        "records": preview_records,
    }


def _write_preview(
    path: Path,
    *,
    expected_insert_count: int = 1,
    expected_phase_count: int = 1,
    expected_operation_count: int = 3,
    begin_statement: str = "BEGIN IMMEDIATE;",
    commit_statement: str = "COMMIT;",
    execution_allowed: bool = False,
    mutation_allowed: bool = False,
) -> Path:
    preview_path = path / "preview.json"
    preview_path.write_text(
        json.dumps(
            {
                "schema_version": (
                    SQLITE_OPERATIONAL_LOG_ADAPTER_EXECUTION_PREVIEW_SCHEMA_VERSION
                ),
                "expected_preview": {
                    "expected_insert_count": expected_insert_count,
                    "expected_phase_count": expected_phase_count,
                    "expected_operation_count": expected_operation_count,
                    "begin_statement": begin_statement,
                    "commit_statement": commit_statement,
                    "require_insert_preview_ok": True,
                    "require_transaction_markers": True,
                    "require_phase_tables": True,
                    "require_phase_inserts": True,
                    "execution_allowed": execution_allowed,
                    "mutation_allowed": mutation_allowed,
                },
            }
        ),
        encoding="utf-8",
    )
    return preview_path


def test_load_fixture_expectations() -> None:
    expected = load_sqlite_operational_log_adapter_execution_preview_expectations(
        FIXTURE_PATH
    )

    assert expected["expected_insert_count"] == 74
    assert expected["expected_phase_count"] == 5
    assert expected["expected_operation_count"] == 84
    assert expected["execution_allowed"] is False
    assert expected["mutation_allowed"] is False


def test_default_project_execution_preview_passes() -> None:
    summary = sqlite_operational_log_adapter_execution_preview_summary()

    assert (
        summary["schema_version"]
        == SQLITE_OPERATIONAL_LOG_ADAPTER_EXECUTION_PREVIEW_SCHEMA_VERSION
    )
    assert summary["ok"] is True
    assert summary["insert_count"] == 74
    assert summary["phase_count"] == 5
    assert summary["operation_count"] == 84
    assert summary["missing_transaction_marker_count"] == 0
    assert summary["missing_phase_table_count"] == 0
    assert summary["phase_without_insert_count"] == 0
    assert summary["execution_allowed"] is False
    assert summary["mutation_allowed"] is False


def test_custom_insert_preview_passes(tmp_path: Path) -> None:
    preview_path = _write_preview(tmp_path)

    summary = sqlite_operational_log_adapter_execution_preview_summary(
        preview_path,
        insert_preview_summary=_insert_preview(),
    )

    assert summary["ok"] is True
    assert summary["phase_previews"][0]["insert_count"] == 1
    assert summary["phase_previews"][0]["begin_statement"] == "BEGIN IMMEDIATE;"


def test_detects_insert_preview_not_ok(tmp_path: Path) -> None:
    preview_path = _write_preview(tmp_path)

    summary = sqlite_operational_log_adapter_execution_preview_summary(
        preview_path,
        insert_preview_summary=_insert_preview(ok=False),
    )

    assert summary["ok"] is False
    assert any("insert preview is not ok" in issue for issue in summary["issues"])


def test_detects_count_mismatches(tmp_path: Path) -> None:
    preview_path = _write_preview(
        tmp_path,
        expected_insert_count=2,
        expected_phase_count=2,
        expected_operation_count=4,
    )

    summary = sqlite_operational_log_adapter_execution_preview_summary(
        preview_path,
        insert_preview_summary=_insert_preview(),
    )

    assert summary["ok"] is False
    assert summary["insert_count"] == 1
    assert summary["phase_count"] == 1
    assert summary["operation_count"] == 3


def test_detects_missing_transaction_marker(tmp_path: Path) -> None:
    preview_path = _write_preview(tmp_path, begin_statement="")

    summary = sqlite_operational_log_adapter_execution_preview_summary(
        preview_path,
        insert_preview_summary=_insert_preview(),
    )

    assert summary["ok"] is False
    assert summary["missing_transaction_marker_count"] == 1


def test_detects_ambiguous_phase_table(tmp_path: Path) -> None:
    preview_path = _write_preview(
        tmp_path,
        expected_insert_count=2,
        expected_operation_count=4,
    )
    records = [
        RECORD,
        {
            **RECORD,
            "log_id": "candidate_annotation_log",
            "table_name": "operational_log_other_table",
        },
    ]

    summary = sqlite_operational_log_adapter_execution_preview_summary(
        preview_path,
        insert_preview_summary=_insert_preview(records=records),
    )

    assert summary["ok"] is False
    assert summary["missing_phase_table_count"] == 1


def test_detects_execution_allowed(tmp_path: Path) -> None:
    preview_path = _write_preview(tmp_path, execution_allowed=True)

    summary = sqlite_operational_log_adapter_execution_preview_summary(
        preview_path,
        insert_preview_summary=_insert_preview(),
    )

    assert summary["ok"] is False
    assert summary["execution_allowed"] is True


def test_detects_mutation_allowed(tmp_path: Path) -> None:
    preview_path = _write_preview(tmp_path, mutation_allowed=True)

    summary = sqlite_operational_log_adapter_execution_preview_summary(
        preview_path,
        insert_preview_summary=_insert_preview(),
    )

    assert summary["ok"] is False
    assert summary["mutation_allowed"] is True
