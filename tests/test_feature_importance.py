"""Tests for feature importance module."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from techno_search.feature_importance import (
    FEATURE_IMPORTANCE_DISCLAIMER,
    FEATURE_IMPORTANCE_SCHEMA_VERSION,
    FeatureImportanceEntry,
    feature_importance_summary,
    load_feature_importance_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "feature_importance.json"


def test_load_entries_returns_list():
    result = load_feature_importance_entries()
    assert isinstance(result, list)


def test_load_entries_returns_dataclass_instances():
    result = load_feature_importance_entries()
    assert all(isinstance(e, FeatureImportanceEntry) for e in result)


def test_fixture_has_six_entries():
    result = load_feature_importance_entries()
    assert len(result) == 6


def test_entries_cover_all_three_tracks():
    result = load_feature_importance_entries()
    tracks = {e.track for e in result}
    assert "radio" in tracks
    assert "infrared" in tracks
    assert "anomaly" in tracks


def test_ranks_positive():
    result = load_feature_importance_entries()
    for e in result:
        assert e.rank >= 1


def test_fire_rates_in_range():
    result = load_feature_importance_entries()
    for e in result:
        assert 0.0 <= e.rule_fire_rate <= 1.0


def test_importance_scores_in_range():
    result = load_feature_importance_entries()
    for e in result:
        assert 0.0 <= e.importance_score <= 1.0


def test_rank_one_has_highest_importance_per_track():
    result = load_feature_importance_entries()
    by_track: dict[str, list[FeatureImportanceEntry]] = {}
    for e in result:
        by_track.setdefault(e.track, []).append(e)
    for entries in by_track.values():
        rank1 = next(e for e in entries if e.rank == 1)
        for e in entries:
            assert rank1.importance_score >= e.importance_score


def test_as_dict_returns_expected_keys():
    e = load_feature_importance_entries()[0]
    d = e.as_dict()
    assert "importance_id" in d
    assert "track" in d
    assert "feature_name" in d
    assert "baseline_rule_name" in d
    assert "rule_fire_rate" in d
    assert "importance_score" in d
    assert "rank" in d


def test_summary_returns_dict():
    result = feature_importance_summary()
    assert isinstance(result, dict)


def test_summary_schema_version():
    result = feature_importance_summary()
    assert result["schema_version"] == FEATURE_IMPORTANCE_SCHEMA_VERSION


def test_summary_disclaimer():
    result = feature_importance_summary()
    assert result["disclaimer"] == FEATURE_IMPORTANCE_DISCLAIMER
    assert "rule fire rates" in result["disclaimer"]


def test_summary_entry_count():
    result = feature_importance_summary()
    assert result["entry_count"] == 6


def test_summary_by_track():
    result = feature_importance_summary()
    assert result["by_track"]["radio"] == 2
    assert result["by_track"]["infrared"] == 2
    assert result["by_track"]["anomaly"] == 2


def test_summary_top_feature_by_track():
    result = feature_importance_summary()
    assert result["top_feature_by_track"]["radio"] == "recurrence_score"
    assert result["top_feature_by_track"]["infrared"] == "ir_excess_score"
    assert result["top_feature_by_track"]["anomaly"] == "crossmatch_confidence"


def test_summary_tracks_covered():
    result = feature_importance_summary()
    assert set(result["tracks_covered"]) == {"radio", "infrared", "anomaly"}


def test_summary_unique_rule_names():
    result = feature_importance_summary()
    assert "rfi_band_clear" in result["unique_rule_names"]
    assert "ir_excess_present" in result["unique_rule_names"]
    assert "crossmatch_confident" in result["unique_rule_names"]


def test_cli_feature_importance_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "feature-importance-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_feature_importance_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "feature-importance-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "entry_count" in data
    assert "top_feature_by_track" in data
    assert "unique_rule_names" in data


def test_cli_feature_importance_with_fixture_path():
    result = subprocess.run(
        [
            sys.executable, "-m", "techno_search.cli",
            "feature-importance-summary",
            "--fixture-path", str(FIXTURE_PATH),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["entry_count"] == 6
