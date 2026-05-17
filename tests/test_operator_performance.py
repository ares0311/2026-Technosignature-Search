"""Tests for operator performance module."""

from __future__ import annotations

import json
import subprocess
import sys

from techno_search.operator_performance import (
    OPERATOR_PERFORMANCE_DISCLAIMER,
    operator_performance_summary,
)


def test_operator_performance_returns_dict():
    result = operator_performance_summary()
    assert isinstance(result, dict)


def test_operator_performance_disclaimer():
    result = operator_performance_summary()
    assert result["disclaimer"] == OPERATOR_PERFORMANCE_DISCLAIMER
    assert "scheduling and workflow" in result["disclaimer"]


def test_operator_count():
    result = operator_performance_summary()
    assert result["operator_count"] == 2


def test_total_assignments():
    result = operator_performance_summary()
    assert result["total_assignments"] == 5


def test_total_completed():
    result = operator_performance_summary()
    assert result["total_completed"] == 1


def test_total_escalated():
    result = operator_performance_summary()
    assert result["total_escalated"] == 1


def test_overall_completion_rate_in_range():
    result = operator_performance_summary()
    assert 0.0 <= result["overall_completion_rate"] <= 1.0


def test_per_operator_is_list():
    result = operator_performance_summary()
    assert isinstance(result["per_operator"], list)
    assert len(result["per_operator"]) == 2


def test_per_operator_has_required_keys():
    result = operator_performance_summary()
    required = {
        "operator_id", "total_assigned", "completed", "escalated",
        "deferred", "pending", "in_progress", "completion_rate",
        "escalation_rate", "tracks_covered",
    }
    for op in result["per_operator"]:
        assert required <= op.keys()


def test_per_operator_rates_in_range():
    result = operator_performance_summary()
    for op in result["per_operator"]:
        assert 0.0 <= op["completion_rate"] <= 1.0
        assert 0.0 <= op["escalation_rate"] <= 1.0


def test_per_operator_tracks_covered():
    result = operator_performance_summary()
    all_tracks = set()
    for op in result["per_operator"]:
        all_tracks.update(op["tracks_covered"])
    assert "radio" in all_tracks
    assert "infrared" in all_tracks


def test_cli_operator_performance_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "operator-performance-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_operator_performance_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "operator-performance-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "operator_count" in data
    assert "overall_completion_rate" in data
    assert "per_operator" in data
