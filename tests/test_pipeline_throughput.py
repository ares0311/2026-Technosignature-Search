"""Tests for pipeline throughput module."""

from __future__ import annotations

import json
import subprocess
import sys

from techno_search.pipeline_throughput import (
    PIPELINE_STAGES,
    PIPELINE_THROUGHPUT_DISCLAIMER,
    pipeline_throughput_summary,
)


def test_pipeline_throughput_returns_dict():
    result = pipeline_throughput_summary()
    assert isinstance(result, dict)


def test_pipeline_throughput_disclaimer():
    result = pipeline_throughput_summary()
    assert result["disclaimer"] == PIPELINE_THROUGHPUT_DISCLAIMER
    assert "local operational metrics" in result["disclaimer"]


def test_pipeline_stages_constant():
    assert "scored" in PIPELINE_STAGES
    assert "human_review" in PIPELINE_STAGES
    assert "archived" in PIPELINE_STAGES


def test_stage_counts_present():
    result = pipeline_throughput_summary()
    assert "stage_counts" in result
    for stage in PIPELINE_STAGES:
        assert stage in result["stage_counts"]


def test_stage_counts_non_negative():
    result = pipeline_throughput_summary()
    for count in result["stage_counts"].values():
        assert isinstance(count, int)
        assert count >= 0


def test_by_track_has_all_tracks():
    result = pipeline_throughput_summary()
    assert "radio" in result["by_track"]
    assert "infrared" in result["by_track"]
    assert "anomaly" in result["by_track"]


def test_by_track_has_all_stages():
    result = pipeline_throughput_summary()
    for track_data in result["by_track"].values():
        for stage in PIPELINE_STAGES:
            assert stage in track_data


def test_throughput_rate_in_range():
    result = pipeline_throughput_summary()
    assert 0.0 <= result["throughput_rate"] <= 1.0


def test_total_lifecycle_entries_present():
    result = pipeline_throughput_summary()
    assert "total_lifecycle_entries" in result
    assert isinstance(result["total_lifecycle_entries"], int)
    assert result["total_lifecycle_entries"] > 0


def test_triage_counts_present():
    result = pipeline_throughput_summary()
    assert "total_triage_notes" in result
    assert "triage_cleared_count" in result
    assert "triage_blocked_count" in result


def test_lifecycle_cleared_plus_blocked_equals_total():
    result = pipeline_throughput_summary()
    assert (
        result["lifecycle_cleared_count"] + result["lifecycle_blocked_count"]
        == result["total_lifecycle_entries"]
    )


def test_cli_pipeline_throughput_summary_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "pipeline-throughput-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_pipeline_throughput_summary_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "pipeline-throughput-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "stage_counts" in data
    assert "throughput_rate" in data
