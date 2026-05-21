"""Tests for operations blocker progress execution records."""

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
    ALLOWED_BLOCKER_PROGRESS_EXECUTION_STATUSES,
    OPERATIONS_BLOCKER_PROGRESS_EXECUTION_DISCLAIMER,
    OPERATIONS_BLOCKER_PROGRESS_EXECUTION_SCHEMA_VERSION,
    load_operations_blocker_progress_execution_records,
    operations_blocker_progress_execution_summary,
)
from techno_search.operations_blocker_progress_next_actions import (
    operations_blocker_progress_next_actions_summary,
)
from techno_search.operations_blocker_progress_review import (
    operations_blocker_progress_review_summary,
)
from techno_search.operations_blocker_review import operations_blocker_review_summary


def _progress_next_actions_summary(tmp_path):
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
    return operations_blocker_progress_next_actions_summary(
        expected_action_ids=[
            str(record["action_id"])
            for record in progress_review["records"]
            if isinstance(record, dict)
        ],
        blocker_progress_review_summary=progress_review,
    )


def test_load_progress_execution_records_covers_next_actions() -> None:
    records = load_operations_blocker_progress_execution_records()
    assert len(records) == 7
    assert [record.priority_rank for record in records] == list(range(1, 8))
    assert {record.next_action_id for record in records} == {
        f"ops-progress-next-{idx:03d}" for idx in range(1, 8)
    }
    assert "ops-action-004" not in {record.action_id for record in records}


def test_progress_execution_schema_version_and_disclaimer(tmp_path) -> None:
    next_actions = _progress_next_actions_summary(tmp_path)
    result = operations_blocker_progress_execution_summary(
        blocker_progress_next_actions_summary=next_actions
    )
    assert result["schema_version"] == OPERATIONS_BLOCKER_PROGRESS_EXECUTION_SCHEMA_VERSION
    assert result["disclaimer"] == OPERATIONS_BLOCKER_PROGRESS_EXECUTION_DISCLAIMER
    assert "do not clear blockers" in result["disclaimer"]


def test_progress_execution_statuses_are_allowed() -> None:
    records = load_operations_blocker_progress_execution_records()
    for record in records:
        assert record.execution_status in ALLOWED_BLOCKER_PROGRESS_EXECUTION_STATUSES


def test_progress_execution_covers_next_actions_only(tmp_path) -> None:
    next_actions = _progress_next_actions_summary(tmp_path)
    result = operations_blocker_progress_execution_summary(
        blocker_progress_next_actions_summary=next_actions
    )
    assert result["record_count"] == next_actions["record_count"]
    assert result["expected_next_action_count"] == 7
    assert result["covered_next_action_count"] == 7
    assert result["missing_next_action_count"] == 0
    assert result["stale_execution_count"] == 0
    assert result["coverage_fraction"] == 1.0
    assert result["coverage_complete"] is True
    assert result["verified_progress_action_ids"] == ["ops-action-004"]


def test_progress_execution_counts_statuses_and_blockers(tmp_path) -> None:
    next_actions = _progress_next_actions_summary(tmp_path)
    result = operations_blocker_progress_execution_summary(
        blocker_progress_next_actions_summary=next_actions
    )
    assert result["awaiting_operator_count"] == 1
    assert result["local_note_recorded_count"] == 4
    assert result["blocked_pending_real_data_count"] == 2
    assert result["policy_review_pending_count"] == 0
    assert result["no_execution_required_count"] == 0
    assert result["residual_blocker_total"] == next_actions["residual_blocker_total"]
    assert result["priority_sequence_ok"] is True


def test_progress_execution_preserves_authorization_gates(tmp_path) -> None:
    next_actions = _progress_next_actions_summary(tmp_path)
    result = operations_blocker_progress_execution_summary(
        blocker_progress_next_actions_summary=next_actions
    )
    assert result["live_data_authorized_count"] == 0
    assert result["external_submission_authorized_count"] == 0
    assert result["all_external_authorization_disabled"] is True


def test_progress_execution_matches_next_action_records(tmp_path) -> None:
    next_actions = _progress_next_actions_summary(tmp_path)
    result = operations_blocker_progress_execution_summary(
        blocker_progress_next_actions_summary=next_actions
    )
    assert result["status_mismatch_count"] == 0
    assert result["residual_mismatch_count"] == 0
    assert result["priority_mismatch_count"] == 0
    assert result["status_mismatches"] == []


def test_progress_execution_missing_ids_are_reported(tmp_path) -> None:
    next_actions = _progress_next_actions_summary(tmp_path)
    result = operations_blocker_progress_execution_summary(
        expected_next_action_ids=["ops-progress-next-001", "ops-progress-next-999"],
        blocker_progress_next_actions_summary=next_actions,
    )
    assert result["missing_next_action_ids"] == ["ops-progress-next-999"]
    assert result["stale_execution_count"] == 6
    assert result["coverage_complete"] is False


def test_cli_operations_blocker_progress_execution_summary_outputs_json(
    tmp_path,
) -> None:
    db_path = tmp_path / "ops.sqlite3"
    init_sqlite_log_db(db_path)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "techno_search.cli",
            "operations-blocker-progress-execution-summary",
            "--sqlite-log-path",
            str(db_path),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["schema_version"] == OPERATIONS_BLOCKER_PROGRESS_EXECUTION_SCHEMA_VERSION
    assert data["record_count"] == 7
    assert data["coverage_complete"] is True
