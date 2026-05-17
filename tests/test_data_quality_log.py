"""Tests for data quality log module."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from techno_search.data_quality_log import (
    ALLOWED_QUALITY_GRADES,
    ALLOWED_QUALITY_ISSUE_TYPES,
    DATA_QUALITY_LOG_DISCLAIMER,
    DATA_QUALITY_LOG_SCHEMA_VERSION,
    DataQualityEntry,
    data_quality_log_summary,
    load_data_quality_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "data_quality_log.json"


def test_load_entries_returns_list():
    result = load_data_quality_entries()
    assert isinstance(result, list)


def test_load_entries_returns_dataclass_instances():
    result = load_data_quality_entries()
    assert all(isinstance(e, DataQualityEntry) for e in result)


def test_fixture_has_five_entries():
    result = load_data_quality_entries()
    assert len(result) == 5


def test_entries_cover_all_three_tracks():
    result = load_data_quality_entries()
    tracks = {e.track for e in result}
    assert "radio" in tracks
    assert "infrared" in tracks
    assert "anomaly" in tracks


def test_quality_grades_are_allowed():
    result = load_data_quality_entries()
    for e in result:
        assert e.quality_grade in ALLOWED_QUALITY_GRADES


def test_issue_types_are_allowed():
    result = load_data_quality_entries()
    for e in result:
        for issue in e.issue_types:
            assert issue in ALLOWED_QUALITY_ISSUE_TYPES


def test_weather_flag_is_bool():
    result = load_data_quality_entries()
    for e in result:
        assert isinstance(e.weather_flag, bool)


def test_equipment_flag_is_bool():
    result = load_data_quality_entries()
    for e in result:
        assert isinstance(e.equipment_flag, bool)


def test_as_dict_returns_expected_keys():
    e = load_data_quality_entries()[0]
    d = e.as_dict()
    assert "entry_id" in d
    assert "observation_id" in d
    assert "track" in d
    assert "quality_grade" in d
    assert "issue_types" in d


def test_summary_schema_version():
    result = data_quality_log_summary()
    assert result["schema_version"] == DATA_QUALITY_LOG_SCHEMA_VERSION


def test_summary_disclaimer():
    result = data_quality_log_summary()
    assert result["disclaimer"] == DATA_QUALITY_LOG_DISCLAIMER
    assert "observational conditions" in result["disclaimer"]


def test_summary_entry_count():
    result = data_quality_log_summary()
    assert result["entry_count"] == 5


def test_summary_poor_count():
    result = data_quality_log_summary()
    # dq-004 is "poor"
    assert result["poor_count"] == 1


def test_summary_usable_count():
    result = data_quality_log_summary()
    # excellent + good + marginal = 4 usable; poor = 1 not usable
    assert result["usable_count"] == 4


def test_summary_weather_affected():
    result = data_quality_log_summary()
    assert result["weather_affected_count"] == 1


def test_summary_equipment_affected():
    result = data_quality_log_summary()
    assert result["equipment_affected_count"] == 1


def test_summary_rfi_affected():
    result = data_quality_log_summary()
    # dq-001 has rfi in issue_types
    assert result["rfi_affected_count"] == 1


def test_summary_by_track():
    result = data_quality_log_summary()
    assert result["by_track"]["radio"] == 2
    assert result["by_track"]["infrared"] == 2
    assert result["by_track"]["anomaly"] == 1


def test_summary_tracks_covered():
    result = data_quality_log_summary()
    assert set(result["tracks_covered"]) == {"radio", "infrared", "anomaly"}


def test_allowed_grades_frozenset():
    assert "excellent" in ALLOWED_QUALITY_GRADES
    assert "poor" in ALLOWED_QUALITY_GRADES
    assert "unusable" in ALLOWED_QUALITY_GRADES


def test_cli_data_quality_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "data-quality-log-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_data_quality_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "data-quality-log-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "entry_count" in data
    assert "poor_count" in data


def test_cli_data_quality_with_fixture_path():
    result = subprocess.run(
        [
            sys.executable, "-m", "techno_search.cli",
            "data-quality-log-summary",
            "--fixture-path", str(FIXTURE_PATH),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["entry_count"] == 5
