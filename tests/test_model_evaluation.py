"""Tests for model evaluation harness module."""

from __future__ import annotations

import json
import subprocess
import sys

from techno_search.model_evaluation import (
    MODEL_EVALUATION_DISCLAIMER,
    MODEL_EVALUATION_SCHEMA_VERSION,
    ModelEvaluationResult,
    load_model_evaluation_results,
    model_evaluation_summary,
)


def test_load_results_returns_list():
    result = load_model_evaluation_results()
    assert isinstance(result, list)


def test_load_results_returns_dataclass_instances():
    result = load_model_evaluation_results()
    assert all(isinstance(r, ModelEvaluationResult) for r in result)


def test_fixture_has_four_entries():
    result = load_model_evaluation_results()
    assert len(result) == 4


def test_accuracy_in_range():
    result = load_model_evaluation_results()
    for r in result:
        assert 0.0 <= r.accuracy <= 1.0


def test_precision_in_range():
    result = load_model_evaluation_results()
    for r in result:
        assert 0.0 <= r.precision <= 1.0


def test_recall_in_range():
    result = load_model_evaluation_results()
    for r in result:
        assert 0.0 <= r.recall <= 1.0


def test_f1_in_range():
    result = load_model_evaluation_results()
    for r in result:
        assert 0.0 <= r.f1 <= 1.0


def test_beats_baseline_flag_consistent():
    result = load_model_evaluation_results()
    for r in result:
        if r.beats_baseline:
            assert r.accuracy > r.baseline_accuracy
        else:
            assert r.accuracy <= r.baseline_accuracy


def test_at_least_one_below_baseline():
    result = load_model_evaluation_results()
    assert any(not r.beats_baseline for r in result)


def test_as_dict_returns_expected_keys():
    r = load_model_evaluation_results()[0]
    d = r.as_dict()
    assert "eval_id" in d
    assert "model_id" in d
    assert "track" in d
    assert "accuracy" in d
    assert "beats_baseline" in d


def test_summary_returns_dict():
    result = model_evaluation_summary()
    assert isinstance(result, dict)


def test_summary_schema_version():
    result = model_evaluation_summary()
    assert result["schema_version"] == MODEL_EVALUATION_SCHEMA_VERSION


def test_summary_disclaimer():
    result = model_evaluation_summary()
    assert result["disclaimer"] == MODEL_EVALUATION_DISCLAIMER
    assert "synthetic" in result["disclaimer"].lower()


def test_summary_evaluation_count():
    result = model_evaluation_summary()
    assert result["evaluation_count"] == 4


def test_summary_above_baseline_count():
    result = model_evaluation_summary()
    assert result["above_baseline_count"] == 3


def test_summary_below_baseline_count():
    result = model_evaluation_summary()
    assert result["below_baseline_count"] == 1


def test_summary_by_track_keys():
    result = model_evaluation_summary()
    assert "radio" in result["by_track"]
    assert "infrared" in result["by_track"]
    assert "anomaly" in result["by_track"]


def test_summary_best_model():
    result = model_evaluation_summary()
    assert result["best_accuracy"] > 0.0
    assert len(result["best_model_id"]) > 0


def test_summary_worst_model():
    result = model_evaluation_summary()
    assert result["worst_accuracy"] < 1.0
    assert len(result["worst_model_id"]) > 0


def test_cli_model_evaluation_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "model-evaluation-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_model_evaluation_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "model-evaluation-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "evaluation_count" in data
    assert "above_baseline_count" in data
    assert "below_baseline_count" in data
