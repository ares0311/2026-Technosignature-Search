"""Tests for local operations blocker follow-up summaries."""

from __future__ import annotations

import json
import subprocess
import sys

from techno_search.log_store import init_sqlite_log_db
from techno_search.operations_blocker_detail import operations_blocker_detail_summary
from techno_search.operations_blocker_followup import (
    ALLOWED_BLOCKER_FOLLOWUP_RECOMMENDATIONS,
    OPERATIONS_BLOCKER_FOLLOWUP_DISCLAIMER,
    OPERATIONS_BLOCKER_FOLLOWUP_SCHEMA_VERSION,
    operations_blocker_followup_summary,
)
from techno_search.operations_blocker_review import operations_blocker_review_summary


def _inputs(tmp_path):
    db_path = tmp_path / "ops.sqlite3"
    init_sqlite_log_db(db_path)
    detail = operations_blocker_detail_summary(sqlite_log_path=db_path)
    review = operations_blocker_review_summary(blocker_detail_summary=detail)
    return detail, review


def test_blocker_followup_summary_schema_version_and_disclaimer(tmp_path) -> None:
    detail, review = _inputs(tmp_path)
    result = operations_blocker_followup_summary(
        blocker_detail_summary_data=detail,
        blocker_review_summary_data=review,
    )

    assert result["schema_version"] == OPERATIONS_BLOCKER_FOLLOWUP_SCHEMA_VERSION
    assert result["disclaimer"] == OPERATIONS_BLOCKER_FOLLOWUP_DISCLAIMER
    assert "does not clear blockers" in result["disclaimer"]


def test_blocker_followup_recommendations_are_allowed(tmp_path) -> None:
    detail, review = _inputs(tmp_path)
    result = operations_blocker_followup_summary(
        blocker_detail_summary_data=detail,
        blocker_review_summary_data=review,
    )

    for action in result["actions"]:
        assert action["recommendation"] in ALLOWED_BLOCKER_FOLLOWUP_RECOMMENDATIONS


def test_blocker_followup_counts_current_review_actions(tmp_path) -> None:
    detail, review = _inputs(tmp_path)
    result = operations_blocker_followup_summary(
        blocker_detail_summary_data=detail,
        blocker_review_summary_data=review,
    )

    assert result["action_count"] == 8
    assert result["action_required_count"] == 7
    assert result["operator_attention_required_count"] == 3
    assert result["local_remediation_count"] == 2
    assert result["real_data_hold_count"] == 2
    assert result["verification_ready_count"] == 1
    assert result["reopen_required_count"] == 0
    assert result["authorization_review_required_count"] == 0


def test_blocker_followup_preserves_blockers_and_authorization_gates(tmp_path) -> None:
    detail, review = _inputs(tmp_path)
    result = operations_blocker_followup_summary(
        blocker_detail_summary_data=detail,
        blocker_review_summary_data=review,
    )

    assert result["residual_blocker_total"] == 29
    assert result["live_data_authorized_count"] == 0
    assert result["external_submission_authorized_count"] == 0
    assert result["all_external_authorization_disabled"] is True


def test_blocker_followup_keeps_review_and_detail_coverage_visible(tmp_path) -> None:
    detail, review = _inputs(tmp_path)
    result = operations_blocker_followup_summary(
        blocker_detail_summary_data=detail,
        blocker_review_summary_data=review,
    )

    assert result["coverage_complete"] is True
    assert result["all_detail_evidence_reviewed"] is True
    assert result["evidence_review_complete"] is True


def test_blocker_followup_prioritizes_open_items_before_real_data_holds(tmp_path) -> None:
    detail, review = _inputs(tmp_path)
    result = operations_blocker_followup_summary(
        blocker_detail_summary_data=detail,
        blocker_review_summary_data=review,
    )

    assert result["next_action_ids"][:3] == [
        "ops-action-008",
        "ops-action-005",
        "ops-action-003",
    ]
    assert result["real_data_hold_action_ids"] == ["ops-action-007", "ops-action-006"]
    assert result["verification_ready_action_ids"] == ["ops-action-004"]


def test_cli_operations_blocker_followup_summary_outputs_json(tmp_path) -> None:
    db_path = tmp_path / "ops.sqlite3"
    init_sqlite_log_db(db_path)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "techno_search.cli",
            "operations-blocker-followup-summary",
            "--sqlite-log-path",
            str(db_path),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["schema_version"] == OPERATIONS_BLOCKER_FOLLOWUP_SCHEMA_VERSION
    assert data["action_count"] == 8
    assert data["all_external_authorization_disabled"] is True
