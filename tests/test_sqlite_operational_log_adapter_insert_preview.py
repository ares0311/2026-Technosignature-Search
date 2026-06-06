from __future__ import annotations

import json
from pathlib import Path

from techno_search.sqlite_operational_log_adapter_insert_preview import (
    SQLITE_OPERATIONAL_LOG_ADAPTER_INSERT_PREVIEW_SCHEMA_VERSION,
    load_sqlite_operational_log_adapter_insert_preview_expectations,
    sqlite_operational_log_adapter_insert_preview_summary,
)

FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "sqlite_operational_log_adapter_insert_preview.json"
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
ROW = {
    "log_id": "candidate_alert_log",
    "phase_id": "candidate_and_review",
    "table_name": "operational_log_candidate_and_review",
    "event_payload_json": "{\"log_id\":\"candidate_alert_log\"}",
    "recorded_at_utc": "preview_only_not_recorded",
    "source_fixture_path": "tests/fixtures/candidate_alert_log.json",
    "sqlite_policy": "top_level_sqlite_required_before_production",
    "provenance_hash": "abc123",
    "execution_allowed": False,
}


def _row_preview(*, ok: bool = True, row: dict[str, object] | None = None) -> dict[str, object]:
    return {
        "ok": ok,
        "records": [row if row is not None else ROW],
    }


def _write_preview(
    path: Path,
    *,
    expected_insert_count: int = 1,
    expected_phase_count: int = 1,
    required_columns: list[str] | None = None,
    expected_bound_value_count: int = 7,
    execution_allowed: bool = False,
) -> Path:
    preview_path = path / "preview.json"
    preview_path.write_text(
        json.dumps(
            {
                "schema_version": SQLITE_OPERATIONAL_LOG_ADAPTER_INSERT_PREVIEW_SCHEMA_VERSION,
                "expected_preview": {
                    "expected_insert_count": expected_insert_count,
                    "expected_phase_count": expected_phase_count,
                    "required_columns": required_columns
                    if required_columns is not None
                    else REQUIRED_COLUMNS,
                    "expected_bound_value_count": expected_bound_value_count,
                    "parameter_placeholder": "?",
                    "require_row_preview_ok": True,
                    "require_table_names": True,
                    "require_bound_values": True,
                    "require_bound_value_count": True,
                    "require_parameterized_sql": True,
                    "forbid_inline_values": True,
                    "execution_allowed": execution_allowed,
                },
            }
        ),
        encoding="utf-8",
    )
    return preview_path


def test_load_fixture_expectations() -> None:
    expected = load_sqlite_operational_log_adapter_insert_preview_expectations(
        FIXTURE_PATH
    )

    assert expected["expected_insert_count"] == 0
    assert expected["expected_phase_count"] == 0
    assert expected["expected_bound_value_count"] == 7
    assert expected["execution_allowed"] is False
    assert "provenance_hash" in expected["required_columns"]


def test_default_project_insert_preview_passes() -> None:
    summary = sqlite_operational_log_adapter_insert_preview_summary()

    assert (
        summary["schema_version"]
        == SQLITE_OPERATIONAL_LOG_ADAPTER_INSERT_PREVIEW_SCHEMA_VERSION
    )
    assert summary["ok"] is True
    assert summary["insert_count"] == 0
    assert summary["phase_count"] == 0
    assert summary["missing_table_name_count"] == 0
    assert summary["missing_bound_value_count"] == 0
    assert summary["value_count_mismatch_count"] == 0
    assert summary["placeholder_mismatch_count"] == 0
    assert summary["non_parameterized_count"] == 0
    assert summary["execution_allowed"] is False
    assert summary["insert_statements"] == []


def test_custom_row_preview_passes(tmp_path: Path) -> None:
    preview_path = _write_preview(tmp_path)

    summary = sqlite_operational_log_adapter_insert_preview_summary(
        preview_path,
        row_preview_summary=_row_preview(),
    )

    assert summary["ok"] is True
    assert summary["insert_count"] == 1
    assert summary["records"][0]["value_count"] == 7


def test_detects_row_preview_not_ok(tmp_path: Path) -> None:
    preview_path = _write_preview(tmp_path)

    summary = sqlite_operational_log_adapter_insert_preview_summary(
        preview_path,
        row_preview_summary=_row_preview(ok=False),
    )

    assert summary["ok"] is False
    assert any("row preview is not ok" in issue for issue in summary["issues"])


def test_detects_insert_count_mismatch(tmp_path: Path) -> None:
    preview_path = _write_preview(tmp_path, expected_insert_count=2)

    summary = sqlite_operational_log_adapter_insert_preview_summary(
        preview_path,
        row_preview_summary=_row_preview(),
    )

    assert summary["ok"] is False
    assert any("insert preview count 1 != expected 2" in issue for issue in summary["issues"])


def test_detects_missing_table_name(tmp_path: Path) -> None:
    preview_path = _write_preview(tmp_path)
    row = {**ROW, "table_name": ""}

    summary = sqlite_operational_log_adapter_insert_preview_summary(
        preview_path,
        row_preview_summary=_row_preview(row=row),
    )

    assert summary["ok"] is False
    assert summary["missing_table_name_count"] == 1


def test_detects_missing_bound_value(tmp_path: Path) -> None:
    preview_path = _write_preview(tmp_path)
    row = {**ROW, "source_fixture_path": ""}

    summary = sqlite_operational_log_adapter_insert_preview_summary(
        preview_path,
        row_preview_summary=_row_preview(row=row),
    )

    assert summary["ok"] is False
    assert summary["missing_bound_value_count"] == 1


def test_detects_value_count_and_placeholder_mismatch(tmp_path: Path) -> None:
    preview_path = _write_preview(tmp_path, expected_bound_value_count=8)

    summary = sqlite_operational_log_adapter_insert_preview_summary(
        preview_path,
        row_preview_summary=_row_preview(),
    )

    assert summary["ok"] is False
    assert summary["value_count_mismatch_count"] == 1
    assert summary["placeholder_mismatch_count"] == 1


def test_detects_execution_allowed(tmp_path: Path) -> None:
    preview_path = _write_preview(tmp_path, execution_allowed=True)

    summary = sqlite_operational_log_adapter_insert_preview_summary(
        preview_path,
        row_preview_summary=_row_preview(),
    )

    assert summary["ok"] is False
    assert summary["execution_allowed"] is True
