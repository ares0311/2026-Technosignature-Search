"""Tests for pipeline health summary module."""

from __future__ import annotations

import json
import subprocess
import sys

from techno_search.pipeline_health import (
    PIPELINE_HEALTH_DISCLAIMER,
    PIPELINE_HEALTH_TRACKS,
    pipeline_health_summary,
)


def test_pipeline_health_returns_dict():
    result = pipeline_health_summary()
    assert isinstance(result, dict)


def test_pipeline_health_disclaimer():
    result = pipeline_health_summary()
    assert result["disclaimer"] == PIPELINE_HEALTH_DISCLAIMER
    assert "operational dashboards" in result["disclaimer"]


def test_pipeline_health_tracks_constant():
    assert "radio" in PIPELINE_HEALTH_TRACKS
    assert "infrared" in PIPELINE_HEALTH_TRACKS
    assert "anomaly" in PIPELINE_HEALTH_TRACKS


def test_pipeline_health_has_per_track():
    result = pipeline_health_summary()
    assert "per_track" in result
    assert "radio" in result["per_track"]
    assert "infrared" in result["per_track"]
    assert "anomaly" in result["per_track"]


def test_per_track_has_required_keys():
    result = pipeline_health_summary()
    required = {
        "triage_count",
        "triage_blocked_count",
        "lifecycle_count",
        "lifecycle_blocked_count",
        "pending_assignments",
        "escalated_assignments",
        "pending_epoch_requests",
        "observation_follow_up_recommended",
    }
    for track in PIPELINE_HEALTH_TRACKS:
        assert required <= result["per_track"][track].keys()


def test_per_track_counts_are_non_negative():
    result = pipeline_health_summary()
    for track_data in result["per_track"].values():
        for val in track_data.values():
            assert isinstance(val, int)
            assert val >= 0


def test_total_blocked_count_present():
    result = pipeline_health_summary()
    assert "total_blocked_count" in result
    assert isinstance(result["total_blocked_count"], int)
    assert result["total_blocked_count"] >= 0


def test_total_escalated_count_present():
    result = pipeline_health_summary()
    assert "total_escalated_count" in result
    assert isinstance(result["total_escalated_count"], int)


def test_total_blocked_equals_sum_of_per_track():
    result = pipeline_health_summary()
    expected = sum(
        v["triage_blocked_count"] + v["lifecycle_blocked_count"]
        for v in result["per_track"].values()
    )
    assert result["total_blocked_count"] == expected


def test_cli_pipeline_health_summary_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "pipeline-health-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_pipeline_health_summary_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "pipeline-health-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "per_track" in data
    assert "total_blocked_count" in data


def test_cli_pipeline_health_summary_has_all_tracks():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "pipeline-health-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "radio" in data["per_track"]
    assert "infrared" in data["per_track"]
    assert "anomaly" in data["per_track"]
