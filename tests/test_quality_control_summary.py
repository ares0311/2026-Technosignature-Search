"""Tests for quality control summary module."""

from __future__ import annotations

import json
import subprocess
import sys

from techno_search.quality_control_summary import (
    QUALITY_CONTROL_DISCLAIMER,
    quality_control_summary,
)


def test_quality_control_summary_returns_dict():
    result = quality_control_summary()
    assert isinstance(result, dict)


def test_quality_control_disclaimer():
    result = quality_control_summary()
    assert result["disclaimer"] == QUALITY_CONTROL_DISCLAIMER
    assert "operational dashboards" in result["disclaimer"]


def test_total_open_flags_non_negative():
    result = quality_control_summary()
    assert isinstance(result["total_open_flags"], int)
    assert result["total_open_flags"] >= 0


def test_critical_flag_count_non_negative():
    result = quality_control_summary()
    assert isinstance(result["critical_flag_count"], int)
    assert result["critical_flag_count"] >= 0


def test_triage_clearance_rate_in_range():
    result = quality_control_summary()
    assert 0.0 <= result["triage_clearance_rate"] <= 1.0


def test_overdue_deadline_count_non_negative():
    result = quality_control_summary()
    assert isinstance(result["overdue_deadline_count"], int)
    assert result["overdue_deadline_count"] >= 0


def test_deadline_compliance_rate_in_range():
    result = quality_control_summary()
    assert 0.0 <= result["deadline_compliance_rate"] <= 1.0


def test_active_candidate_count_non_negative():
    result = quality_control_summary()
    assert isinstance(result["active_candidate_count"], int)
    assert result["active_candidate_count"] >= 0


def test_resolved_count_non_negative():
    result = quality_control_summary()
    assert isinstance(result["resolved_count"], int)
    assert result["resolved_count"] >= 0


def test_open_escalation_count_non_negative():
    result = quality_control_summary()
    assert isinstance(result["open_escalation_count"], int)
    assert result["open_escalation_count"] >= 0


def test_overall_qc_health_is_valid():
    result = quality_control_summary()
    assert result["overall_qc_health"] in ("ok", "degraded", "blocked")


def test_cli_quality_control_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "quality-control-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_quality_control_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "quality-control-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "overall_qc_health" in data
    assert "total_open_flags" in data
    assert "triage_clearance_rate" in data
