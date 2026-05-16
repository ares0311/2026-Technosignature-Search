"""Tests for operator assignment module."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from techno_search.operator_assignment import (
    ALLOWED_ASSIGNMENT_PRIORITIES,
    ALLOWED_ASSIGNMENT_STATUSES,
    OPERATOR_ASSIGNMENT_DISCLAIMER,
    OPERATOR_ASSIGNMENT_SCHEMA_VERSION,
    OperatorAssignment,
    load_operator_assignments,
    operator_assignment_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "operator_assignments.json"


def test_load_operator_assignments_returns_list():
    result = load_operator_assignments()
    assert isinstance(result, list)


def test_load_operator_assignments_returns_dataclass_instances():
    result = load_operator_assignments()
    assert all(isinstance(a, OperatorAssignment) for a in result)


def test_fixture_has_five_assignments():
    result = load_operator_assignments()
    assert len(result) == 5


def test_assignments_cover_all_three_tracks():
    result = load_operator_assignments()
    tracks = {a.track for a in result}
    assert "radio" in tracks
    assert "infrared" in tracks
    assert "anomaly" in tracks


def test_assignment_statuses_are_allowed():
    result = load_operator_assignments()
    for a in result:
        assert a.assignment_status in ALLOWED_ASSIGNMENT_STATUSES, (
            f"Unexpected status: {a.assignment_status}"
        )


def test_assignment_priorities_are_allowed():
    result = load_operator_assignments()
    for a in result:
        assert a.priority in ALLOWED_ASSIGNMENT_PRIORITIES, (
            f"Unexpected priority: {a.priority}"
        )


def test_as_dict_returns_expected_keys():
    assignment = load_operator_assignments()[0]
    d = assignment.as_dict()
    assert "assignment_id" in d
    assert "candidate_id" in d
    assert "track" in d
    assert "operator_id" in d
    assert "assignment_status" in d
    assert "priority" in d
    assert "assigned_utc" in d
    assert "due_utc" in d


def test_summary_schema_version():
    result = operator_assignment_summary()
    assert result["schema_version"] == OPERATOR_ASSIGNMENT_SCHEMA_VERSION


def test_summary_disclaimer():
    result = operator_assignment_summary()
    assert result["disclaimer"] == OPERATOR_ASSIGNMENT_DISCLAIMER
    assert "scheduling aids" in result["disclaimer"]


def test_summary_assignment_count():
    result = operator_assignment_summary()
    assert result["assignment_count"] == 5


def test_summary_unique_candidate_count():
    result = operator_assignment_summary()
    assert result["unique_candidate_count"] == 5


def test_summary_unique_operator_count():
    result = operator_assignment_summary()
    assert result["unique_operator_count"] == 2


def test_summary_pending_count():
    result = operator_assignment_summary()
    assert result["pending_count"] == 1


def test_summary_completed_count():
    result = operator_assignment_summary()
    assert result["completed_count"] == 1


def test_summary_escalated_count():
    result = operator_assignment_summary()
    assert result["escalated_count"] == 1


def test_summary_by_track():
    result = operator_assignment_summary()
    assert result["by_track"]["radio"] == 2
    assert result["by_track"]["infrared"] == 2
    assert result["by_track"]["anomaly"] == 1


def test_summary_by_status():
    result = operator_assignment_summary()
    assert "in_progress" in result["by_status"]
    assert "pending" in result["by_status"]
    assert "completed" in result["by_status"]
    assert "escalated" in result["by_status"]
    assert "deferred" in result["by_status"]


def test_summary_by_priority():
    result = operator_assignment_summary()
    assert "high" in result["by_priority"]
    assert "medium" in result["by_priority"]
    assert "low" in result["by_priority"]


def test_allowed_statuses_frozenset():
    assert "pending" in ALLOWED_ASSIGNMENT_STATUSES
    assert "escalated" in ALLOWED_ASSIGNMENT_STATUSES
    assert "completed" in ALLOWED_ASSIGNMENT_STATUSES


def test_allowed_priorities_frozenset():
    assert "high" in ALLOWED_ASSIGNMENT_PRIORITIES
    assert "medium" in ALLOWED_ASSIGNMENT_PRIORITIES
    assert "low" in ALLOWED_ASSIGNMENT_PRIORITIES


def test_cli_operator_assignment_summary_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "operator-assignment-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_operator_assignment_summary_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "operator-assignment-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "assignment_count" in data
    assert "tracks_covered" in data


def test_cli_operator_assignment_summary_with_fixture_path():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "techno_search.cli",
            "operator-assignment-summary",
            "--fixture-path",
            str(FIXTURE_PATH),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["assignment_count"] == 5
