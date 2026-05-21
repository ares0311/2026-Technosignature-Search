"""Tests for operations blocker progress next-action records."""

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
from techno_search.operations_blocker_progress_next_actions import (
    ALLOWED_BLOCKER_PROGRESS_NEXT_ACTION_STATUSES,
    OPERATIONS_BLOCKER_PROGRESS_NEXT_ACTIONS_DISCLAIMER,
    OPERATIONS_BLOCKER_PROGRESS_NEXT_ACTIONS_SCHEMA_VERSION,
    load_operations_blocker_progress_next_action_records,
    operations_blocker_progress_next_actions_summary,
)
from techno_search.operations_blocker_progress_review import (
    operations_blocker_progress_review_summary,
)
from techno_search.operations_blocker_review import operations_blocker_review_summary


def _progress_review_summary(tmp_path):
    db_path = tmp_path / "ops.sqlite3"
    init_sqlite_log_db(db_path)
    detail = operations_blocker_detail_summary(sqlite_log_path=db_path)
    review = operations_blocker_review_summary(blocker_detail_summary=detail)
    followup = operations_blocker_followup_summary(
        blocker_detail_summary_data=detail,
        blocker_review_summary_data=review,
    )
    progress = operations_blocker_followup_progress_summary(
        expected_action_ids=[
            str(action["action_id"])
            for action in followup["actions"]
            if isinstance(action, dict)
        ],
        blocker_followup_summary=followup,
    )
    return operations_blocker_progress_review_summary(
        expected_action_ids=[
            str(record["action_id"])
            for record in progress["records"]
            if isinstance(record, dict)
            and str(record.get("progress_status", "")) != "verified_local"
        ],
        blocker_followup_progress_summary=progress,
    )


def test_load_progress_next_actions_covers_unresolved_review_actions() -> None:
    records = load_operations_blocker_progress_next_action_records()
    assert len(records) == 7
    assert [record.priority_rank for record in records] == list(range(1, 8))
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


def test_progress_next_actions_schema_version_and_disclaimer(tmp_path) -> None:
    review = _progress_review_summary(tmp_path)
    result = operations_blocker_progress_next_actions_summary(
        blocker_progress_review_summary=review
    )
    assert (
        result["schema_version"]
        == OPERATIONS_BLOCKER_PROGRESS_NEXT_ACTIONS_SCHEMA_VERSION
    )
    assert result["disclaimer"] == OPERATIONS_BLOCKER_PROGRESS_NEXT_ACTIONS_DISCLAIMER
    assert "do not clear blockers" in result["disclaimer"]


def test_progress_next_action_statuses_are_allowed() -> None:
    records = load_operations_blocker_progress_next_action_records()
    for record in records:
        assert (
            record.next_action_status
            in ALLOWED_BLOCKER_PROGRESS_NEXT_ACTION_STATUSES
        )


def test_progress_next_actions_cover_unresolved_reviews_only(tmp_path) -> None:
    review = _progress_review_summary(tmp_path)
    result = operations_blocker_progress_next_actions_summary(
        blocker_progress_review_summary=review
    )
    assert result["record_count"] == review["record_count"]
    assert result["expected_action_count"] == 7
    assert result["covered_action_count"] == 7
    assert result["missing_action_count"] == 0
    assert result["stale_next_action_count"] == 0
    assert result["coverage_fraction"] == 1.0
    assert result["coverage_complete"] is True
    assert result["verified_progress_action_ids"] == ["ops-action-004"]


def test_progress_next_actions_count_statuses_and_blockers(tmp_path) -> None:
    review = _progress_review_summary(tmp_path)
    result = operations_blocker_progress_next_actions_summary(
        blocker_progress_review_summary=review
    )
    assert result["operator_action_required_count"] == 1
    assert result["local_note_ready_count"] == 4
    assert result["blocked_pending_real_data_count"] == 2
    assert result["policy_review_required_count"] == 0
    assert result["no_action_required_count"] == 0
    assert result["residual_blocker_total"] == review["residual_blocker_total"]
    assert result["priority_sequence_ok"] is True


def test_progress_next_actions_preserve_authorization_gates(tmp_path) -> None:
    review = _progress_review_summary(tmp_path)
    result = operations_blocker_progress_next_actions_summary(
        blocker_progress_review_summary=review
    )
    assert result["live_data_authorized_count"] == 0
    assert result["external_submission_authorized_count"] == 0
    assert result["all_external_authorization_disabled"] is True


def test_progress_next_actions_match_expected_review_statuses(tmp_path) -> None:
    review = _progress_review_summary(tmp_path)
    result = operations_blocker_progress_next_actions_summary(
        blocker_progress_review_summary=review
    )
    assert result["status_mismatch_count"] == 0
    assert result["status_mismatches"] == []


def test_progress_next_actions_missing_ids_are_reported(tmp_path) -> None:
    review = _progress_review_summary(tmp_path)
    result = operations_blocker_progress_next_actions_summary(
        expected_action_ids=["ops-action-001", "ops-action-999"],
        blocker_progress_review_summary=review,
    )
    assert result["missing_action_ids"] == ["ops-action-999"]
    assert result["stale_next_action_count"] == 6
    assert result["coverage_complete"] is False


def test_cli_operations_blocker_progress_next_actions_summary_outputs_json(
    tmp_path,
) -> None:
    db_path = tmp_path / "ops.sqlite3"
    init_sqlite_log_db(db_path)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "techno_search.cli",
            "operations-blocker-progress-next-actions-summary",
            "--sqlite-log-path",
            str(db_path),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert (
        data["schema_version"]
        == OPERATIONS_BLOCKER_PROGRESS_NEXT_ACTIONS_SCHEMA_VERSION
    )
    assert data["record_count"] == 7
    assert data["coverage_complete"] is True
