"""Tests for second-pass operations blocker progress reviews."""

from __future__ import annotations

import json
import subprocess
import sys

from techno_search.log_store import init_sqlite_log_db
from techno_search.operations_blocker_detail import operations_blocker_detail_summary
from techno_search.operations_blocker_followup import operations_blocker_followup_summary
from techno_search.operations_blocker_followup_progress import (
    operations_blocker_followup_progress_summary,
)
from techno_search.operations_blocker_progress_review import (
    ALLOWED_BLOCKER_PROGRESS_REVIEW_STATUSES,
    OPERATIONS_BLOCKER_PROGRESS_REVIEW_DISCLAIMER,
    OPERATIONS_BLOCKER_PROGRESS_REVIEW_SCHEMA_VERSION,
    load_operations_blocker_progress_review_records,
    operations_blocker_progress_review_summary,
)
from techno_search.operations_blocker_review import operations_blocker_review_summary


def _progress_summary(tmp_path):
    db_path = tmp_path / "ops.sqlite3"
    init_sqlite_log_db(db_path)
    detail = operations_blocker_detail_summary(sqlite_log_path=db_path)
    review = operations_blocker_review_summary(blocker_detail_summary=detail)
    followup = operations_blocker_followup_summary(
        blocker_detail_summary_data=detail,
        blocker_review_summary_data=review,
    )
    return operations_blocker_followup_progress_summary(
        expected_action_ids=[
            str(action["action_id"])
            for action in followup["actions"]
            if isinstance(action, dict)
        ],
        blocker_followup_summary=followup,
    )


def test_load_progress_review_records_covers_unresolved_actions() -> None:
    records = load_operations_blocker_progress_review_records()
    assert len(records) == 7
    assert {record.action_id for record in records} == {
        "ops-action-001",
        "ops-action-002",
        "ops-action-003",
        "ops-action-005",
        "ops-action-006",
        "ops-action-007",
        "ops-action-008",
    }
    assert "ops-action-004" not in {record.action_id for record in records}


def test_progress_review_schema_version_and_disclaimer(tmp_path) -> None:
    progress = _progress_summary(tmp_path)
    result = operations_blocker_progress_review_summary(
        blocker_followup_progress_summary=progress
    )
    assert result["schema_version"] == OPERATIONS_BLOCKER_PROGRESS_REVIEW_SCHEMA_VERSION
    assert result["disclaimer"] == OPERATIONS_BLOCKER_PROGRESS_REVIEW_DISCLAIMER
    assert "does not clear blockers" in result["disclaimer"]


def test_progress_review_statuses_are_allowed() -> None:
    records = load_operations_blocker_progress_review_records()
    for record in records:
        assert record.review_status in ALLOWED_BLOCKER_PROGRESS_REVIEW_STATUSES


def test_progress_review_covers_unresolved_progress_only(tmp_path) -> None:
    progress = _progress_summary(tmp_path)
    result = operations_blocker_progress_review_summary(
        blocker_followup_progress_summary=progress
    )
    assert result["record_count"] == progress["unresolved_progress_count"]
    assert result["expected_action_count"] == 7
    assert result["covered_action_count"] == 7
    assert result["missing_action_count"] == 0
    assert result["stale_review_count"] == 0
    assert result["coverage_fraction"] == 1.0
    assert result["coverage_complete"] is True
    assert result["verified_progress_action_ids"] == ["ops-action-004"]


def test_progress_review_counts_statuses_and_blockers(tmp_path) -> None:
    progress = _progress_summary(tmp_path)
    result = operations_blocker_progress_review_summary(
        blocker_followup_progress_summary=progress
    )
    assert result["needs_operator_action_count"] == 1
    assert result["ready_for_next_local_note_count"] == 4
    assert result["blocked_for_real_data_count"] == 2
    assert result["waiting_on_policy_count"] == 0
    assert result["verified_no_action_count"] == 0
    assert result["residual_blocker_total"] == progress["residual_blocker_total"]


def test_progress_review_preserves_authorization_gates(tmp_path) -> None:
    progress = _progress_summary(tmp_path)
    result = operations_blocker_progress_review_summary(
        blocker_followup_progress_summary=progress
    )
    assert result["live_data_authorized_count"] == 0
    assert result["external_submission_authorized_count"] == 0
    assert result["all_external_authorization_disabled"] is True


def test_progress_review_matches_expected_progress_statuses(tmp_path) -> None:
    progress = _progress_summary(tmp_path)
    result = operations_blocker_progress_review_summary(
        blocker_followup_progress_summary=progress
    )
    assert result["status_mismatch_count"] == 0
    assert result["status_mismatches"] == []


def test_progress_review_missing_ids_are_reported(tmp_path) -> None:
    progress = _progress_summary(tmp_path)
    result = operations_blocker_progress_review_summary(
        expected_action_ids=["ops-action-001", "ops-action-999"],
        blocker_followup_progress_summary=progress,
    )
    assert result["missing_action_ids"] == ["ops-action-999"]
    assert result["stale_review_count"] == 6
    assert result["coverage_complete"] is False


def test_cli_operations_blocker_progress_review_summary_outputs_json(tmp_path) -> None:
    db_path = tmp_path / "ops.sqlite3"
    init_sqlite_log_db(db_path)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "techno_search.cli",
            "operations-blocker-progress-review-summary",
            "--sqlite-log-path",
            str(db_path),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["schema_version"] == OPERATIONS_BLOCKER_PROGRESS_REVIEW_SCHEMA_VERSION
    assert data["record_count"] == 7
    assert data["coverage_complete"] is True
