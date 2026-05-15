"""Tests for false-negative summary from injection-recovery fixture."""

from __future__ import annotations

import json
from io import StringIO

from techno_search.cli import main
from techno_search.injection_recovery import (
    INJECTION_RECOVERY_DISCLAIMER,
    false_negative_summary,
)


def test_false_negative_summary_keys_present():
    summary = false_negative_summary()
    for key in (
        "total_injected_cases",
        "missed_count",
        "false_alarm_count",
        "synthetic_missed_injection_rate",
        "by_track_missed_count",
        "by_track_missed_rate",
        "by_injection_type_missed",
        "missed_case_ids",
    ):
        assert key in summary, f"Missing key: {key}"


def test_false_negative_summary_counts_non_negative():
    summary = false_negative_summary()
    assert summary["total_injected_cases"] >= 0
    assert summary["missed_count"] >= 0
    assert summary["false_alarm_count"] >= 0


def test_false_negative_summary_rate_in_range():
    summary = false_negative_summary()
    rate = summary["synthetic_missed_injection_rate"]
    assert 0.0 <= float(rate) <= 1.0


def test_false_negative_summary_track_rates_in_range():
    summary = false_negative_summary()
    for track, rate in summary["by_track_missed_rate"].items():
        assert 0.0 <= float(rate) <= 1.0, f"Track {track} missed rate out of range: {rate}"


def test_false_negative_summary_total_injected_consistent():
    summary = false_negative_summary()
    total = summary["total_injected_cases"]
    missed = summary["missed_count"]
    assert missed <= total


def test_false_negative_summary_disclaimer():
    summary = false_negative_summary()
    assert INJECTION_RECOVERY_DISCLAIMER in str(summary["disclaimer"])


def test_false_negative_summary_missed_rate_below_one():
    """At least one injection should be recovered — missed rate must be < 1.0."""
    summary = false_negative_summary()
    assert float(summary["synthetic_missed_injection_rate"]) < 1.0


def test_cli_false_negative_summary_exit_zero():
    out = StringIO()
    ret = main(["false-negative-summary"], stdout=out)
    assert ret == 0
    data = json.loads(out.getvalue())
    assert "total_injected_cases" in data
    assert "missed_count" in data


def test_cli_false_negative_summary_disclaimer():
    out = StringIO()
    main(["false-negative-summary"], stdout=out)
    data = json.loads(out.getvalue())
    assert INJECTION_RECOVERY_DISCLAIMER in data["disclaimer"]
