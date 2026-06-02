from __future__ import annotations

import json
from pathlib import Path

from techno_search.sqlite_operational_log_adapter_row_preview import (
    SQLITE_OPERATIONAL_LOG_ADAPTER_ROW_PREVIEW_SCHEMA_VERSION,
    load_sqlite_operational_log_adapter_row_preview_expectations,
    sqlite_operational_log_adapter_row_preview_summary,
)

FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "sqlite_operational_log_adapter_row_preview.json"
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


def _contract(*, ok: bool = True, columns: list[str] | None = None) -> dict[str, object]:
    return {
        "ok": ok,
        "records": [
            {
                "phase_id": "candidate_and_review",
                "table_name": "operational_log_candidate_and_review",
                "required_columns": columns if columns is not None else REQUIRED_COLUMNS,
            }
        ],
    }


def _plan(
    *,
    ok: bool = True,
    phase_id: str = "candidate_and_review",
    log_id: str = "candidate_alert_log",
) -> dict[str, object]:
    return {
        "ok": ok,
        "records": [
            {
                "log_id": log_id,
                "phase_id": phase_id,
                "sqlite_policy": "top_level_sqlite_required_before_production",
            }
        ],
    }


def _registry(
    *,
    ok: bool = True,
    log_id: str = "candidate_alert_log",
    fixture_path: str = "tests/fixtures/candidate_alert_log.json",
) -> dict[str, object]:
    return {
        "ok": ok,
        "records": [
            {
                "log_id": log_id,
                "fixture_path": fixture_path,
                "sqlite_policy": "top_level_sqlite_required_before_production",
                "sqlite_backed": False,
            }
        ],
    }


def _write_preview(
    path: Path,
    *,
    expected_row_count: int = 1,
    expected_phase_count: int = 1,
    required_row_fields: list[str] | None = None,
    execution_allowed: bool = False,
) -> Path:
    preview_path = path / "preview.json"
    preview_path.write_text(
        json.dumps(
            {
                "schema_version": SQLITE_OPERATIONAL_LOG_ADAPTER_ROW_PREVIEW_SCHEMA_VERSION,
                "expected_preview": {
                    "expected_row_count": expected_row_count,
                    "expected_phase_count": expected_phase_count,
                    "required_row_fields": required_row_fields
                    if required_row_fields is not None
                    else REQUIRED_COLUMNS,
                    "require_adapter_contract_ok": True,
                    "require_adapter_plan_ok": True,
                    "require_registry_ok": True,
                    "require_contract_columns": True,
                    "require_row_fields": True,
                    "require_json_payloads": True,
                    "execution_allowed": execution_allowed,
                },
            }
        ),
        encoding="utf-8",
    )
    return preview_path


def test_load_fixture_expectations() -> None:
    expected = load_sqlite_operational_log_adapter_row_preview_expectations(FIXTURE_PATH)

    assert expected["expected_row_count"] == 74
    assert expected["expected_phase_count"] == 5
    assert expected["execution_allowed"] is False
    assert "provenance_hash" in expected["required_row_fields"]


def test_default_project_row_preview_passes() -> None:
    summary = sqlite_operational_log_adapter_row_preview_summary()

    assert summary["schema_version"] == SQLITE_OPERATIONAL_LOG_ADAPTER_ROW_PREVIEW_SCHEMA_VERSION
    assert summary["ok"] is True
    assert summary["row_count"] == 74
    assert summary["phase_count"] == 5
    assert summary["missing_row_field_count"] == 0
    assert summary["invalid_payload_count"] == 0
    assert summary["execution_allowed"] is False
    assert json.loads(summary["records"][0]["event_payload_json"])["log_id"]


def test_custom_summaries_pass(tmp_path: Path) -> None:
    preview_path = _write_preview(tmp_path)

    summary = sqlite_operational_log_adapter_row_preview_summary(
        preview_path,
        adapter_contract_summary=_contract(),
        adapter_plan_summary=_plan(),
        registry_summary=_registry(),
    )

    assert summary["ok"] is True
    assert summary["row_count"] == 1
    assert summary["phase_count"] == 1


def test_detects_contract_not_ok(tmp_path: Path) -> None:
    preview_path = _write_preview(tmp_path)

    summary = sqlite_operational_log_adapter_row_preview_summary(
        preview_path,
        adapter_contract_summary=_contract(ok=False),
        adapter_plan_summary=_plan(),
        registry_summary=_registry(),
    )

    assert summary["ok"] is False
    assert any("adapter contract is not ok" in issue for issue in summary["issues"])


def test_detects_plan_not_ok(tmp_path: Path) -> None:
    preview_path = _write_preview(tmp_path)

    summary = sqlite_operational_log_adapter_row_preview_summary(
        preview_path,
        adapter_contract_summary=_contract(),
        adapter_plan_summary=_plan(ok=False),
        registry_summary=_registry(),
    )

    assert summary["ok"] is False
    assert any("adapter plan is not ok" in issue for issue in summary["issues"])


def test_detects_row_count_mismatch(tmp_path: Path) -> None:
    preview_path = _write_preview(tmp_path, expected_row_count=2)

    summary = sqlite_operational_log_adapter_row_preview_summary(
        preview_path,
        adapter_contract_summary=_contract(),
        adapter_plan_summary=_plan(),
        registry_summary=_registry(),
    )

    assert summary["ok"] is False
    assert any("row preview count 1 != expected 2" in issue for issue in summary["issues"])


def test_detects_missing_contract_column(tmp_path: Path) -> None:
    preview_path = _write_preview(tmp_path)

    summary = sqlite_operational_log_adapter_row_preview_summary(
        preview_path,
        adapter_contract_summary=_contract(columns=REQUIRED_COLUMNS[:-1]),
        adapter_plan_summary=_plan(),
        registry_summary=_registry(),
    )

    assert summary["ok"] is False
    assert summary["missing_contract_column_count"] == 1


def test_detects_missing_row_field(tmp_path: Path) -> None:
    preview_path = _write_preview(tmp_path)

    summary = sqlite_operational_log_adapter_row_preview_summary(
        preview_path,
        adapter_contract_summary=_contract(),
        adapter_plan_summary=_plan(),
        registry_summary=_registry(fixture_path=""),
    )

    assert summary["ok"] is False
    assert summary["missing_row_field_count"] == 1


def test_detects_missing_table_mapping(tmp_path: Path) -> None:
    preview_path = _write_preview(tmp_path)

    summary = sqlite_operational_log_adapter_row_preview_summary(
        preview_path,
        adapter_contract_summary=_contract(),
        adapter_plan_summary=_plan(phase_id="unknown_phase"),
        registry_summary=_registry(),
    )

    assert summary["ok"] is False
    assert summary["missing_table_mapping_count"] == 1


def test_detects_execution_allowed(tmp_path: Path) -> None:
    preview_path = _write_preview(tmp_path, execution_allowed=True)

    summary = sqlite_operational_log_adapter_row_preview_summary(
        preview_path,
        adapter_contract_summary=_contract(),
        adapter_plan_summary=_plan(),
        registry_summary=_registry(),
    )

    assert summary["ok"] is False
    assert summary["execution_allowed"] is True
