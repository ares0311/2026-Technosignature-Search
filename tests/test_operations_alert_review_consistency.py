from __future__ import annotations

import json
from pathlib import Path

from techno_search.operations_alert_review_consistency import (
    load_operations_alert_review_expectations,
    operations_alert_review_consistency_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "operations_alert_review_consistency.json"


def _write_expected(
    path: Path,
    *,
    open_alert_count: int = 2,
    critical_open_alert_count: int = 1,
    resolution_open_count: int = 1,
) -> Path:
    expected_path = path / "expected.json"
    expected_path.write_text(
        json.dumps(
            {
                "schema_version": "operations_alert_review_consistency_v1",
                "expected_review": {
                    "open_alert_count": open_alert_count,
                    "critical_open_alert_count": critical_open_alert_count,
                    "alert_resolution_open_count": resolution_open_count,
                    "qc_overall_health": "blocked",
                    "operations_readiness_recommendation": "blocked_for_real_data",
                    "require_open_alert_resolution_coverage": True,
                    "require_zero_external_authorization": True,
                    "require_zero_network_access": True,
                },
            }
        ),
        encoding="utf-8",
    )
    return expected_path


def _write_alerts(path: Path, *, omit_critical_coverage: bool = False) -> tuple[Path, Path]:
    alerts_path = path / "alerts.json"
    resolutions_path = path / "resolutions.json"
    alerts_path.write_text(
        json.dumps(
            {
                "candidate_alert_entries": [
                    {
                        "alert_id": "alrt-test-001",
                        "candidate_id": "candidate-a",
                        "alert_kind": "score_threshold_crossed",
                        "severity": "warning",
                        "message": "Local operator review required.",
                        "resolved": False,
                        "alert_utc": "2026-05-26T00:00:00Z",
                        "resolved_utc": None,
                        "notes": "No external action authorized.",
                    },
                    {
                        "alert_id": "alrt-test-002",
                        "candidate_id": "candidate-b",
                        "alert_kind": "provenance_inconsistency",
                        "severity": "critical",
                        "message": "Critical local provenance review required.",
                        "resolved": False,
                        "alert_utc": "2026-05-26T00:01:00Z",
                        "resolved_utc": None,
                        "notes": "Blocks scheduling only.",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    open_resolution_ids = ["alrt-test-001"] if omit_critical_coverage else [
        "alrt-test-001",
        "alrt-test-002",
    ]
    resolutions_path.write_text(
        json.dumps(
            {
                "alert_resolution_entries": [
                    {
                        "resolution_id": "ares-test-001",
                        "candidate_id": "candidate-a",
                        "linked_alert_ids": open_resolution_ids,
                        "status": "open",
                        "resolution_kind": "operator_review",
                        "resolving_operator": "operator-alpha",
                        "resolution_utc": "2026-05-26T00:02:00Z",
                        "notes": "Operator review remains open.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return alerts_path, resolutions_path


def _qc() -> dict[str, object]:
    return {"overall_qc_health": "blocked"}


def _readiness(
    *,
    open_alert_count: int = 2,
    critical_open_alert_count: int = 1,
    network_access_allowed_count: int = 0,
    external_submission_approved_count: int = 0,
) -> dict[str, object]:
    return {
        "recommendation": "blocked_for_real_data",
        "open_alert_count": open_alert_count,
        "critical_open_alert_count": critical_open_alert_count,
        "network_access_allowed_count": network_access_allowed_count,
        "external_submission_approved_count": external_submission_approved_count,
    }


def test_load_operations_alert_review_expectations_fixture() -> None:
    expected = load_operations_alert_review_expectations(FIXTURE_PATH)

    assert expected["open_alert_count"] == 0
    assert expected["critical_open_alert_count"] == 0
    assert expected["qc_overall_health"] == "blocked"


def test_operations_alert_review_consistency_custom_project_passes(
    tmp_path: Path,
) -> None:
    expected_path = _write_expected(tmp_path)
    alerts_path, resolutions_path = _write_alerts(tmp_path)

    summary = operations_alert_review_consistency_summary(
        expected_path,
        alert_fixture_path=alerts_path,
        resolution_fixture_path=resolutions_path,
        quality_control=_qc(),
        readiness=_readiness(),
    )

    assert summary["ok"] is True
    assert summary["issue_count"] == 0
    assert summary["uncovered_open_alert_count"] == 0
    assert summary["external_submission_approved_count"] == 0
    assert summary["network_access_allowed_count"] == 0


def test_operations_alert_review_consistency_detects_open_alert_count_drift(
    tmp_path: Path,
) -> None:
    expected_path = _write_expected(tmp_path, open_alert_count=3)
    alerts_path, resolutions_path = _write_alerts(tmp_path)

    summary = operations_alert_review_consistency_summary(
        expected_path,
        alert_fixture_path=alerts_path,
        resolution_fixture_path=resolutions_path,
        quality_control=_qc(),
        readiness=_readiness(),
    )

    assert summary["ok"] is False
    assert any("open alert count 2 != expected 3" in issue for issue in summary["issues"])


def test_operations_alert_review_consistency_detects_missing_critical_coverage(
    tmp_path: Path,
) -> None:
    expected_path = _write_expected(tmp_path)
    alerts_path, resolutions_path = _write_alerts(tmp_path, omit_critical_coverage=True)

    summary = operations_alert_review_consistency_summary(
        expected_path,
        alert_fixture_path=alerts_path,
        resolution_fixture_path=resolutions_path,
        quality_control=_qc(),
        readiness=_readiness(),
    )

    assert summary["ok"] is False
    assert summary["uncovered_critical_alert_ids"] == ["alrt-test-002"]
    assert any("critical open alert IDs" in issue for issue in summary["issues"])


def test_operations_alert_review_consistency_detects_authorization_drift(
    tmp_path: Path,
) -> None:
    expected_path = _write_expected(tmp_path)
    alerts_path, resolutions_path = _write_alerts(tmp_path)

    summary = operations_alert_review_consistency_summary(
        expected_path,
        alert_fixture_path=alerts_path,
        resolution_fixture_path=resolutions_path,
        quality_control=_qc(),
        readiness=_readiness(network_access_allowed_count=1),
    )

    assert summary["ok"] is False
    assert any("network access allowed count is nonzero" in issue for issue in summary["issues"])


def test_operations_alert_review_consistency_default_project_passes() -> None:
    summary = operations_alert_review_consistency_summary()

    assert summary["schema_version"] == "operations_alert_review_consistency_v1"
    assert summary["ok"] is True
    assert summary["actual_open_alert_count"] == 0
    assert summary["actual_critical_open_alert_count"] == 0
    assert summary["actual_qc_overall_health"] == "blocked"
