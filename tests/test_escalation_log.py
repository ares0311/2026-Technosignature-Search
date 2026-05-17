"""Tests for escalation log module."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from techno_search.escalation_log import (
    ALLOWED_ESCALATION_PRIORITIES,
    ALLOWED_ESCALATION_STATUSES,
    ESCALATION_LOG_DISCLAIMER,
    ESCALATION_LOG_SCHEMA_VERSION,
    EscalationEntry,
    escalation_log_summary,
    load_escalation_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "escalation_log.json"


def test_load_escalation_entries_returns_list():
    result = load_escalation_entries()
    assert isinstance(result, list)


def test_load_escalation_entries_returns_dataclass_instances():
    result = load_escalation_entries()
    assert all(isinstance(e, EscalationEntry) for e in result)


def test_fixture_has_five_entries():
    result = load_escalation_entries()
    assert len(result) == 5


def test_entries_cover_all_three_tracks():
    result = load_escalation_entries()
    tracks = {e.track for e in result}
    assert "radio" in tracks
    assert "infrared" in tracks
    assert "anomaly" in tracks


def test_priorities_are_allowed():
    result = load_escalation_entries()
    for e in result:
        assert e.priority in ALLOWED_ESCALATION_PRIORITIES


def test_statuses_are_allowed():
    result = load_escalation_entries()
    for e in result:
        assert e.status in ALLOWED_ESCALATION_STATUSES


def test_days_open_non_negative():
    result = load_escalation_entries()
    for e in result:
        assert e.days_open >= 0


def test_as_dict_returns_expected_keys():
    entry = load_escalation_entries()[0]
    d = entry.as_dict()
    assert "entry_id" in d
    assert "candidate_id" in d
    assert "track" in d
    assert "priority" in d
    assert "status" in d
    assert "days_open" in d


def test_summary_schema_version():
    result = escalation_log_summary()
    assert result["schema_version"] == ESCALATION_LOG_SCHEMA_VERSION


def test_summary_disclaimer():
    result = escalation_log_summary()
    assert result["disclaimer"] == ESCALATION_LOG_DISCLAIMER
    assert "operational urgency" in result["disclaimer"]


def test_summary_entry_count():
    result = escalation_log_summary()
    assert result["entry_count"] == 5


def test_summary_open_count():
    result = escalation_log_summary()
    # open + in_review = 3 (esc-001 open, esc-002 in_review, esc-003 open)
    assert result["open_count"] == 3


def test_summary_critical_count():
    result = escalation_log_summary()
    assert result["critical_count"] == 1


def test_summary_average_days_non_negative():
    result = escalation_log_summary()
    assert result["average_days_open"] >= 0


def test_summary_by_track():
    result = escalation_log_summary()
    assert result["by_track"]["radio"] == 2
    assert result["by_track"]["infrared"] == 2
    assert result["by_track"]["anomaly"] == 1


def test_summary_by_priority_present():
    result = escalation_log_summary()
    assert "high" in result["by_priority"]
    assert "critical" in result["by_priority"]


def test_summary_by_status_present():
    result = escalation_log_summary()
    assert "open" in result["by_status"]
    assert "resolved" in result["by_status"]


def test_summary_tracks_covered():
    result = escalation_log_summary()
    assert set(result["tracks_covered"]) == {"radio", "infrared", "anomaly"}


def test_allowed_priorities_frozenset():
    assert "low" in ALLOWED_ESCALATION_PRIORITIES
    assert "critical" in ALLOWED_ESCALATION_PRIORITIES
    assert "high" in ALLOWED_ESCALATION_PRIORITIES


def test_allowed_statuses_frozenset():
    assert "open" in ALLOWED_ESCALATION_STATUSES
    assert "resolved" in ALLOWED_ESCALATION_STATUSES
    assert "dismissed" in ALLOWED_ESCALATION_STATUSES


def test_cli_escalation_log_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "escalation-log-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_escalation_log_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "escalation-log-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "entry_count" in data
    assert "open_count" in data


def test_cli_escalation_log_with_fixture_path():
    result = subprocess.run(
        [
            sys.executable, "-m", "techno_search.cli",
            "escalation-log-summary",
            "--fixture-path", str(FIXTURE_PATH),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["entry_count"] == 5
