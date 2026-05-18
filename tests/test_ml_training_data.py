"""Tests for ML training data scaffold module."""

from __future__ import annotations

import json
import subprocess
import sys

from techno_search.ml_training_data import (
    ML_TRAINING_DATA_DISCLAIMER,
    ml_training_data_summary,
)


def test_summary_returns_dict():
    result = ml_training_data_summary()
    assert isinstance(result, dict)


def test_summary_disclaimer():
    result = ml_training_data_summary()
    assert result["disclaimer"] == ML_TRAINING_DATA_DISCLAIMER
    assert "provenance records" in result["disclaimer"]


def test_total_case_count_non_negative():
    result = ml_training_data_summary()
    assert isinstance(result["total_case_count"], int)
    assert result["total_case_count"] >= 0


def test_calibration_and_injection_sum_to_total():
    result = ml_training_data_summary()
    assert (
        result["calibration_case_count"] + result["injection_recovery_case_count"]
        == result["total_case_count"]
    )


def test_train_and_test_sum_to_total():
    result = ml_training_data_summary()
    assert (
        result["recommended_train_count"] + result["recommended_test_count"]
        == result["total_case_count"]
    )


def test_by_track_covers_three_tracks():
    result = ml_training_data_summary()
    assert "radio" in result["by_track"]
    assert "infrared" in result["by_track"]
    assert "anomaly" in result["by_track"]


def test_by_source_keys_present():
    result = ml_training_data_summary()
    assert "calibration" in result["by_source"]
    assert "injection_recovery" in result["by_source"]


def test_pathway_breakdown_is_dict():
    result = ml_training_data_summary()
    assert isinstance(result["pathway_breakdown"], dict)


def test_recommended_train_count_larger_than_test():
    result = ml_training_data_summary()
    assert result["recommended_train_count"] >= result["recommended_test_count"]


def test_cli_ml_training_data_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "ml-training-data-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_ml_training_data_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "ml-training-data-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "total_case_count" in data
    assert "recommended_train_count" in data
    assert "pathway_breakdown" in data


def test_calibration_case_count_positive():
    result = ml_training_data_summary()
    assert result["calibration_case_count"] >= 1
