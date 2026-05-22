"""Tests for operations action-plan summaries."""

from __future__ import annotations

import json
import subprocess
import sys

from techno_search.operations_action_plan import (
    ALLOWED_ACTION_CATEGORIES,
    ALLOWED_ACTION_PRIORITIES,
    ALLOWED_ACTION_STATUSES,
    OPERATIONS_ACTION_PLAN_DISCLAIMER,
    OPERATIONS_ACTION_PLAN_SCHEMA_VERSION,
    build_operations_actions,
    operations_action_plan_summary,
)


def _clean_readiness() -> dict[str, object]:
    return {
        "qc_overall_health": "ok",
        "pipeline_capacity_status": "nominal",
        "open_alert_count": 0,
        "critical_open_alert_count": 0,
        "overdue_review_deadline_count": 0,
        "pipeline_health_blocked_count": 0,
        "validation_readiness_blocking_issue_count": 0,
        "curated_intake_blocking_issue_count": 0,
        "submission_missing_provenance_field_count": 0,
        "submission_blocking_issue_count": 0,
        "route_uncovered_pathway_count": 0,
        "external_submission_approved_count": 0,
        "network_access_allowed_count": 0,
        "sqlite_log_snapshot": {
            "integrity_ok": True,
            "weekly_digest_ok": True,
        },
    }


def test_action_plan_returns_dict() -> None:
    result = operations_action_plan_summary()
    assert isinstance(result, dict)


def test_action_plan_schema_version_and_disclaimer() -> None:
    result = operations_action_plan_summary()
    assert result["schema_version"] == OPERATIONS_ACTION_PLAN_SCHEMA_VERSION
    assert result["disclaimer"] == OPERATIONS_ACTION_PLAN_DISCLAIMER
    assert "do not authorize live data access" in result["disclaimer"]


def test_clean_readiness_has_no_actions() -> None:
    result = operations_action_plan_summary(_clean_readiness())
    assert result["action_count"] == 0
    assert result["all_actions_clear"] is True
    assert result["next_action"] is None


def test_current_fixture_readiness_has_real_data_blockers() -> None:
    result = operations_action_plan_summary()
    assert result["action_count"] >= 1
    assert result["critical_action_count"] >= 1
    assert result["real_data_blocking_action_count"] >= 1
    assert result["next_action"] is not None


def test_build_actions_uses_allowed_values() -> None:
    actions = build_operations_actions()
    for action in actions:
        assert action.category in ALLOWED_ACTION_CATEGORIES
        assert action.priority in ALLOWED_ACTION_PRIORITIES
        assert action.status in ALLOWED_ACTION_STATUSES
        assert action.blocker_count >= 1


def test_alerts_create_operator_review_action() -> None:
    readiness = _clean_readiness()
    readiness["open_alert_count"] = 2
    result = operations_action_plan_summary(readiness)
    assert result["operator_review_action_count"] == 1
    assert result["by_category"] == {"alerts": 1}


def test_validation_readiness_creates_real_data_blocking_action() -> None:
    readiness = _clean_readiness()
    readiness["validation_readiness_blocking_issue_count"] = 3
    result = operations_action_plan_summary(readiness)
    assert result["real_data_blocking_action_count"] == 1
    assert result["by_category"] == {"validation_readiness": 1}


def test_cli_operations_action_plan_summary_outputs_json() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "operations-action-plan-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["schema_version"] == OPERATIONS_ACTION_PLAN_SCHEMA_VERSION
    assert "actions" in data
