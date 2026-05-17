"""Tests for candidate resolution module."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from techno_search.candidate_resolution import (
    ALLOWED_RESOLUTION_STATUSES,
    CANDIDATE_RESOLUTION_DISCLAIMER,
    CANDIDATE_RESOLUTION_SCHEMA_VERSION,
    CandidateResolutionRecord,
    candidate_resolution_summary,
    load_resolution_records,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "candidate_resolution.json"


def test_load_resolution_records_returns_list():
    result = load_resolution_records()
    assert isinstance(result, list)


def test_load_resolution_records_returns_dataclass_instances():
    result = load_resolution_records()
    assert all(isinstance(r, CandidateResolutionRecord) for r in result)


def test_fixture_has_five_records():
    result = load_resolution_records()
    assert len(result) == 5


def test_records_cover_all_three_tracks():
    result = load_resolution_records()
    tracks = {r.track for r in result}
    assert "radio" in tracks
    assert "infrared" in tracks
    assert "anomaly" in tracks


def test_resolution_statuses_are_allowed():
    result = load_resolution_records()
    for r in result:
        assert r.resolution_status in ALLOWED_RESOLUTION_STATUSES


def test_days_to_resolution_non_negative():
    result = load_resolution_records()
    for r in result:
        assert r.days_to_resolution >= 0


def test_as_dict_returns_expected_keys():
    rec = load_resolution_records()[0]
    d = rec.as_dict()
    assert "record_id" in d
    assert "candidate_id" in d
    assert "track" in d
    assert "resolution_status" in d
    assert "days_to_resolution" in d


def test_summary_schema_version():
    result = candidate_resolution_summary()
    assert result["schema_version"] == CANDIDATE_RESOLUTION_SCHEMA_VERSION


def test_summary_disclaimer():
    result = candidate_resolution_summary()
    assert result["disclaimer"] == CANDIDATE_RESOLUTION_DISCLAIMER
    assert "scheduling closure" in result["disclaimer"]


def test_summary_record_count():
    result = candidate_resolution_summary()
    assert result["record_count"] == 5


def test_summary_unresolved_count():
    result = candidate_resolution_summary()
    assert result["unresolved_count"] == 1


def test_summary_resolved_fp_count():
    result = candidate_resolution_summary()
    assert result["resolved_fp_count"] == 2


def test_summary_average_days_positive():
    result = candidate_resolution_summary()
    assert result["average_days_to_resolution"] > 0


def test_summary_max_days():
    result = candidate_resolution_summary()
    assert result["max_days_to_resolution"] == 45


def test_summary_by_track():
    result = candidate_resolution_summary()
    assert result["by_track"]["radio"] == 2
    assert result["by_track"]["infrared"] == 2
    assert result["by_track"]["anomaly"] == 1


def test_summary_tracks_covered():
    result = candidate_resolution_summary()
    assert set(result["tracks_covered"]) == {"radio", "infrared", "anomaly"}


def test_summary_unique_operator_count():
    result = candidate_resolution_summary()
    assert result["unique_operator_count"] >= 1


def test_allowed_statuses_frozenset():
    assert "resolved_fp" in ALLOWED_RESOLUTION_STATUSES
    assert "unresolved" in ALLOWED_RESOLUTION_STATUSES
    assert "inconclusive" in ALLOWED_RESOLUTION_STATUSES
    assert "deferred" in ALLOWED_RESOLUTION_STATUSES


def test_cli_resolution_summary_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "candidate-resolution-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_resolution_summary_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "candidate-resolution-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "record_count" in data
    assert "unresolved_count" in data


def test_cli_resolution_summary_with_fixture_path():
    result = subprocess.run(
        [
            sys.executable, "-m", "techno_search.cli",
            "candidate-resolution-summary",
            "--fixture-path", str(FIXTURE_PATH),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["record_count"] == 5
