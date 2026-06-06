"""Tests for local operations blocker follow-up progress records."""

from __future__ import annotations

import json
import subprocess
import sys

from techno_search.log_store import init_sqlite_log_db
from techno_search.operations_blocker_detail import operations_blocker_detail_summary
from techno_search.operations_blocker_followup import operations_blocker_followup_summary
from techno_search.operations_blocker_followup_progress import (
    ALLOWED_BLOCKER_FOLLOWUP_PROGRESS_STATUSES,
    OPERATIONS_BLOCKER_FOLLOWUP_PROGRESS_DISCLAIMER,
    OPERATIONS_BLOCKER_FOLLOWUP_PROGRESS_SCHEMA_VERSION,
    load_operations_blocker_followup_progress_records,
    operations_blocker_followup_progress_summary,
)
from techno_search.operations_blocker_review import operations_blocker_review_summary


def _followup_summary(tmp_path):
    db_path = tmp_path / "ops.sqlite3"
    init_sqlite_log_db(db_path)
    detail = operations_blocker_detail_summary(sqlite_log_path=db_path)
    review = operations_blocker_review_summary(blocker_detail_summary=detail)
    return operations_blocker_followup_summary(
        blocker_detail_summary_data=detail,
        blocker_review_summary_data=review,
    )


def test_load_blocker_followup_progress_records_returns_current_actions() -> None:
    records = load_operations_blocker_followup_progress_records()
    assert len(records) == 7
    assert {record.action_id for record in records} == {
        f"ops-action-{idx:03d}" for idx in range(1, 8)
    }


def test_blocker_followup_progress_schema_version_and_disclaimer(tmp_path) -> None:
    followup = _followup_summary(tmp_path)
    result = operations_blocker_followup_progress_summary(
        blocker_followup_summary=followup
    )
    assert result["schema_version"] == OPERATIONS_BLOCKER_FOLLOWUP_PROGRESS_SCHEMA_VERSION
    assert result["disclaimer"] == OPERATIONS_BLOCKER_FOLLOWUP_PROGRESS_DISCLAIMER
    assert "does not clear blockers" in result["disclaimer"]


def test_blocker_followup_progress_statuses_are_allowed() -> None:
    records = load_operations_blocker_followup_progress_records()
    for record in records:
        assert record.progress_status in ALLOWED_BLOCKER_FOLLOWUP_PROGRESS_STATUSES


def test_blocker_followup_progress_covers_current_followup_actions(tmp_path) -> None:
    followup = _followup_summary(tmp_path)
    result = operations_blocker_followup_progress_summary(
        blocker_followup_summary=followup
    )
    assert result["expected_action_count"] == 7
    assert result["covered_action_count"] == 7
    assert result["missing_action_count"] == 0
    assert result["stale_progress_count"] == 0
    assert result["coverage_fraction"] == 1.0
    assert result["coverage_complete"] is True


def test_blocker_followup_progress_counts_status_and_blockers(tmp_path) -> None:
    followup = _followup_summary(tmp_path)
    result = operations_blocker_followup_progress_summary(
        blocker_followup_summary=followup
    )
    assert result["record_count"] == 7
    assert result["not_started_count"] == 0
    assert result["in_progress_count"] == 4
    assert result["waiting_for_real_data_count"] == 2
    assert result["verified_local_count"] == 1
    assert result["unresolved_progress_count"] == 6
    assert result["residual_blocker_total"] == 26


def test_blocker_followup_progress_preserves_authorization_gates(tmp_path) -> None:
    followup = _followup_summary(tmp_path)
    result = operations_blocker_followup_progress_summary(
        blocker_followup_summary=followup
    )
    assert result["live_data_authorized_count"] == 0
    assert result["external_submission_authorized_count"] == 0
    assert result["all_external_authorization_disabled"] is True


def test_blocker_followup_progress_matches_followup_recommendations(tmp_path) -> None:
    followup = _followup_summary(tmp_path)
    result = operations_blocker_followup_progress_summary(
        blocker_followup_summary=followup
    )
    assert result["recommendation_mismatch_count"] == 0
    assert result["recommendation_mismatches"] == []


def test_blocker_followup_progress_missing_ids_are_reported(tmp_path) -> None:
    followup = _followup_summary(tmp_path)
    result = operations_blocker_followup_progress_summary(
        expected_action_ids=["ops-action-001", "ops-action-999"],
        blocker_followup_summary=followup,
    )
    assert result["missing_action_ids"] == ["ops-action-999"]
    assert result["stale_progress_count"] == 6
    assert result["coverage_complete"] is False


def test_cli_operations_blocker_followup_progress_summary_outputs_json(tmp_path) -> None:
    db_path = tmp_path / "ops.sqlite3"
    init_sqlite_log_db(db_path)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "techno_search.cli",
            "operations-blocker-followup-progress-summary",
            "--sqlite-log-path",
            str(db_path),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["schema_version"] == OPERATIONS_BLOCKER_FOLLOWUP_PROGRESS_SCHEMA_VERSION
    assert data["record_count"] == 7
    assert data["coverage_complete"] is True
