"""Tests for pipeline audit summary module."""

from __future__ import annotations

import json
import subprocess
import sys

from techno_search.pipeline_audit_summary import (
    PIPELINE_AUDIT_DISCLAIMER,
    pipeline_audit_summary,
)


def test_pipeline_audit_summary_returns_dict():
    result = pipeline_audit_summary()
    assert isinstance(result, dict)


def test_pipeline_audit_disclaimer():
    result = pipeline_audit_summary()
    assert result["disclaimer"] == PIPELINE_AUDIT_DISCLAIMER
    assert "provenance records" in result["disclaimer"]


def test_total_audit_actions_non_negative():
    result = pipeline_audit_summary()
    assert isinstance(result["total_audit_actions"], int)
    assert result["total_audit_actions"] >= 0


def test_unique_candidates_audited_non_negative():
    result = pipeline_audit_summary()
    assert isinstance(result["unique_candidates_audited"], int)
    assert result["unique_candidates_audited"] >= 0


def test_unique_operators_non_negative():
    result = pipeline_audit_summary()
    assert isinstance(result["unique_operators"], int)
    assert result["unique_operators"] >= 0


def test_action_type_breakdown_is_dict():
    result = pipeline_audit_summary()
    assert isinstance(result["action_type_breakdown"], dict)


def test_track_breakdown_is_dict():
    result = pipeline_audit_summary()
    assert isinstance(result["track_breakdown"], dict)


def test_overall_audit_coverage_is_valid():
    result = pipeline_audit_summary()
    assert result["overall_audit_coverage"] in ("adequate", "sparse")


def test_total_actions_positive():
    result = pipeline_audit_summary()
    assert result["total_audit_actions"] > 0


def test_most_recent_action_utc_is_string():
    result = pipeline_audit_summary()
    assert isinstance(result["most_recent_action_utc"], str)


def test_cli_pipeline_audit_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "pipeline-audit-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_pipeline_audit_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "pipeline-audit-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "total_audit_actions" in data
    assert "overall_audit_coverage" in data
    assert "action_type_breakdown" in data
