"""Tests for operations blocker-review summaries."""

from __future__ import annotations

import json
import subprocess
import sys

from techno_search.log_store import init_sqlite_log_db
from techno_search.operations_blocker_detail import operations_blocker_detail_summary
from techno_search.operations_blocker_review import (
    ALLOWED_BLOCKER_REVIEW_STATUSES,
    OPERATIONS_BLOCKER_REVIEW_DISCLAIMER,
    OPERATIONS_BLOCKER_REVIEW_SCHEMA_VERSION,
    load_operations_blocker_review_records,
    operations_blocker_review_summary,
)


def _detail_summary(tmp_path):
    db_path = tmp_path / "ops.sqlite3"
    init_sqlite_log_db(db_path)
    return operations_blocker_detail_summary(sqlite_log_path=db_path)


def test_load_blocker_review_records_returns_records() -> None:
    records = load_operations_blocker_review_records()
    assert len(records) == 8
    assert {record.action_id for record in records} == {
        f"ops-action-{idx:03d}" for idx in range(1, 9)
    }


def test_blocker_review_summary_schema_version_and_disclaimer(tmp_path) -> None:
    detail = _detail_summary(tmp_path)
    result = operations_blocker_review_summary(blocker_detail_summary=detail)
    assert result["schema_version"] == OPERATIONS_BLOCKER_REVIEW_SCHEMA_VERSION
    assert result["disclaimer"] == OPERATIONS_BLOCKER_REVIEW_DISCLAIMER
    assert "does not clear blockers" in result["disclaimer"]


def test_blocker_review_statuses_are_allowed() -> None:
    records = load_operations_blocker_review_records()
    for record in records:
        assert record.review_status in ALLOWED_BLOCKER_REVIEW_STATUSES


def test_blocker_review_covers_current_detail_actions(tmp_path) -> None:
    detail = _detail_summary(tmp_path)
    result = operations_blocker_review_summary(blocker_detail_summary=detail)
    assert result["expected_action_count"] == 8
    assert result["covered_action_count"] == 8
    assert result["missing_action_count"] == 0
    assert result["stale_review_count"] == 0
    assert result["coverage_complete"] is True
    assert result["coverage_fraction"] == 1.0


def test_blocker_review_preserves_residual_blockers_and_zero_authorization(
    tmp_path,
) -> None:
    detail = _detail_summary(tmp_path)
    result = operations_blocker_review_summary(blocker_detail_summary=detail)
    assert result["residual_blocker_total"] == 29
    assert result["live_data_authorized_count"] == 0
    assert result["external_submission_authorized_count"] == 0
    assert result["all_external_authorization_disabled"] is True


def test_blocker_review_accounts_for_all_detail_evidence(tmp_path) -> None:
    detail = _detail_summary(tmp_path)
    result = operations_blocker_review_summary(blocker_detail_summary=detail)
    assert result["detail_evidence_record_count"] == 32
    assert result["reviewed_evidence_record_count"] == 32
    assert result["unreviewed_evidence_record_count"] == 0
    assert result["evidence_count_mismatch_count"] == 0
    assert result["all_detail_evidence_reviewed"] is True


def test_blocker_review_missing_expected_ids_are_reported(tmp_path) -> None:
    detail = _detail_summary(tmp_path)
    result = operations_blocker_review_summary(
        expected_action_ids=["ops-action-001", "ops-action-999"],
        blocker_detail_summary=detail,
    )
    assert result["missing_action_ids"] == ["ops-action-999"]
    assert result["stale_review_count"] == 7
    assert result["coverage_complete"] is False


def test_cli_operations_blocker_review_summary_outputs_json(tmp_path) -> None:
    db_path = tmp_path / "ops.sqlite3"
    init_sqlite_log_db(db_path)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "techno_search.cli",
            "operations-blocker-review-summary",
            "--sqlite-log-path",
            str(db_path),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["schema_version"] == OPERATIONS_BLOCKER_REVIEW_SCHEMA_VERSION
    assert data["record_count"] == 8
    assert data["all_detail_evidence_reviewed"] is True
