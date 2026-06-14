"""Tests for review deadlines module."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from techno_search.review_deadlines import (
    ALLOWED_DEADLINE_STATUSES,
    ALLOWED_DEADLINE_TYPES,
    ALLOWED_DEADLINE_URGENCIES,
    REVIEW_DEADLINES_DISCLAIMER,
    REVIEW_DEADLINES_SCHEMA_VERSION,
    ReviewDeadline,
    load_review_deadlines,
    review_deadlines_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "review_deadlines.json"


def test_load_review_deadlines_returns_list():
    result = load_review_deadlines()
    assert isinstance(result, list)


def test_load_review_deadlines_returns_dataclass_instances():
    result = load_review_deadlines()
    assert all(isinstance(d, ReviewDeadline) for d in result)


def test_fixture_has_five_deadlines():
    result = load_review_deadlines()
    assert len(result) == 5


def test_deadlines_cover_all_three_tracks():
    result = load_review_deadlines()
    tracks = {d.track for d in result}
    assert "radio" in tracks
    assert "infrared" in tracks
    assert "anomaly" in tracks


def test_deadline_urgencies_are_allowed():
    result = load_review_deadlines()
    for d in result:
        assert d.urgency in ALLOWED_DEADLINE_URGENCIES, f"Unexpected urgency: {d.urgency}"


def test_deadline_types_are_allowed():
    result = load_review_deadlines()
    for d in result:
        assert d.deadline_type in ALLOWED_DEADLINE_TYPES, f"Unexpected type: {d.deadline_type}"


def test_deadline_statuses_are_allowed():
    result = load_review_deadlines()
    for d in result:
        assert d.status in ALLOWED_DEADLINE_STATUSES, f"Unexpected status: {d.status}"


def test_as_dict_returns_expected_keys():
    deadline = load_review_deadlines()[0]
    d = deadline.as_dict()
    assert "deadline_id" in d
    assert "candidate_id" in d
    assert "track" in d
    assert "operator_id" in d
    assert "deadline_type" in d
    assert "urgency" in d
    assert "due_utc" in d
    assert "status" in d


def test_summary_schema_version():
    result = review_deadlines_summary()
    assert result["schema_version"] == REVIEW_DEADLINES_SCHEMA_VERSION


def test_summary_disclaimer():
    result = review_deadlines_summary()
    assert result["disclaimer"] == REVIEW_DEADLINES_DISCLAIMER
    assert "scheduling aids" in result["disclaimer"]


def test_summary_deadline_count():
    result = review_deadlines_summary()
    assert result["deadline_count"] == 5


def test_summary_pending_count():
    result = review_deadlines_summary()
    assert result["pending_count"] == 2


def test_summary_overdue_count():
    result = review_deadlines_summary()
    assert result["overdue_count"] == 0


def test_summary_immediate_count():
    result = review_deadlines_summary()
    assert result["immediate_count"] == 1


def test_summary_by_track():
    result = review_deadlines_summary()
    assert result["by_track"]["radio"] == 2
    assert result["by_track"]["infrared"] == 2
    assert result["by_track"]["anomaly"] == 1


def test_summary_by_urgency():
    result = review_deadlines_summary()
    assert "high" in result["by_urgency"]
    assert "medium" in result["by_urgency"]
    assert "immediate" in result["by_urgency"]
    assert "low" in result["by_urgency"]


def test_summary_by_status():
    result = review_deadlines_summary()
    assert "in_progress" in result["by_status"]
    assert "pending" in result["by_status"]
    assert "completed" in result["by_status"]


def test_allowed_urgencies_frozenset():
    assert "immediate" in ALLOWED_DEADLINE_URGENCIES
    assert "low" in ALLOWED_DEADLINE_URGENCIES


def test_allowed_types_frozenset():
    assert "initial_review" in ALLOWED_DEADLINE_TYPES
    assert "escalation_review" in ALLOWED_DEADLINE_TYPES


def test_cli_review_deadlines_summary_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "review-deadlines-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_review_deadlines_summary_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "review-deadlines-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "deadline_count" in data
    assert "tracks_covered" in data


def test_cli_review_deadlines_summary_with_fixture_path():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "techno_search.cli",
            "review-deadlines-summary",
            "--fixture-path",
            str(FIXTURE_PATH),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["deadline_count"] == 5
