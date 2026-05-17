"""Tests for candidate flags module."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from techno_search.candidate_flags import (
    ALLOWED_FLAG_SEVERITIES,
    ALLOWED_FLAG_STATUSES,
    ALLOWED_FLAG_TYPES,
    CANDIDATE_FLAGS_DISCLAIMER,
    CANDIDATE_FLAGS_SCHEMA_VERSION,
    CandidateFlag,
    candidate_flags_summary,
    load_candidate_flags,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "candidate_flags.json"


def test_load_candidate_flags_returns_list():
    result = load_candidate_flags()
    assert isinstance(result, list)


def test_load_candidate_flags_returns_dataclass_instances():
    result = load_candidate_flags()
    assert all(isinstance(f, CandidateFlag) for f in result)


def test_fixture_has_five_flags():
    result = load_candidate_flags()
    assert len(result) == 5


def test_flags_cover_all_three_tracks():
    result = load_candidate_flags()
    tracks = {f.track for f in result}
    assert "radio" in tracks
    assert "infrared" in tracks
    assert "anomaly" in tracks


def test_flag_severities_are_allowed():
    result = load_candidate_flags()
    for f in result:
        assert f.severity in ALLOWED_FLAG_SEVERITIES, f"Unexpected severity: {f.severity}"


def test_flag_types_are_allowed():
    result = load_candidate_flags()
    for f in result:
        assert f.flag_type in ALLOWED_FLAG_TYPES, f"Unexpected type: {f.flag_type}"


def test_flag_statuses_are_allowed():
    result = load_candidate_flags()
    for f in result:
        assert f.status in ALLOWED_FLAG_STATUSES, f"Unexpected status: {f.status}"


def test_as_dict_returns_expected_keys():
    flag = load_candidate_flags()[0]
    d = flag.as_dict()
    assert "flag_id" in d
    assert "candidate_id" in d
    assert "track" in d
    assert "flag_type" in d
    assert "severity" in d
    assert "raised_by" in d
    assert "raised_utc" in d
    assert "status" in d


def test_summary_schema_version():
    result = candidate_flags_summary()
    assert result["schema_version"] == CANDIDATE_FLAGS_SCHEMA_VERSION


def test_summary_disclaimer():
    result = candidate_flags_summary()
    assert result["disclaimer"] == CANDIDATE_FLAGS_DISCLAIMER
    assert "do not constitute" in result["disclaimer"]


def test_summary_flag_count():
    result = candidate_flags_summary()
    assert result["flag_count"] == 5


def test_summary_open_count():
    result = candidate_flags_summary()
    assert result["open_count"] == 2


def test_summary_critical_count():
    result = candidate_flags_summary()
    assert result["critical_count"] == 1


def test_summary_by_track():
    result = candidate_flags_summary()
    assert result["by_track"]["radio"] == 2
    assert result["by_track"]["infrared"] == 2
    assert result["by_track"]["anomaly"] == 1


def test_summary_by_severity():
    result = candidate_flags_summary()
    assert "high" in result["by_severity"]
    assert "medium" in result["by_severity"]
    assert "critical" in result["by_severity"]
    assert "low" in result["by_severity"]


def test_summary_by_status():
    result = candidate_flags_summary()
    assert "open" in result["by_status"]
    assert "resolved" in result["by_status"]
    assert "dismissed" in result["by_status"]


def test_summary_tracks_covered():
    result = candidate_flags_summary()
    assert set(result["tracks_covered"]) == {"radio", "infrared", "anomaly"}


def test_allowed_severities_frozenset():
    assert "critical" in ALLOWED_FLAG_SEVERITIES
    assert "info" in ALLOWED_FLAG_SEVERITIES


def test_allowed_types_frozenset():
    assert "rfi_suspected" in ALLOWED_FLAG_TYPES
    assert "data_quality_low" in ALLOWED_FLAG_TYPES


def test_cli_candidate_flags_summary_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "candidate-flags-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_candidate_flags_summary_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "candidate-flags-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "flag_count" in data
    assert "tracks_covered" in data


def test_cli_candidate_flags_summary_with_fixture_path():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "techno_search.cli",
            "candidate-flags-summary",
            "--fixture-path",
            str(FIXTURE_PATH),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["flag_count"] == 5
