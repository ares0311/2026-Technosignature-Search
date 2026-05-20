"""Tests for local operations readiness summaries."""

from __future__ import annotations

import json
import subprocess
import sys

from techno_search.log_store import init_sqlite_log_db
from techno_search.operations_readiness import (
    ALLOWED_OPERATIONS_READINESS_RECOMMENDATIONS,
    OPERATIONS_READINESS_DISCLAIMER,
    OPERATIONS_READINESS_SCHEMA_VERSION,
    operations_readiness_digest,
    operations_readiness_summary,
)


def _clean_summary() -> dict[str, object]:
    return operations_readiness_summary(
        quality_control={"overall_qc_health": "ok"},
        pipeline_capacity={"capacity_status": "nominal"},
        candidate_alerts={"open_count": 0, "critical_open_count": 0},
        review_deadlines={"overdue_count": 0},
        pipeline_health={"total_blocked_count": 0},
        route_coverage={"uncovered_pathway_count": 0},
        validation_readiness={"blocking_issue_count": 0},
        curated_intake={"total_blocking_issue_count": 0},
        submission_readiness={
            "total_missing_provenance_field_count": 0,
            "total_blocking_issue_count": 0,
        },
        user_decisions={"external_submission_approved_count": 0},
        sqlite_logs={
            "run_count": 2,
            "network_access_allowed_count": 0,
            "external_submission_approved_count": 0,
        },
        sqlite_integrity={"ok": True},
        sqlite_weekly_digest={"ok": True},
    )


def test_operations_readiness_returns_dict() -> None:
    result = operations_readiness_summary()
    assert isinstance(result, dict)


def test_operations_readiness_schema_version_and_disclaimer() -> None:
    result = operations_readiness_summary()
    assert result["schema_version"] == OPERATIONS_READINESS_SCHEMA_VERSION
    assert result["disclaimer"] == OPERATIONS_READINESS_DISCLAIMER
    assert "do not authorize live-provider access" in result["disclaimer"]


def test_operations_readiness_recommendation_is_allowed() -> None:
    result = operations_readiness_summary()
    assert result["recommendation"] in ALLOWED_OPERATIONS_READINESS_RECOMMENDATIONS


def test_clean_inputs_are_local_only_ready() -> None:
    result = _clean_summary()
    assert result["recommendation"] == "local_only_ready"
    assert result["local_validation_ready"] is True
    assert result["real_data_blocker_count"] == 0
    assert result["operator_attention_count"] == 0


def test_open_alert_requires_operator_review() -> None:
    result = operations_readiness_summary(
        quality_control={"overall_qc_health": "ok"},
        pipeline_capacity={"capacity_status": "nominal"},
        candidate_alerts={"open_count": 1, "critical_open_count": 0},
        review_deadlines={"overdue_count": 0},
        pipeline_health={"total_blocked_count": 0},
        route_coverage={"uncovered_pathway_count": 0},
        validation_readiness={"blocking_issue_count": 0},
        curated_intake={"total_blocking_issue_count": 0},
        submission_readiness={
            "total_missing_provenance_field_count": 0,
            "total_blocking_issue_count": 0,
        },
        user_decisions={"external_submission_approved_count": 0},
        sqlite_logs={
            "run_count": 2,
            "network_access_allowed_count": 0,
            "external_submission_approved_count": 0,
        },
        sqlite_integrity={"ok": True},
        sqlite_weekly_digest={"ok": True},
    )
    assert result["recommendation"] == "operator_review_required"
    assert result["operator_attention_count"] == 1


def test_validation_blockers_block_real_data() -> None:
    result = operations_readiness_summary(
        quality_control={"overall_qc_health": "ok"},
        pipeline_capacity={"capacity_status": "nominal"},
        candidate_alerts={"open_count": 0, "critical_open_count": 0},
        review_deadlines={"overdue_count": 0},
        pipeline_health={"total_blocked_count": 0},
        route_coverage={"uncovered_pathway_count": 0},
        validation_readiness={"blocking_issue_count": 2},
        curated_intake={"total_blocking_issue_count": 0},
        submission_readiness={
            "total_missing_provenance_field_count": 0,
            "total_blocking_issue_count": 0,
        },
        user_decisions={"external_submission_approved_count": 0},
        sqlite_logs={
            "run_count": 2,
            "network_access_allowed_count": 0,
            "external_submission_approved_count": 0,
        },
        sqlite_integrity={"ok": True},
        sqlite_weekly_digest={"ok": True},
    )
    assert result["recommendation"] == "blocked_for_real_data"
    assert result["real_data_blocker_count"] == 2


def test_sqlite_log_path_restores_sqlite_readiness_gates(tmp_path) -> None:
    db_path = tmp_path / "logs" / "techno_search.sqlite3"
    init_sqlite_log_db(
        db_path,
        code_commit="ops-readiness-test",
        config_version="background_priority_v0",
    )

    result = operations_readiness_summary(sqlite_log_path=db_path)
    sqlite_snapshot = result["sqlite_log_snapshot"]

    assert sqlite_snapshot["present"] is True
    assert sqlite_snapshot["integrity_ok"] is True
    assert sqlite_snapshot["weekly_digest_ok"] is True
    assert sqlite_snapshot["network_access_allowed_count"] == 0
    assert sqlite_snapshot["external_submission_approved_count"] == 0
    assert result["readiness_gates"]["sqlite_integrity_ok"] is True
    assert result["readiness_gates"]["sqlite_weekly_digest_ok"] is True
    assert "SQLite log integrity is not confirmed" not in result[
        "outstanding_blockers"
    ]
    assert "SQLite weekly digest is not confirmed" not in result[
        "outstanding_blockers"
    ]


def test_digest_contains_review_safe_markdown() -> None:
    digest = operations_readiness_digest(_clean_summary())
    assert digest["schema_version"] == OPERATIONS_READINESS_SCHEMA_VERSION
    assert digest["recommendation"] == "local_only_ready"
    assert "# Operations Readiness Digest" in digest["markdown"]
    assert "does not include large data payloads" in digest["markdown"]


def test_cli_operations_readiness_summary_outputs_json() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "operations-readiness-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["schema_version"] == OPERATIONS_READINESS_SCHEMA_VERSION
    assert "recommendation" in data


def test_cli_operations_readiness_digest_outputs_markdown() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "operations-readiness-digest"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "# Operations Readiness Digest" in result.stdout
    assert "External submission approvals logged" in result.stdout
