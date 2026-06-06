"""Tests for operations blocker progress execution-followup records."""

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
from techno_search.operations_blocker_progress_execution import (
    operations_blocker_progress_execution_summary,
)
from techno_search.operations_blocker_progress_execution_followup import (
    ALLOWED_BLOCKER_PROGRESS_EXECUTION_FOLLOWUP_STATUSES,
    OPERATIONS_BLOCKER_PROGRESS_EXECUTION_FOLLOWUP_DISCLAIMER,
    OPERATIONS_BLOCKER_PROGRESS_EXECUTION_FOLLOWUP_SCHEMA_VERSION,
    load_operations_blocker_progress_execution_followup_records,
    operations_blocker_progress_execution_followup_summary,
)
from techno_search.operations_blocker_progress_execution_review import (
    operations_blocker_progress_execution_review_summary,
)
from techno_search.operations_blocker_progress_next_actions import (
    operations_blocker_progress_next_actions_summary,
)
from techno_search.operations_blocker_progress_review import (
    operations_blocker_progress_review_summary,
)
from techno_search.operations_blocker_review import operations_blocker_review_summary


def _progress_execution_review_summary(tmp_path):
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
    progress_review = operations_blocker_progress_review_summary(
        expected_action_ids=[
            str(record["action_id"])
            for record in progress["records"]
            if isinstance(record, dict)
            and str(record.get("progress_status", "")) != "verified_local"
        ],
        blocker_followup_progress_summary=progress,
    )
    next_actions = operations_blocker_progress_next_actions_summary(
        expected_action_ids=[
            str(record["action_id"])
            for record in progress_review["records"]
            if isinstance(record, dict)
        ],
        blocker_progress_review_summary=progress_review,
    )
    execution = operations_blocker_progress_execution_summary(
        expected_next_action_ids=[
            str(record["next_action_id"])
            for record in next_actions["records"]
            if isinstance(record, dict)
        ],
        blocker_progress_next_actions_summary=next_actions,
    )
    return operations_blocker_progress_execution_review_summary(
        expected_execution_ids=[
            str(record["execution_id"])
            for record in execution["records"]
            if isinstance(record, dict)
        ],
        blocker_progress_execution_summary=execution,
    )


def test_load_progress_execution_followup_records_covers_reviews() -> None:
    records = load_operations_blocker_progress_execution_followup_records()
    assert len(records) == 6
    assert [record.priority_rank for record in records] == list(range(2, 8))
    assert {record.review_id for record in records} == {
        f"ops-progress-exec-review-{idx:03d}" for idx in range(2, 8)
    }
    assert "ops-action-004" in {record.action_id for record in records}


def test_progress_execution_followup_schema_version_and_disclaimer(tmp_path) -> None:
    execution_review = _progress_execution_review_summary(tmp_path)
    result = operations_blocker_progress_execution_followup_summary(
        blocker_progress_execution_review_summary=execution_review
    )
    assert (
        result["schema_version"]
        == OPERATIONS_BLOCKER_PROGRESS_EXECUTION_FOLLOWUP_SCHEMA_VERSION
    )
    assert (
        result["disclaimer"]
        == OPERATIONS_BLOCKER_PROGRESS_EXECUTION_FOLLOWUP_DISCLAIMER
    )
    assert "does not clear blockers" in result["disclaimer"]


def test_progress_execution_followup_statuses_are_allowed() -> None:
    records = load_operations_blocker_progress_execution_followup_records()
    for record in records:
        assert (
            record.followup_status
            in ALLOWED_BLOCKER_PROGRESS_EXECUTION_FOLLOWUP_STATUSES
        )


def test_progress_execution_followup_covers_reviews_only(tmp_path) -> None:
    execution_review = _progress_execution_review_summary(tmp_path)
    result = operations_blocker_progress_execution_followup_summary(
        blocker_progress_execution_review_summary=execution_review
    )
    assert result["record_count"] == execution_review["record_count"]
    assert result["expected_review_count"] == 6
    assert result["covered_review_count"] == 6
    assert result["missing_review_count"] == 0
    assert result["stale_followup_count"] == 0
    assert result["coverage_fraction"] == 1.0
    assert result["coverage_complete"] is True
    assert result["verified_progress_action_ids"] == ["ops-action-003"]


def test_progress_execution_followup_counts_statuses_and_blockers(tmp_path) -> None:
    execution_review = _progress_execution_review_summary(tmp_path)
    result = operations_blocker_progress_execution_followup_summary(
        blocker_progress_execution_review_summary=execution_review
    )
    assert result["operator_followup_required_count"] == 0
    assert result["local_note_followup_ready_count"] == 4
    assert result["blocked_pending_real_data_count"] == 2
    assert result["policy_review_pending_count"] == 0
    assert result["no_followup_required_count"] == 0
    assert result["residual_blocker_total"] == execution_review["residual_blocker_total"]
    assert result["priority_sequence_ok"] is True


def test_progress_execution_followup_preserves_authorization_gates(tmp_path) -> None:
    execution_review = _progress_execution_review_summary(tmp_path)
    result = operations_blocker_progress_execution_followup_summary(
        blocker_progress_execution_review_summary=execution_review
    )
    assert result["live_data_authorized_count"] == 0
    assert result["external_submission_authorized_count"] == 0
    assert result["all_external_authorization_disabled"] is True


def test_progress_execution_followup_matches_review_records(tmp_path) -> None:
    execution_review = _progress_execution_review_summary(tmp_path)
    result = operations_blocker_progress_execution_followup_summary(
        blocker_progress_execution_review_summary=execution_review
    )
    assert result["status_mismatch_count"] == 0
    assert result["residual_mismatch_count"] == 0
    assert result["priority_mismatch_count"] == 0
    assert result["status_mismatches"] == []


def test_progress_execution_followup_missing_ids_are_reported(tmp_path) -> None:
    execution_review = _progress_execution_review_summary(tmp_path)
    result = operations_blocker_progress_execution_followup_summary(
        expected_review_ids=[
            "ops-progress-exec-review-002",
            "ops-progress-exec-review-999",
        ],
        blocker_progress_execution_review_summary=execution_review,
    )
    assert result["missing_review_ids"] == ["ops-progress-exec-review-999"]
    assert result["stale_followup_count"] == 5
    assert result["coverage_complete"] is False


def test_cli_operations_blocker_progress_execution_followup_summary_outputs_json(
    tmp_path,
) -> None:
    db_path = tmp_path / "ops.sqlite3"
    init_sqlite_log_db(db_path)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "techno_search.cli",
            "operations-blocker-progress-execution-followup-summary",
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
        == OPERATIONS_BLOCKER_PROGRESS_EXECUTION_FOLLOWUP_SCHEMA_VERSION
    )
    assert data["record_count"] == 6
    assert data["coverage_complete"] is True
