"""Tests for candidate annotation module."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from techno_search.candidate_annotation import (
    ALLOWED_ANNOTATION_TYPES,
    CANDIDATE_ANNOTATION_DISCLAIMER,
    CANDIDATE_ANNOTATION_SCHEMA_VERSION,
    CandidateAnnotation,
    candidate_annotation_summary,
    load_candidate_annotations,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "candidate_annotations.json"


def test_load_annotations_returns_list():
    result = load_candidate_annotations()
    assert isinstance(result, list)


def test_load_annotations_returns_dataclass_instances():
    result = load_candidate_annotations()
    assert all(isinstance(a, CandidateAnnotation) for a in result)


def test_fixture_has_five_annotations():
    result = load_candidate_annotations()
    assert len(result) == 5


def test_annotations_cover_all_three_tracks():
    result = load_candidate_annotations()
    tracks = {a.track for a in result}
    assert "radio" in tracks
    assert "infrared" in tracks
    assert "anomaly" in tracks


def test_annotation_types_are_allowed():
    result = load_candidate_annotations()
    for a in result:
        assert a.annotation_type in ALLOWED_ANNOTATION_TYPES


def test_is_resolved_is_bool():
    result = load_candidate_annotations()
    for a in result:
        assert isinstance(a.is_resolved, bool)


def test_as_dict_returns_expected_keys():
    a = load_candidate_annotations()[0]
    d = a.as_dict()
    assert "annotation_id" in d
    assert "candidate_id" in d
    assert "track" in d
    assert "annotation_type" in d
    assert "is_resolved" in d


def test_summary_returns_dict():
    result = candidate_annotation_summary()
    assert isinstance(result, dict)


def test_summary_schema_version():
    result = candidate_annotation_summary()
    assert result["schema_version"] == CANDIDATE_ANNOTATION_SCHEMA_VERSION


def test_summary_disclaimer():
    result = candidate_annotation_summary()
    assert result["disclaimer"] == CANDIDATE_ANNOTATION_DISCLAIMER
    assert "scheduling provenance" in result["disclaimer"]


def test_summary_annotation_count():
    result = candidate_annotation_summary()
    assert result["annotation_count"] == 5


def test_summary_unresolved_count():
    result = candidate_annotation_summary()
    # ann-004 is resolved, the rest are unresolved
    assert result["unresolved_count"] == 4


def test_summary_by_track():
    result = candidate_annotation_summary()
    assert result["by_track"]["radio"] == 2
    assert result["by_track"]["infrared"] == 2
    assert result["by_track"]["anomaly"] == 1


def test_summary_by_type_contains_warning():
    result = candidate_annotation_summary()
    assert "warning" in result["by_type"]


def test_summary_tracks_covered():
    result = candidate_annotation_summary()
    assert set(result["tracks_covered"]) == {"radio", "infrared", "anomaly"}


def test_summary_unique_operators():
    result = candidate_annotation_summary()
    assert result["unique_operators"] >= 2


def test_allowed_annotation_types_frozenset():
    assert "note" in ALLOWED_ANNOTATION_TYPES
    assert "warning" in ALLOWED_ANNOTATION_TYPES
    assert "tag" in ALLOWED_ANNOTATION_TYPES
    assert "question" in ALLOWED_ANNOTATION_TYPES
    assert "followup" in ALLOWED_ANNOTATION_TYPES
    assert "highlight" in ALLOWED_ANNOTATION_TYPES


def test_cli_candidate_annotation_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "candidate-annotation-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_candidate_annotation_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "candidate-annotation-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "annotation_count" in data
    assert "unresolved_count" in data
    assert "by_track" in data


def test_cli_candidate_annotation_with_fixture_path():
    result = subprocess.run(
        [
            sys.executable, "-m", "techno_search.cli",
            "candidate-annotation-summary",
            "--fixture-path", str(FIXTURE_PATH),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["annotation_count"] == 5
