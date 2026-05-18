"""Tests for pipeline capacity module."""

from __future__ import annotations

import json
import subprocess
import sys

from techno_search.pipeline_capacity import (
    PIPELINE_CAPACITY_DISCLAIMER,
    pipeline_capacity_summary,
)


def test_pipeline_capacity_returns_dict():
    result = pipeline_capacity_summary()
    assert isinstance(result, dict)


def test_pipeline_capacity_disclaimer():
    result = pipeline_capacity_summary()
    assert result["disclaimer"] == PIPELINE_CAPACITY_DISCLAIMER
    assert "operational scheduling" in result["disclaimer"]


def test_open_assignment_count_non_negative():
    result = pipeline_capacity_summary()
    assert isinstance(result["open_assignment_count"], int)
    assert result["open_assignment_count"] >= 0


def test_open_request_count_non_negative():
    result = pipeline_capacity_summary()
    assert isinstance(result["open_request_count"], int)
    assert result["open_request_count"] >= 0


def test_unresolved_annotation_count_non_negative():
    result = pipeline_capacity_summary()
    assert isinstance(result["unresolved_annotation_count"], int)
    assert result["unresolved_annotation_count"] >= 0


def test_queue_depth_non_negative():
    result = pipeline_capacity_summary()
    assert isinstance(result["queue_depth"], int)
    assert result["queue_depth"] >= 0


def test_total_scheduling_load_non_negative():
    result = pipeline_capacity_summary()
    assert isinstance(result["total_scheduling_load"], int)
    assert result["total_scheduling_load"] >= 0


def test_capacity_status_is_valid():
    result = pipeline_capacity_summary()
    assert result["capacity_status"] in ("nominal", "strained", "overloaded")


def test_total_load_equals_sum_of_parts():
    result = pipeline_capacity_summary()
    expected = (
        result["open_assignment_count"]
        + result["open_request_count"]
        + result["queue_depth"]
    )
    assert result["total_scheduling_load"] == expected


def test_cli_pipeline_capacity_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "pipeline-capacity-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_pipeline_capacity_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "pipeline-capacity-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "queue_depth" in data
    assert "capacity_status" in data
    assert "total_scheduling_load" in data
