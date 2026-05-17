"""Tests for pipeline bottleneck module."""

from __future__ import annotations

import json
import subprocess
import sys

from techno_search.pipeline_bottleneck import (
    PIPELINE_BOTTLENECK_DISCLAIMER,
    pipeline_bottleneck_summary,
)


def test_pipeline_bottleneck_returns_dict():
    result = pipeline_bottleneck_summary()
    assert isinstance(result, dict)


def test_pipeline_bottleneck_disclaimer():
    result = pipeline_bottleneck_summary()
    assert result["disclaimer"] == PIPELINE_BOTTLENECK_DISCLAIMER
    assert "operational dashboard" in result["disclaimer"]


def test_total_stalled_non_negative():
    result = pipeline_bottleneck_summary()
    assert isinstance(result["total_stalled_candidates"], int)
    assert result["total_stalled_candidates"] >= 0


def test_overdue_review_count_non_negative():
    result = pipeline_bottleneck_summary()
    assert isinstance(result["overdue_review_count"], int)
    assert result["overdue_review_count"] >= 0


def test_unassigned_candidate_count_non_negative():
    result = pipeline_bottleneck_summary()
    assert isinstance(result["unassigned_candidate_count"], int)
    assert result["unassigned_candidate_count"] >= 0


def test_critical_blocker_count_non_negative():
    result = pipeline_bottleneck_summary()
    assert isinstance(result["critical_blocker_count"], int)
    assert result["critical_blocker_count"] >= 0


def test_open_escalation_count_non_negative():
    result = pipeline_bottleneck_summary()
    assert isinstance(result["open_escalation_count"], int)
    assert result["open_escalation_count"] >= 0


def test_bottleneck_stages_is_dict():
    result = pipeline_bottleneck_summary()
    assert isinstance(result["bottleneck_stages"], dict)


def test_top_bottleneck_stage_is_string():
    result = pipeline_bottleneck_summary()
    assert isinstance(result["top_bottleneck_stage"], str)
    assert len(result["top_bottleneck_stage"]) > 0


def test_per_track_stall_counts_is_dict():
    result = pipeline_bottleneck_summary()
    assert isinstance(result["per_track_stall_counts"], dict)


def test_cli_pipeline_bottleneck_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "pipeline-bottleneck-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_pipeline_bottleneck_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "pipeline-bottleneck-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "total_stalled_candidates" in data
    assert "top_bottleneck_stage" in data
    assert "bottleneck_stages" in data
