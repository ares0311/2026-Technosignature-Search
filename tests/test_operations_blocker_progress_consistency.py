from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from techno_search.operations_blocker_progress_consistency import (
    load_operations_blocker_progress_expectations,
    operations_blocker_progress_consistency_summary,
)

FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "operations_blocker_progress_consistency.json"
)


def _write_expected(
    path: Path,
    *,
    residual_total: int = 4,
    verified_ids: list[str] | None = None,
    categories: list[str] | None = None,
) -> Path:
    expected_path = path / "expected.json"
    expected_path.write_text(
        json.dumps(
            {
                "schema_version": "operations_blocker_progress_consistency_v1",
                "expected_progress": {
                    "detail_count": 2,
                    "review_record_count": 2,
                    "followup_action_count": 2,
                    "progress_record_count": 2,
                    "unresolved_progress_count": 1,
                    "verified_local_count": 1,
                    "progress_review_record_count": 1,
                    "next_action_record_count": 1,
                    "execution_record_count": 1,
                    "execution_review_record_count": 1,
                    "execution_followup_record_count": 1,
                    "operator_followup_required_count": 1,
                    "local_note_followup_ready_count": 0,
                    "blocked_pending_real_data_count": 0,
                    "residual_blocker_total": residual_total,
                    "verified_progress_action_ids": verified_ids
                    or ["ops-action-002"],
                    "categories_covered": categories or ["alerts"],
                    "require_coverage_complete": True,
                    "require_priority_sequence_ok": True,
                    "require_zero_mismatches": True,
                    "require_zero_live_data_authorization": True,
                    "require_zero_external_authorization": True,
                },
            }
        ),
        encoding="utf-8",
    )
    return expected_path


def _summaries() -> dict[str, dict[str, object]]:
    detail = {
        "detail_count": 2,
        "network_access_allowed_count": 0,
        "external_submission_approved_count": 0,
    }
    review = {
        "record_count": 2,
        "coverage_complete": True,
        "residual_blocker_total": 4,
        "live_data_authorized_count": 0,
        "external_submission_authorized_count": 0,
    }
    followup = {
        "action_count": 2,
        "coverage_complete": True,
        "residual_blocker_total": 4,
        "live_data_authorized_count": 0,
        "external_submission_authorized_count": 0,
    }
    progress = {
        "record_count": 2,
        "unresolved_progress_count": 1,
        "verified_local_count": 1,
        "coverage_complete": True,
        "residual_blocker_total": 4,
        "live_data_authorized_count": 0,
        "external_submission_authorized_count": 0,
        "recommendation_mismatch_count": 0,
    }
    progress_review = {
        "record_count": 1,
        "coverage_complete": True,
        "residual_blocker_total": 4,
        "live_data_authorized_count": 0,
        "external_submission_authorized_count": 0,
        "status_mismatch_count": 0,
    }
    next_actions = {
        "record_count": 1,
        "coverage_complete": True,
        "residual_blocker_total": 4,
        "live_data_authorized_count": 0,
        "external_submission_authorized_count": 0,
        "status_mismatch_count": 0,
        "priority_sequence_ok": True,
    }
    execution = {
        "record_count": 1,
        "coverage_complete": True,
        "residual_blocker_total": 4,
        "live_data_authorized_count": 0,
        "external_submission_authorized_count": 0,
        "status_mismatch_count": 0,
        "residual_mismatch_count": 0,
        "priority_mismatch_count": 0,
        "priority_sequence_ok": True,
    }
    execution_review = {
        "record_count": 1,
        "coverage_complete": True,
        "residual_blocker_total": 4,
        "live_data_authorized_count": 0,
        "external_submission_authorized_count": 0,
        "status_mismatch_count": 0,
        "residual_mismatch_count": 0,
        "priority_mismatch_count": 0,
        "priority_sequence_ok": True,
    }
    execution_followup = {
        "record_count": 1,
        "coverage_complete": True,
        "residual_blocker_total": 4,
        "live_data_authorized_count": 0,
        "external_submission_authorized_count": 0,
        "status_mismatch_count": 0,
        "residual_mismatch_count": 0,
        "priority_mismatch_count": 0,
        "priority_sequence_ok": True,
        "operator_followup_required_count": 1,
        "local_note_followup_ready_count": 0,
        "blocked_pending_real_data_count": 0,
        "categories_covered": ["alerts"],
        "verified_progress_action_ids": ["ops-action-002"],
    }
    return {
        "blocker_detail": detail,
        "blocker_review": review,
        "blocker_followup": followup,
        "blocker_followup_progress": progress,
        "blocker_progress_review": progress_review,
        "blocker_progress_next_actions": next_actions,
        "blocker_progress_execution": execution,
        "blocker_progress_execution_review": execution_review,
        "blocker_progress_execution_followup": execution_followup,
    }


