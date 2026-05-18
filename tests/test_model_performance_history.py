"""Tests for model performance history module."""

from __future__ import annotations

import json
import subprocess
import sys

from techno_search.model_performance_history import (
    ALLOWED_TRENDS,
    MODEL_PERFORMANCE_HISTORY_DISCLAIMER,
    MODEL_PERFORMANCE_HISTORY_SCHEMA_VERSION,
    ModelPerformanceSnapshot,
    load_model_performance_snapshots,
    model_performance_history_summary,
)


def test_load_snapshots_returns_list():
    result = load_model_performance_snapshots()
    assert isinstance(result, list)


def test_load_snapshots_returns_dataclass_instances():
    result = load_model_performance_snapshots()
    assert all(isinstance(s, ModelPerformanceSnapshot) for s in result)


def test_fixture_has_five_snapshots():
    result = load_model_performance_snapshots()
    assert len(result) == 5


def test_accuracy_in_range():
    result = load_model_performance_snapshots()
    for s in result:
        assert 0.0 <= s.accuracy <= 1.0


def test_loss_non_negative():
    result = load_model_performance_snapshots()
    for s in result:
        assert s.loss >= 0.0


def test_trends_valid():
    result = load_model_performance_snapshots()
    for s in result:
        assert s.trend in ALLOWED_TRENDS


def test_epoch_non_negative():
    result = load_model_performance_snapshots()
    for s in result:
        assert s.epoch >= 0


def test_at_least_one_declining_trend():
    result = load_model_performance_snapshots()
    assert any(s.trend == "declining" for s in result)


def test_at_least_one_improving_trend():
    result = load_model_performance_snapshots()
    assert any(s.trend == "improving" for s in result)


def test_as_dict_returns_expected_keys():
    s = load_model_performance_snapshots()[0]
    d = s.as_dict()
    assert "snapshot_id" in d
    assert "model_id" in d
    assert "track" in d
    assert "epoch" in d
    assert "accuracy" in d
    assert "loss" in d
    assert "trend" in d


def test_summary_returns_dict():
    result = model_performance_history_summary()
    assert isinstance(result, dict)


def test_summary_schema_version():
    result = model_performance_history_summary()
    assert result["schema_version"] == MODEL_PERFORMANCE_HISTORY_SCHEMA_VERSION


def test_summary_disclaimer():
    result = model_performance_history_summary()
    assert result["disclaimer"] == MODEL_PERFORMANCE_HISTORY_DISCLAIMER
    assert "local scheduling records" in result["disclaimer"].lower()


def test_summary_snapshot_count():
    result = model_performance_history_summary()
    assert result["snapshot_count"] == 5


def test_summary_unique_model_count():
    result = model_performance_history_summary()
    assert result["unique_model_count"] == 3


def test_summary_by_model_keys():
    result = model_performance_history_summary()
    assert "mdl-001" in result["by_model"]
    assert "mdl-002" in result["by_model"]
    assert "mdl-003" in result["by_model"]


def test_summary_by_trend_has_declining():
    result = model_performance_history_summary()
    assert "declining" in result["by_trend"]


def test_summary_most_recent_covers_all_models():
    result = model_performance_history_summary()
    most_recent = result["most_recent_snapshot_by_model"]
    assert "mdl-001" in most_recent
    assert "mdl-002" in most_recent
    assert "mdl-003" in most_recent


def test_summary_most_recent_is_highest_epoch():
    result = model_performance_history_summary()
    assert result["most_recent_snapshot_by_model"]["mdl-001"]["epoch"] == 5
    assert result["most_recent_snapshot_by_model"]["mdl-002"]["epoch"] == 5


def test_cli_model_performance_history_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "model-performance-history-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_model_performance_history_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "model-performance-history-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "snapshot_count" in data
    assert "unique_model_count" in data
    assert "by_trend" in data
