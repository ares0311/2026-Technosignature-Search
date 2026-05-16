"""Tests for candidate score history module."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from techno_search.candidate_score_history import (
    ALLOWED_SCORE_HISTORY_PATHWAYS,
    CANDIDATE_SCORE_HISTORY_DISCLAIMER,
    CANDIDATE_SCORE_HISTORY_SCHEMA_VERSION,
    CandidateScoreHistoryEntry,
    load_score_history,
    score_history_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "candidate_score_history.json"


def test_load_score_history_returns_list():
    result = load_score_history()
    assert isinstance(result, list)


def test_load_score_history_returns_dataclass_instances():
    result = load_score_history()
    assert all(isinstance(e, CandidateScoreHistoryEntry) for e in result)


def test_fixture_has_five_entries():
    result = load_score_history()
    assert len(result) == 5


def test_entries_cover_all_three_tracks():
    result = load_score_history()
    tracks = {e.track for e in result}
    assert "radio" in tracks
    assert "infrared" in tracks
    assert "anomaly" in tracks


def test_entry_pathways_are_allowed():
    result = load_score_history()
    for e in result:
        assert e.pathway in ALLOWED_SCORE_HISTORY_PATHWAYS, (
            f"Unexpected pathway: {e.pathway}"
        )


def test_epoch_numbers_are_positive():
    result = load_score_history()
    for e in result:
        assert e.epoch_number >= 1


def test_composite_scores_in_range():
    result = load_score_history()
    for e in result:
        assert 0.0 <= e.composite_score <= 1.0


def test_blocking_count_non_negative():
    result = load_score_history()
    for e in result:
        assert e.blocking_count >= 0


def test_as_dict_returns_expected_keys():
    entry = load_score_history()[0]
    d = entry.as_dict()
    assert "entry_id" in d
    assert "candidate_id" in d
    assert "track" in d
    assert "epoch_number" in d
    assert "composite_score" in d
    assert "pathway" in d
    assert "blocking_count" in d
    assert "operator_id" in d
    assert "created_utc" in d


def test_summary_schema_version():
    result = score_history_summary()
    assert result["schema_version"] == CANDIDATE_SCORE_HISTORY_SCHEMA_VERSION


def test_summary_disclaimer():
    result = score_history_summary()
    assert result["disclaimer"] == CANDIDATE_SCORE_HISTORY_DISCLAIMER
    assert "not constitute" in result["disclaimer"]


def test_summary_entry_count():
    result = score_history_summary()
    assert result["entry_count"] == 5


def test_summary_unique_candidate_count():
    result = score_history_summary()
    assert result["unique_candidate_count"] == 3


def test_summary_tracks_covered():
    result = score_history_summary()
    assert set(result["tracks_covered"]) == {"radio", "infrared", "anomaly"}


def test_summary_by_track():
    result = score_history_summary()
    assert result["by_track"]["radio"] == 2
    assert result["by_track"]["infrared"] == 2
    assert result["by_track"]["anomaly"] == 1


def test_summary_max_epoch_number():
    result = score_history_summary()
    assert result["max_epoch_number"] == 2


def test_summary_declining_candidates():
    result = score_history_summary()
    # cand-infrared-001 went from 0.55 → 0.38 (declining)
    assert "cand-infrared-001" in result["declining_candidates"]


def test_summary_improving_candidates():
    result = score_history_summary()
    # cand-radio-001 went from 0.42 → 0.61 (improving)
    assert "cand-radio-001" in result["improving_candidates"]


def test_summary_stable_candidates_single_epoch():
    result = score_history_summary()
    # cand-anomaly-001 has only epoch 1 (stable)
    assert "cand-anomaly-001" in result["stable_candidates"]


def test_cli_score_history_summary_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "score-history-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_score_history_summary_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "score-history-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "entry_count" in data
    assert "tracks_covered" in data


def test_cli_score_history_summary_with_fixture_path():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "techno_search.cli",
            "score-history-summary",
            "--fixture-path",
            str(FIXTURE_PATH),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["entry_count"] == 5
