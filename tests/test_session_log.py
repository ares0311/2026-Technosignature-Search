"""Tests for session log module."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from techno_search.session_log import (
    ALLOWED_SESSION_OUTCOMES,
    SESSION_LOG_DISCLAIMER,
    SESSION_LOG_SCHEMA_VERSION,
    SessionLogEntry,
    load_session_log_entries,
    session_log_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "session_log.json"


def test_load_entries_returns_list():
    result = load_session_log_entries()
    assert isinstance(result, list)


def test_load_entries_returns_dataclass_instances():
    result = load_session_log_entries()
    assert all(isinstance(e, SessionLogEntry) for e in result)


def test_fixture_has_five_sessions():
    result = load_session_log_entries()
    assert len(result) == 5


def test_sessions_cover_all_three_tracks():
    result = load_session_log_entries()
    tracks = {e.track for e in result}
    assert "radio" in tracks
    assert "infrared" in tracks
    assert "anomaly" in tracks


def test_session_outcomes_are_allowed():
    result = load_session_log_entries()
    for e in result:
        assert e.outcome in ALLOWED_SESSION_OUTCOMES


def test_duration_minutes_non_negative():
    result = load_session_log_entries()
    for e in result:
        assert e.duration_minutes >= 0


def test_candidates_observed_is_list():
    result = load_session_log_entries()
    for e in result:
        assert isinstance(e.candidates_observed, list)


def test_as_dict_returns_expected_keys():
    e = load_session_log_entries()[0]
    d = e.as_dict()
    assert "session_id" in d
    assert "campaign_id" in d
    assert "track" in d
    assert "outcome" in d
    assert "candidates_observed" in d


def test_summary_returns_dict():
    result = session_log_summary()
    assert isinstance(result, dict)


def test_summary_schema_version():
    result = session_log_summary()
    assert result["schema_version"] == SESSION_LOG_SCHEMA_VERSION


def test_summary_disclaimer():
    result = session_log_summary()
    assert result["disclaimer"] == SESSION_LOG_DISCLAIMER
    assert "provenance records" in result["disclaimer"]


def test_summary_session_count():
    result = session_log_summary()
    assert result["session_count"] == 5


def test_summary_completed_count():
    result = session_log_summary()
    # sess-001, sess-003, sess-005 completed
    assert result["completed_count"] == 3


def test_summary_aborted_count():
    result = session_log_summary()
    # sess-004 aborted
    assert result["aborted_count"] == 1


def test_summary_total_duration():
    result = session_log_summary()
    # 120+90+180+0+150 = 540
    assert result["total_duration_minutes"] == 540


def test_summary_average_duration():
    result = session_log_summary()
    assert isinstance(result["average_duration_minutes"], float)
    assert result["average_duration_minutes"] >= 0.0


def test_summary_by_track():
    result = session_log_summary()
    assert result["by_track"]["radio"] == 2
    assert result["by_track"]["infrared"] == 2
    assert result["by_track"]["anomaly"] == 1


def test_summary_tracks_covered():
    result = session_log_summary()
    assert set(result["tracks_covered"]) == {"radio", "infrared", "anomaly"}


def test_summary_unique_candidates_observed():
    result = session_log_summary()
    assert result["unique_candidates_observed"] >= 1


def test_allowed_outcomes_frozenset():
    assert "completed" in ALLOWED_SESSION_OUTCOMES
    assert "aborted" in ALLOWED_SESSION_OUTCOMES
    assert "partial" in ALLOWED_SESSION_OUTCOMES
    assert "rescheduled" in ALLOWED_SESSION_OUTCOMES
    assert "failed" in ALLOWED_SESSION_OUTCOMES


def test_cli_session_log_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "session-log-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_session_log_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "session-log-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "session_count" in data
    assert "completed_count" in data
    assert "by_track" in data


def test_cli_session_log_with_fixture_path():
    result = subprocess.run(
        [
            sys.executable, "-m", "techno_search.cli",
            "session-log-summary",
            "--fixture-path", str(FIXTURE_PATH),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["session_count"] == 5
