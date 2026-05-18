"""Tests for candidate feature vector module."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from techno_search.candidate_feature_vector import (
    ALLOWED_NORMALIZATION_KINDS,
    CANDIDATE_FEATURE_VECTOR_DISCLAIMER,
    CANDIDATE_FEATURE_VECTOR_SCHEMA_VERSION,
    CandidateFeatureVector,
    feature_vector_summary,
    load_feature_vectors,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "candidate_feature_vectors.json"


def test_load_feature_vectors_returns_list():
    result = load_feature_vectors()
    assert isinstance(result, list)


def test_load_feature_vectors_returns_dataclass_instances():
    result = load_feature_vectors()
    assert all(isinstance(v, CandidateFeatureVector) for v in result)


def test_fixture_has_five_vectors():
    result = load_feature_vectors()
    assert len(result) == 5


def test_vectors_cover_all_three_tracks():
    result = load_feature_vectors()
    tracks = {v.track for v in result}
    assert "radio" in tracks
    assert "infrared" in tracks
    assert "anomaly" in tracks


def test_normalization_kinds_are_allowed():
    result = load_feature_vectors()
    for v in result:
        assert v.normalization_kind in ALLOWED_NORMALIZATION_KINDS


def test_feature_names_and_values_same_length():
    result = load_feature_vectors()
    for v in result:
        assert len(v.feature_names) == len(v.feature_values)


def test_feature_values_are_floats():
    result = load_feature_vectors()
    for v in result:
        assert all(isinstance(f, float) for f in v.feature_values)


def test_is_normalized_is_bool():
    result = load_feature_vectors()
    for v in result:
        assert isinstance(v.is_normalized, bool)


def test_as_dict_returns_expected_keys():
    v = load_feature_vectors()[0]
    d = v.as_dict()
    assert "vector_id" in d
    assert "candidate_id" in d
    assert "track" in d
    assert "feature_names" in d
    assert "feature_values" in d
    assert "normalization_kind" in d
    assert "is_normalized" in d


def test_summary_returns_dict():
    result = feature_vector_summary()
    assert isinstance(result, dict)


def test_summary_schema_version():
    result = feature_vector_summary()
    assert result["schema_version"] == CANDIDATE_FEATURE_VECTOR_SCHEMA_VERSION


def test_summary_disclaimer():
    result = feature_vector_summary()
    assert result["disclaimer"] == CANDIDATE_FEATURE_VECTOR_DISCLAIMER
    assert "ML preprocessing" in result["disclaimer"]


def test_summary_vector_count():
    result = feature_vector_summary()
    assert result["vector_count"] == 5


def test_summary_by_track():
    result = feature_vector_summary()
    assert result["by_track"]["radio"] == 2
    assert result["by_track"]["infrared"] == 2
    assert result["by_track"]["anomaly"] == 1


def test_summary_tracks_covered():
    result = feature_vector_summary()
    assert set(result["tracks_covered"]) == {"radio", "infrared", "anomaly"}


def test_summary_avg_feature_count():
    result = feature_vector_summary()
    assert isinstance(result["avg_feature_count"], float)
    assert result["avg_feature_count"] == 6.0


def test_summary_unique_extractor_versions():
    result = feature_vector_summary()
    assert "feature_extractor_v0" in result["unique_extractor_versions"]


def test_allowed_normalization_kinds_frozenset():
    assert "none" in ALLOWED_NORMALIZATION_KINDS
    assert "min_max" in ALLOWED_NORMALIZATION_KINDS
    assert "z_score" in ALLOWED_NORMALIZATION_KINDS


def test_cli_feature_vector_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "feature-vector-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_feature_vector_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "feature-vector-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "vector_count" in data
    assert "by_track" in data
    assert "tracks_covered" in data


def test_cli_feature_vector_with_fixture_path():
    result = subprocess.run(
        [
            sys.executable, "-m", "techno_search.cli",
            "feature-vector-summary",
            "--fixture-path", str(FIXTURE_PATH),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["vector_count"] == 5
