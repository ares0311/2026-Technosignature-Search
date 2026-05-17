"""Tests for follow-up request module."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from techno_search.follow_up_request import (
    ALLOWED_REQUEST_PRIORITIES,
    ALLOWED_REQUEST_STATUSES,
    FOLLOW_UP_REQUEST_DISCLAIMER,
    FOLLOW_UP_REQUEST_SCHEMA_VERSION,
    FollowUpRequest,
    follow_up_request_summary,
    load_follow_up_requests,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "follow_up_requests.json"


def test_load_requests_returns_list():
    result = load_follow_up_requests()
    assert isinstance(result, list)


def test_load_requests_returns_dataclass_instances():
    result = load_follow_up_requests()
    assert all(isinstance(r, FollowUpRequest) for r in result)


def test_fixture_has_five_requests():
    result = load_follow_up_requests()
    assert len(result) == 5


def test_requests_cover_all_three_tracks():
    result = load_follow_up_requests()
    tracks = {r.track for r in result}
    assert "radio" in tracks
    assert "infrared" in tracks
    assert "anomaly" in tracks


def test_request_priorities_are_allowed():
    result = load_follow_up_requests()
    for r in result:
        assert r.priority in ALLOWED_REQUEST_PRIORITIES


def test_request_statuses_are_allowed():
    result = load_follow_up_requests()
    for r in result:
        assert r.status in ALLOWED_REQUEST_STATUSES


def test_days_open_non_negative():
    result = load_follow_up_requests()
    for r in result:
        assert r.days_open >= 0


def test_as_dict_returns_expected_keys():
    r = load_follow_up_requests()[0]
    d = r.as_dict()
    assert "request_id" in d
    assert "candidate_id" in d
    assert "track" in d
    assert "priority" in d
    assert "status" in d


def test_summary_returns_dict():
    result = follow_up_request_summary()
    assert isinstance(result, dict)


def test_summary_schema_version():
    result = follow_up_request_summary()
    assert result["schema_version"] == FOLLOW_UP_REQUEST_SCHEMA_VERSION


def test_summary_disclaimer():
    result = follow_up_request_summary()
    assert result["disclaimer"] == FOLLOW_UP_REQUEST_DISCLAIMER
    assert "scheduling coordination" in result["disclaimer"]


def test_summary_request_count():
    result = follow_up_request_summary()
    assert result["request_count"] == 5


def test_summary_open_count():
    result = follow_up_request_summary()
    # fur-001 in_progress, fur-002 open, fur-003 assigned = 3 open
    assert result["open_count"] == 3


def test_summary_urgent_count():
    result = follow_up_request_summary()
    # fur-001 is urgent
    assert result["urgent_count"] == 1


def test_summary_overdue_count():
    result = follow_up_request_summary()
    # fur-002 open 22d>14d, fur-005 deferred not open_status
    assert result["overdue_count"] >= 1


def test_summary_average_days_open():
    result = follow_up_request_summary()
    assert isinstance(result["average_days_open"], float)
    assert result["average_days_open"] >= 0.0


def test_summary_by_track():
    result = follow_up_request_summary()
    assert result["by_track"]["radio"] == 2
    assert result["by_track"]["infrared"] == 2
    assert result["by_track"]["anomaly"] == 1


def test_summary_tracks_covered():
    result = follow_up_request_summary()
    assert set(result["tracks_covered"]) == {"radio", "infrared", "anomaly"}


def test_summary_unique_requestors():
    result = follow_up_request_summary()
    assert result["unique_requestors"] >= 2


def test_allowed_priorities_frozenset():
    assert "low" in ALLOWED_REQUEST_PRIORITIES
    assert "normal" in ALLOWED_REQUEST_PRIORITIES
    assert "high" in ALLOWED_REQUEST_PRIORITIES
    assert "urgent" in ALLOWED_REQUEST_PRIORITIES


def test_allowed_statuses_frozenset():
    assert "open" in ALLOWED_REQUEST_STATUSES
    assert "completed" in ALLOWED_REQUEST_STATUSES
    assert "deferred" in ALLOWED_REQUEST_STATUSES


def test_cli_follow_up_request_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "follow-up-request-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_follow_up_request_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "follow-up-request-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "request_count" in data
    assert "open_count" in data
    assert "by_track" in data


def test_cli_follow_up_request_with_fixture_path():
    result = subprocess.run(
        [
            sys.executable, "-m", "techno_search.cli",
            "follow-up-request-summary",
            "--fixture-path", str(FIXTURE_PATH),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["request_count"] == 5
