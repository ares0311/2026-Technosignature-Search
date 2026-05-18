"""Tests for feature normalization bounds module."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from techno_search.feature_normalization import (
    FEATURE_NORMALIZATION_DISCLAIMER,
    FEATURE_NORMALIZATION_SCHEMA_VERSION,
    FeatureNormalizationBounds,
    feature_normalization_summary,
    load_normalization_bounds,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "feature_normalization.json"


def test_load_bounds_returns_list():
    result = load_normalization_bounds()
    assert isinstance(result, list)


def test_load_bounds_returns_dataclass_instances():
    result = load_normalization_bounds()
    assert all(isinstance(b, FeatureNormalizationBounds) for b in result)


def test_fixture_has_three_entries():
    result = load_normalization_bounds()
    assert len(result) == 3


def test_bounds_cover_all_three_tracks():
    result = load_normalization_bounds()
    tracks = {b.track for b in result}
    assert "radio" in tracks
    assert "infrared" in tracks
    assert "anomaly" in tracks


def test_feature_lists_same_length():
    result = load_normalization_bounds()
    for b in result:
        n = len(b.feature_names)
        assert len(b.min_values) == n
        assert len(b.max_values) == n
        assert len(b.mean_values) == n
        assert len(b.std_values) == n


def test_sample_count_positive():
    result = load_normalization_bounds()
    for b in result:
        assert b.sample_count >= 1


def test_min_lte_max():
    result = load_normalization_bounds()
    for b in result:
        for lo, hi in zip(b.min_values, b.max_values, strict=False):
            assert lo <= hi


def test_as_dict_returns_expected_keys():
    b = load_normalization_bounds()[0]
    d = b.as_dict()
    assert "bounds_id" in d
    assert "track" in d
    assert "feature_names" in d
    assert "min_values" in d
    assert "max_values" in d
    assert "normalization_kind" in d
    assert "sample_count" in d


def test_summary_returns_dict():
    result = feature_normalization_summary()
    assert isinstance(result, dict)


def test_summary_schema_version():
    result = feature_normalization_summary()
    assert result["schema_version"] == FEATURE_NORMALIZATION_SCHEMA_VERSION


def test_summary_disclaimer():
    result = feature_normalization_summary()
    assert result["disclaimer"] == FEATURE_NORMALIZATION_DISCLAIMER
    assert "ML preprocessing" in result["disclaimer"]


def test_summary_bounds_count():
    result = feature_normalization_summary()
    assert result["bounds_count"] == 3


def test_summary_by_track():
    result = feature_normalization_summary()
    assert result["by_track"]["radio"] == 1
    assert result["by_track"]["infrared"] == 1
    assert result["by_track"]["anomaly"] == 1


def test_summary_tracks_covered():
    result = feature_normalization_summary()
    assert set(result["tracks_covered"]) == {"radio", "infrared", "anomaly"}


def test_summary_drift_detected_false():
    # Single extractor version — no drift expected
    result = feature_normalization_summary()
    assert result["drift_detected"] is False


def test_summary_unique_extractor_versions():
    result = feature_normalization_summary()
    assert "feature_extractor_v0" in result["unique_extractor_versions"]


def test_cli_feature_normalization_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "feature-normalization-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_feature_normalization_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "feature-normalization-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "bounds_count" in data
    assert "drift_detected" in data
    assert "tracks_covered" in data


def test_cli_feature_normalization_with_fixture_path():
    result = subprocess.run(
        [
            sys.executable, "-m", "techno_search.cli",
            "feature-normalization-summary",
            "--fixture-path", str(FIXTURE_PATH),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["bounds_count"] == 3
