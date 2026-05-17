"""Tests for track comparison module."""

from __future__ import annotations

import json
import subprocess
import sys

from techno_search.track_comparison import (
    COMPARISON_TRACKS,
    TRACK_COMPARISON_DISCLAIMER,
    track_comparison_summary,
)

REQUIRED_PER_TRACK_KEYS = {
    "triage_count",
    "triage_blocked",
    "lifecycle_count",
    "lifecycle_blocked",
    "open_flags",
    "critical_flags",
    "pending_deadlines",
    "overdue_deadlines",
    "pending_epoch_requests",
    "observation_follow_up",
}


def test_track_comparison_returns_dict():
    result = track_comparison_summary()
    assert isinstance(result, dict)


def test_track_comparison_disclaimer():
    result = track_comparison_summary()
    assert result["disclaimer"] == TRACK_COMPARISON_DISCLAIMER
    assert "local operational" in result["disclaimer"]


def test_comparison_tracks_constant():
    assert "radio" in COMPARISON_TRACKS
    assert "infrared" in COMPARISON_TRACKS
    assert "anomaly" in COMPARISON_TRACKS


def test_per_track_has_all_tracks():
    result = track_comparison_summary()
    for track in COMPARISON_TRACKS:
        assert track in result["per_track"]


def test_per_track_has_required_keys():
    result = track_comparison_summary()
    for track in COMPARISON_TRACKS:
        assert result["per_track"][track].keys() >= REQUIRED_PER_TRACK_KEYS


def test_per_track_counts_non_negative():
    result = track_comparison_summary()
    for track_data in result["per_track"].values():
        for val in track_data.values():
            assert isinstance(val, int)
            assert val >= 0


def test_total_open_flags_present():
    result = track_comparison_summary()
    assert "total_open_flags" in result
    assert isinstance(result["total_open_flags"], int)
    assert result["total_open_flags"] >= 0


def test_total_overdue_deadlines_present():
    result = track_comparison_summary()
    assert "total_overdue_deadlines" in result
    assert isinstance(result["total_overdue_deadlines"], int)


def test_total_open_flags_equals_sum_of_per_track():
    result = track_comparison_summary()
    expected = sum(v["open_flags"] for v in result["per_track"].values())
    assert result["total_open_flags"] == expected


def test_triage_counts_match_fixtures():
    result = track_comparison_summary()
    # All 3 tracks have triage data
    total_triage = sum(v["triage_count"] for v in result["per_track"].values())
    assert total_triage > 0


def test_cli_track_comparison_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "track-comparison-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_track_comparison_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "track-comparison-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "per_track" in data
    assert "total_open_flags" in data


def test_cli_track_comparison_has_all_tracks():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "track-comparison-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "radio" in data["per_track"]
    assert "infrared" in data["per_track"]
    assert "anomaly" in data["per_track"]
