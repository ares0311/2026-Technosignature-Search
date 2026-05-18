"""Tests for candidate priority queue module."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from techno_search.candidate_priority_queue import (
    ALLOWED_QUEUE_REASONS,
    CANDIDATE_PRIORITY_QUEUE_DISCLAIMER,
    CANDIDATE_PRIORITY_QUEUE_SCHEMA_VERSION,
    CandidatePriorityQueueEntry,
    load_priority_queue_entries,
    priority_queue_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "candidate_priority_queue.json"


def test_load_entries_returns_list():
    result = load_priority_queue_entries()
    assert isinstance(result, list)


def test_load_entries_returns_dataclass_instances():
    result = load_priority_queue_entries()
    assert all(isinstance(e, CandidatePriorityQueueEntry) for e in result)


def test_fixture_has_five_entries():
    result = load_priority_queue_entries()
    assert len(result) == 5


def test_entries_cover_all_three_tracks():
    result = load_priority_queue_entries()
    tracks = {e.track for e in result}
    assert "radio" in tracks
    assert "infrared" in tracks
    assert "anomaly" in tracks


def test_queue_reasons_are_allowed():
    result = load_priority_queue_entries()
    for e in result:
        assert e.queue_reason in ALLOWED_QUEUE_REASONS


def test_queue_position_positive():
    result = load_priority_queue_entries()
    for e in result:
        assert e.queue_position >= 1


def test_days_in_queue_non_negative():
    result = load_priority_queue_entries()
    for e in result:
        assert e.days_in_queue >= 0


def test_as_dict_returns_expected_keys():
    e = load_priority_queue_entries()[0]
    d = e.as_dict()
    assert "queue_id" in d
    assert "candidate_id" in d
    assert "track" in d
    assert "queue_reason" in d
    assert "queue_position" in d


def test_summary_returns_dict():
    result = priority_queue_summary()
    assert isinstance(result, dict)


def test_summary_schema_version():
    result = priority_queue_summary()
    assert result["schema_version"] == CANDIDATE_PRIORITY_QUEUE_SCHEMA_VERSION


def test_summary_disclaimer():
    result = priority_queue_summary()
    assert result["disclaimer"] == CANDIDATE_PRIORITY_QUEUE_DISCLAIMER
    assert "scheduling aids" in result["disclaimer"]


def test_summary_queue_depth():
    result = priority_queue_summary()
    assert result["queue_depth"] == 5


def test_summary_average_days_in_queue():
    result = priority_queue_summary()
    assert isinstance(result["average_days_in_queue"], float)
    assert result["average_days_in_queue"] >= 0.0


def test_summary_max_days_in_queue():
    result = priority_queue_summary()
    # q-002 has 22 days
    assert result["max_days_in_queue"] == 22


def test_summary_by_track():
    result = priority_queue_summary()
    assert result["by_track"]["radio"] == 2
    assert result["by_track"]["infrared"] == 2
    assert result["by_track"]["anomaly"] == 1


def test_summary_tracks_covered():
    result = priority_queue_summary()
    assert set(result["tracks_covered"]) == {"radio", "infrared", "anomaly"}


def test_allowed_queue_reasons_frozenset():
    assert "score_threshold" in ALLOWED_QUEUE_REASONS
    assert "flag_escalation" in ALLOWED_QUEUE_REASONS
    assert "deadline_pressure" in ALLOWED_QUEUE_REASONS
    assert "operator_request" in ALLOWED_QUEUE_REASONS
    assert "routine_review" in ALLOWED_QUEUE_REASONS


def test_cli_priority_queue_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "priority-queue-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_priority_queue_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "priority-queue-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "queue_depth" in data
    assert "max_days_in_queue" in data
    assert "by_track" in data


def test_cli_priority_queue_with_fixture_path():
    result = subprocess.run(
        [
            sys.executable, "-m", "techno_search.cli",
            "priority-queue-summary",
            "--fixture-path", str(FIXTURE_PATH),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["queue_depth"] == 5