def _summary(expected_path: Path, summaries: dict[str, dict[str, object]]) -> dict[str, object]:
    return operations_blocker_progress_consistency_summary(
        expected_path,
        blocker_detail=summaries["blocker_detail"],
        blocker_review=summaries["blocker_review"],
        blocker_followup=summaries["blocker_followup"],
        blocker_followup_progress=summaries["blocker_followup_progress"],
        blocker_progress_review=summaries["blocker_progress_review"],
        blocker_progress_next_actions=summaries["blocker_progress_next_actions"],
        blocker_progress_execution=summaries["blocker_progress_execution"],
        blocker_progress_execution_review=summaries[
            "blocker_progress_execution_review"
        ],
        blocker_progress_execution_followup=summaries[
            "blocker_progress_execution_followup"
        ],
    )


def test_load_operations_blocker_progress_expectations_fixture() -> None:
    expected = load_operations_blocker_progress_expectations(FIXTURE_PATH)

    assert expected["detail_count"] == 7
    assert expected["execution_followup_record_count"] == 6
    assert expected["residual_blocker_total"] == 26
    assert expected["verified_progress_action_ids"] == ["ops-action-003"]


def test_operations_blocker_progress_consistency_custom_project_passes(
    tmp_path: Path,
) -> None:
    expected_path = _write_expected(tmp_path)

    summary = _summary(expected_path, _summaries())

    assert summary["ok"] is True
    assert summary["issue_count"] == 0
    assert summary["coverage_complete"] is True
    assert summary["priority_sequence_ok"] is True


def test_operations_blocker_progress_consistency_detects_count_drift(
    tmp_path: Path,
) -> None:
    expected_path = _write_expected(tmp_path)
    summaries = deepcopy(_summaries())
    summaries["blocker_progress_execution_followup"]["record_count"] = 2

    summary = _summary(expected_path, summaries)

    assert summary["ok"] is False
    assert any(
        "execution_followup_record_count 2 != expected 1" in issue
        for issue in summary["issues"]
    )


def test_operations_blocker_progress_consistency_detects_residual_drift(
    tmp_path: Path,
) -> None:
    expected_path = _write_expected(tmp_path, residual_total=5)

    summary = _summary(expected_path, _summaries())

    assert summary["ok"] is False
    assert any("residual blocker total 4 != expected 5" in issue for issue in summary["issues"])


def test_operations_blocker_progress_consistency_detects_authorization_drift(
    tmp_path: Path,
) -> None:
    expected_path = _write_expected(tmp_path)
    summaries = deepcopy(_summaries())
    summaries["blocker_progress_execution"]["live_data_authorized_count"] = 1

    summary = _summary(expected_path, summaries)

    assert summary["ok"] is False
    assert any("live data authorization count is nonzero" in issue for issue in summary["issues"])


def test_operations_blocker_progress_consistency_detects_mismatch_drift(
    tmp_path: Path,
) -> None:
    expected_path = _write_expected(tmp_path)
    summaries = deepcopy(_summaries())
    summaries["blocker_progress_execution_review"]["status_mismatch_count"] = 1

    summary = _summary(expected_path, summaries)

    assert summary["ok"] is False
    assert summary["mismatch_total"] == 1


def test_operations_blocker_progress_consistency_detects_coverage_drift(
    tmp_path: Path,
) -> None:
    expected_path = _write_expected(tmp_path)
    summaries = deepcopy(_summaries())
    summaries["blocker_progress_next_actions"]["coverage_complete"] = False

    summary = _summary(expected_path, summaries)

    assert summary["ok"] is False
    assert any("coverage is incomplete" in issue for issue in summary["issues"])


def test_operations_blocker_progress_consistency_detects_category_drift(
    tmp_path: Path,
) -> None:
    expected_path = _write_expected(tmp_path, categories=["capacity"])

    summary = _summary(expected_path, _summaries())

    assert summary["ok"] is False
    assert any("categories covered" in issue for issue in summary["issues"])


def test_operations_blocker_progress_consistency_default_project_passes() -> None:
    summary = operations_blocker_progress_consistency_summary()

    assert summary["schema_version"] == "operations_blocker_progress_consistency_v1"
    assert summary["ok"] is True
    assert summary["actual_counts"]["detail_count"] == 7
    assert summary["actual_counts"]["execution_followup_record_count"] == 6
    assert summary["actual_residual_blocker_totals"]["execution_followup"] == 26
    assert summary["actual_verified_progress_action_ids"] == ["ops-action-003"]
