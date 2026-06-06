from __future__ import annotations

import json
from pathlib import Path

from techno_search.operations_action_resolution_consistency import (
    load_operations_action_resolution_expectations,
    operations_action_resolution_consistency_summary,
)

FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "operations_action_resolution_consistency.json"
)


def _write_expected(
    path: Path,
    *,
    action_count: int = 2,
    record_count: int = 3,
    stale_count: int = 1,
    stale_ids: list[str] | None = None,
    residual_total: int = 4,
) -> Path:
    expected_path = path / "expected.json"
    expected_path.write_text(
        json.dumps(
            {
                "schema_version": "operations_action_resolution_consistency_v1",
                "expected_resolution": {
                    "expected_action_count": action_count,
                    "record_count": record_count,
                    "stale_resolution_count": stale_count,
                    "stale_resolution_action_ids": stale_ids or ["ops-action-003"],
                    "residual_blocker_total": residual_total,
                    "require_coverage_complete": True,
                    "require_zero_live_data_authorization": True,
                    "require_zero_external_authorization": True,
                },
            }
        ),
        encoding="utf-8",
    )
    return expected_path


def _write_resolutions(
    path: Path,
    *,
    live_authorized: bool = False,
    external_authorized: bool = False,
    omit_current_action: bool = False,
) -> Path:
    resolution_path = path / "resolutions.json"
    records = [
        {
            "resolution_id": "ops-resolution-test-001",
            "action_id": "ops-action-001",
            "category": "quality_control",
            "resolution_status": "acknowledged",
            "operator_id": "operator-alpha",
            "resolution_utc": "2026-05-26T00:00:00Z",
            "evidence_note": "Local current action acknowledged.",
            "residual_blocker_count": 1,
            "live_data_authorized": live_authorized,
            "external_submission_authorized": False,
            "notes": "Local workflow only.",
        },
        {
            "resolution_id": "ops-resolution-test-002",
            "action_id": "ops-action-002",
            "category": "alerts",
            "resolution_status": "open",
            "operator_id": "operator-beta",
            "resolution_utc": "2026-05-26T00:01:00Z",
            "evidence_note": "Local current action remains open.",
            "residual_blocker_count": 2,
            "live_data_authorized": False,
            "external_submission_authorized": external_authorized,
            "notes": "No external action authorized.",
        },
        {
            "resolution_id": "ops-resolution-test-003",
            "action_id": "ops-action-003",
            "category": "sqlite_logs",
            "resolution_status": "open",
            "operator_id": "operator-gamma",
            "resolution_utc": "2026-05-26T00:02:00Z",
            "evidence_note": "Stale local action remains visible.",
            "residual_blocker_count": 1,
            "live_data_authorized": False,
            "external_submission_authorized": False,
            "notes": "Staleness visibility only.",
        },
    ]
    if omit_current_action:
        records = [records[0], records[2]]
    resolution_path.write_text(
        json.dumps(
            {
                "schema_version": "operations_action_resolution_v1",
                "operations_action_resolution_records": records,
            }
        ),
        encoding="utf-8",
    )
    return resolution_path


def _action_plan() -> dict[str, object]:
    return {
        "actions": [
            {"action_id": "ops-action-001"},
            {"action_id": "ops-action-002"},
        ]
    }


def test_load_operations_action_resolution_expectations_fixture() -> None:
    expected = load_operations_action_resolution_expectations(FIXTURE_PATH)

    assert expected["expected_action_count"] == 7
    assert expected["stale_resolution_count"] == 3
    assert expected["stale_resolution_action_ids"] == [
        "ops-action-008",
        "ops-action-009",
        "ops-action-010",
    ]


def test_operations_action_resolution_consistency_custom_project_passes(
    tmp_path: Path,
) -> None:
    expected_path = _write_expected(tmp_path)
    resolution_path = _write_resolutions(tmp_path)

    summary = operations_action_resolution_consistency_summary(
        expected_path,
        resolution_fixture_path=resolution_path,
        action_plan=_action_plan(),
    )

    assert summary["ok"] is True
    assert summary["issue_count"] == 0
    assert summary["actual_stale_resolution_action_ids"] == ["ops-action-003"]
    assert summary["coverage_complete"] is True


def test_operations_action_resolution_consistency_detects_stale_id_drift(
    tmp_path: Path,
) -> None:
    expected_path = _write_expected(tmp_path, stale_ids=["ops-action-999"])
    resolution_path = _write_resolutions(tmp_path)

    summary = operations_action_resolution_consistency_summary(
        expected_path,
        resolution_fixture_path=resolution_path,
        action_plan=_action_plan(),
    )

    assert summary["ok"] is False
    assert any("stale resolution action IDs" in issue for issue in summary["issues"])


def test_operations_action_resolution_consistency_detects_authorization_drift(
    tmp_path: Path,
) -> None:
    expected_path = _write_expected(tmp_path)
    resolution_path = _write_resolutions(tmp_path, external_authorized=True)

    summary = operations_action_resolution_consistency_summary(
        expected_path,
        resolution_fixture_path=resolution_path,
        action_plan=_action_plan(),
    )

    assert summary["ok"] is False
    assert any(
        "external submission authorization count is nonzero" in issue
        for issue in summary["issues"]
    )


def test_operations_action_resolution_consistency_detects_missing_current_action(
    tmp_path: Path,
) -> None:
    expected_path = _write_expected(
        tmp_path,
        record_count=2,
        stale_count=1,
        residual_total=2,
    )
    resolution_path = _write_resolutions(tmp_path, omit_current_action=True)

    summary = operations_action_resolution_consistency_summary(
        expected_path,
        resolution_fixture_path=resolution_path,
        action_plan=_action_plan(),
    )

    assert summary["ok"] is False
    assert summary["coverage_complete"] is False
    assert summary["missing_action_ids"] == ["ops-action-002"]


def test_operations_action_resolution_consistency_default_project_passes() -> None:
    summary = operations_action_resolution_consistency_summary()

    assert summary["schema_version"] == "operations_action_resolution_consistency_v1"
    assert summary["ok"] is True
    assert summary["actual_action_count"] == 7
    assert summary["actual_stale_resolution_count"] == 3
    assert summary["actual_stale_resolution_action_ids"] == [
        "ops-action-008",
        "ops-action-009",
        "ops-action-010",
    ]
