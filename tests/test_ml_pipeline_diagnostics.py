"""Tests for ML pipeline diagnostics module."""

from __future__ import annotations

import json
import subprocess
import sys

from techno_search.ml_pipeline_diagnostics import (
    ML_PIPELINE_DIAGNOSTICS_DISCLAIMER,
    ml_pipeline_diagnostics_summary,
)

VALID_PIPELINE_STATUSES = {"no_models", "all_above_baseline", "some_below_baseline"}


def test_summary_returns_dict():
    result = ml_pipeline_diagnostics_summary()
    assert isinstance(result, dict)


def test_summary_disclaimer():
    result = ml_pipeline_diagnostics_summary()
    assert result["disclaimer"] == ML_PIPELINE_DIAGNOSTICS_DISCLAIMER
    assert "scheduling summaries" in result["disclaimer"]


def test_baseline_accuracy_non_negative():
    result = ml_pipeline_diagnostics_summary()
    assert isinstance(result["baseline_accuracy"], float)
    assert result["baseline_accuracy"] >= 0.0


def test_registered_model_count_non_negative():
    result = ml_pipeline_diagnostics_summary()
    assert isinstance(result["registered_model_count"], int)
    assert result["registered_model_count"] >= 0


def test_above_baseline_count_non_negative():
    result = ml_pipeline_diagnostics_summary()
    assert isinstance(result["above_baseline_count"], int)
    assert result["above_baseline_count"] >= 0


def test_below_baseline_count_non_negative():
    result = ml_pipeline_diagnostics_summary()
    assert isinstance(result["below_baseline_count"], int)
    assert result["below_baseline_count"] >= 0


def test_validated_model_count_non_negative():
    result = ml_pipeline_diagnostics_summary()
    assert isinstance(result["validated_model_count"], int)
    assert result["validated_model_count"] >= 0


def test_pipeline_ml_status_is_valid():
    result = ml_pipeline_diagnostics_summary()
    assert result["pipeline_ml_status"] in VALID_PIPELINE_STATUSES


def test_above_plus_below_equals_total():
    result = ml_pipeline_diagnostics_summary()
    assert (
        result["above_baseline_count"] + result["below_baseline_count"]
        == result["registered_model_count"]
    )


def test_fixture_has_below_baseline_model():
    result = ml_pipeline_diagnostics_summary()
    # mdl-003 cnn_radio_v0_draft is below baseline
    assert result["below_baseline_count"] >= 1
    assert result["pipeline_ml_status"] == "some_below_baseline"


def test_cli_ml_diagnostics_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "ml-diagnostics-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_ml_diagnostics_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "ml-diagnostics-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "baseline_accuracy" in data
    assert "pipeline_ml_status" in data
    assert "registered_model_count" in data
