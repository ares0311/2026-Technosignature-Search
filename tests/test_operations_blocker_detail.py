"""Tests for operations blocker-detail summaries."""

from __future__ import annotations

import json
import subprocess
import sys

from techno_search.log_store import init_sqlite_log_db
from techno_search.operations_blocker_detail import (
    OPERATIONS_BLOCKER_DETAIL_DISCLAIMER,
    OPERATIONS_BLOCKER_DETAIL_SCHEMA_VERSION,
    operations_blocker_detail_summary,
)


def test_blocker_detail_returns_dict(tmp_path) -> None:
    db_path = tmp_path / "ops.sqlite3"
    init_sqlite_log_db(db_path)
    result = operations_blocker_detail_summary(sqlite_log_path=db_path)
    assert isinstance(result, dict)


def test_blocker_detail_schema_version_and_disclaimer(tmp_path) -> None:
    db_path = tmp_path / "ops.sqlite3"
    init_sqlite_log_db(db_path)
    result = operations_blocker_detail_summary(sqlite_log_path=db_path)
    assert result["schema_version"] == OPERATIONS_BLOCKER_DETAIL_SCHEMA_VERSION
    assert result["disclaimer"] == OPERATIONS_BLOCKER_DETAIL_DISCLAIMER
    assert "do not clear blockers" in result["disclaimer"]


def test_blocker_detail_matches_current_action_plan(tmp_path) -> None:
    db_path = tmp_path / "ops.sqlite3"
    init_sqlite_log_db(db_path)
    result = operations_blocker_detail_summary(sqlite_log_path=db_path)
    assert result["action_count"] == 8
    assert result["detail_count"] == result["action_count"]
    assert result["total_evidence_record_count"] >= 8
    assert result["readiness_recommendation"] == "blocked_for_real_data"
    assert result["sqlite_context_is_resolved"] is True


def test_blocker_detail_preserves_local_only_authorization_counts(tmp_path) -> None:
    db_path = tmp_path / "ops.sqlite3"
    init_sqlite_log_db(db_path)
    result = operations_blocker_detail_summary(sqlite_log_path=db_path)
    assert result["local_only"] is True
    assert result["network_access_allowed_count"] == 0
    assert result["external_submission_approved_count"] == 0
    assert result["all_external_authorization_disabled"] is True


def test_blocker_detail_expands_expected_categories(tmp_path) -> None:
    db_path = tmp_path / "ops.sqlite3"
    init_sqlite_log_db(db_path)
    result = operations_blocker_detail_summary(sqlite_log_path=db_path)
    assert result["categories_with_details"] == [
        "alerts",
        "capacity",
        "curated_intake",
        "pipeline_health",
        "quality_control",
        "review_deadlines",
        "submission_provenance",
        "validation_readiness",
    ]


def test_blocker_detail_contains_source_records(tmp_path) -> None:
    db_path = tmp_path / "ops.sqlite3"
    init_sqlite_log_db(db_path)
    result = operations_blocker_detail_summary(sqlite_log_path=db_path)
    by_category = {detail["category"]: detail for detail in result["details"]}
    assert by_category["alerts"]["evidence_records"]["open_alerts"]
    assert by_category["review_deadlines"]["evidence_records"][
        "overdue_or_pending_deadlines"
    ]
    assert by_category["validation_readiness"]["evidence_records"][
        "records_requiring_review"
    ]
    assert by_category["curated_intake"]["evidence_records"][
        "records_requiring_review"
    ]
    assert by_category["submission_provenance"]["evidence_records"][
        "records_with_missing_or_blocked_provenance"
    ]


def test_cli_operations_blocker_detail_summary_outputs_json(tmp_path) -> None:
    db_path = tmp_path / "ops.sqlite3"
    init_sqlite_log_db(db_path)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "techno_search.cli",
            "operations-blocker-detail-summary",
            "--sqlite-log-path",
            str(db_path),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["schema_version"] == OPERATIONS_BLOCKER_DETAIL_SCHEMA_VERSION
    assert data["detail_count"] == 8
