"""Tests for lifecycle transition validation and observation efficiency."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_lifecycle_transition_summary_keys() -> None:
    from techno_search.candidate_lifecycle import lifecycle_transition_summary

    result = lifecycle_transition_summary()
    assert "total_entry_count" in result
    assert "unique_candidate_count" in result
    assert "candidates_with_multiple_entries" in result
    assert "invalid_transition_count" in result
    assert "candidates_with_invalid_transitions" in result
    assert "invalid_transitions" in result
    assert "all_transitions_valid" in result


def test_lifecycle_transition_summary_schema_version() -> None:
    from techno_search.candidate_lifecycle import (
        CANDIDATE_LIFECYCLE_SCHEMA_VERSION,
        lifecycle_transition_summary,
    )

    result = lifecycle_transition_summary()
    assert result["schema_version"] == CANDIDATE_LIFECYCLE_SCHEMA_VERSION


def test_lifecycle_transition_summary_disclaimer() -> None:
    from techno_search.candidate_lifecycle import lifecycle_transition_summary

    result = lifecycle_transition_summary()
    assert "disclaimer" in result
    assert len(str(result["disclaimer"])) > 10


def test_lifecycle_transition_counts_non_negative() -> None:
    from techno_search.candidate_lifecycle import lifecycle_transition_summary

    result = lifecycle_transition_summary()
    assert isinstance(result["total_entry_count"], int)
    assert result["total_entry_count"] >= 0
    assert isinstance(result["invalid_transition_count"], int)
    assert result["invalid_transition_count"] >= 0
    assert isinstance(result["unique_candidate_count"], int)
    assert result["unique_candidate_count"] >= 0


def test_lifecycle_fixture_has_no_invalid_transitions() -> None:
    from techno_search.candidate_lifecycle import lifecycle_transition_summary

    result = lifecycle_transition_summary()
    assert result["all_transitions_valid"] is True
    assert result["invalid_transition_count"] == 0


def test_lifecycle_transition_detects_invalid_ordering(tmp_path: Path) -> None:
    from techno_search.candidate_lifecycle import lifecycle_transition_summary

    bad_fixture = {
        "schema_version": "candidate_lifecycle_v1",
        "disclaimer": "test",
        "entries": [
            {
                "candidate_id": "test-001",
                "track": "radio",
                "stage": "scored",
                "stage_entered_utc": "2026-01-02T00:00:00Z",
                "pathway": "human_review_queue",
            },
            {
                "candidate_id": "test-001",
                "track": "radio",
                "stage": "initial_detection",
                "stage_entered_utc": "2026-01-03T00:00:00Z",
                "pathway": "human_review_queue",
            },
        ],
    }
    fixture_path = tmp_path / "bad_lifecycle.json"
    fixture_path.write_text(json.dumps(bad_fixture))

    result = lifecycle_transition_summary(fixture_path=fixture_path)
    assert result["invalid_transition_count"] == 1
    assert result["all_transitions_valid"] is False
    assert len(result["invalid_transitions"]) == 1
    assert result["invalid_transitions"][0]["candidate_id"] == "test-001"


def test_lifecycle_transition_multiple_candidates() -> None:
    from techno_search.candidate_lifecycle import lifecycle_transition_summary

    result = lifecycle_transition_summary()
    assert result["unique_candidate_count"] >= 1


def test_lifecycle_transition_cli_exits_zero() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "lifecycle-transition-summary"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    parsed = json.loads(proc.stdout)
    assert "invalid_transition_count" in parsed
    assert "all_transitions_valid" in parsed


def test_observation_efficiency_summary_keys() -> None:
    from techno_search.observation_schedule import observation_efficiency_summary

    result = observation_efficiency_summary()
    assert "window_count" in result
    assert "completed_count" in result
    assert "cancelled_count" in result
    assert "planned_count" in result
    assert "completion_rate" in result
    assert "cancellation_rate" in result
    assert "total_scheduled_hours" in result
    assert "completed_hours" in result
    assert "by_track_stats" in result
    assert "by_track_completion_rate" in result


def test_observation_efficiency_rates_in_range() -> None:
    from techno_search.observation_schedule import observation_efficiency_summary

    result = observation_efficiency_summary()
    assert 0.0 <= result["completion_rate"] <= 1.0
    assert 0.0 <= result["cancellation_rate"] <= 1.0


def test_observation_efficiency_hours_positive() -> None:
    from techno_search.observation_schedule import observation_efficiency_summary

    result = observation_efficiency_summary()
    assert result["total_scheduled_hours"] >= 0.0
    assert result["completed_hours"] >= 0.0
    assert result["completed_hours"] <= result["total_scheduled_hours"]


def test_observation_efficiency_by_track_completion_in_range() -> None:
    from techno_search.observation_schedule import observation_efficiency_summary

    result = observation_efficiency_summary()
    for track, rate in result["by_track_completion_rate"].items():
        assert 0.0 <= rate <= 1.0, f"Track {track} completion rate out of range: {rate}"


def test_observation_efficiency_counts_sum_correctly() -> None:
    from techno_search.observation_schedule import observation_efficiency_summary

    result = observation_efficiency_summary()
    total = result["window_count"]
    parts = result["completed_count"] + result["cancelled_count"] + result["planned_count"]
    assert parts == total


def test_observation_efficiency_disclaimer_present() -> None:
    from techno_search.observation_schedule import (
        OBSERVATION_SCHEDULE_DISCLAIMER,
        observation_efficiency_summary,
    )

    result = observation_efficiency_summary()
    assert result["disclaimer"] == OBSERVATION_SCHEDULE_DISCLAIMER


def test_observation_efficiency_cli_exits_zero() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "observation-efficiency-summary"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    parsed = json.loads(proc.stdout)
    assert "completion_rate" in parsed
    assert "window_count" in parsed
