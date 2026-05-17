"""Tests for candidate_observation_notes module."""

from __future__ import annotations

import json
from io import StringIO

from techno_search.candidate_observation_notes import (
    ALLOWED_OBSERVATION_OUTCOMES,
    CANDIDATE_OBSERVATION_NOTES_DISCLAIMER,
    CANDIDATE_OBSERVATION_NOTES_SCHEMA_VERSION,
    CandidateObservationNote,
    load_observation_notes,
    observation_notes_summary,
)
from techno_search.cli import main


def test_load_observation_notes_returns_list():
    notes = load_observation_notes()
    assert isinstance(notes, list)
    assert len(notes) >= 1


def test_observation_notes_are_dataclass_instances():
    notes = load_observation_notes()
    for note in notes:
        assert isinstance(note, CandidateObservationNote)
        assert isinstance(note.note_id, str)
        assert isinstance(note.candidate_id, str)
        assert isinstance(note.track, str)
        assert isinstance(note.observation_id, str)
        assert isinstance(note.operator_id, str)
        assert isinstance(note.outcome, str)
        assert isinstance(note.note_text, str)
        assert isinstance(note.created_utc, str)
        assert isinstance(note.quality_flags, list)
        assert isinstance(note.follow_up_recommended, bool)


def test_observation_note_outcomes_are_allowed():
    notes = load_observation_notes()
    for note in notes:
        assert note.outcome in ALLOWED_OBSERVATION_OUTCOMES, (
            f"Unexpected outcome: {note.outcome}"
        )


def test_observation_notes_cover_all_tracks():
    notes = load_observation_notes()
    tracks = {n.track for n in notes}
    assert "radio" in tracks
    assert "infrared" in tracks
    assert "anomaly" in tracks


def test_observation_notes_fixture_has_five():
    notes = load_observation_notes()
    assert len(notes) == 5


def test_observation_note_as_dict():
    notes = load_observation_notes()
    d = notes[0].as_dict()
    for key in (
        "note_id", "candidate_id", "track", "observation_id",
        "operator_id", "outcome", "note_text", "created_utc",
        "quality_flags", "follow_up_recommended",
    ):
        assert key in d


def test_observation_notes_summary_schema_version():
    summary = observation_notes_summary()
    assert summary["schema_version"] == CANDIDATE_OBSERVATION_NOTES_SCHEMA_VERSION


def test_observation_notes_summary_disclaimer():
    summary = observation_notes_summary()
    assert CANDIDATE_OBSERVATION_NOTES_DISCLAIMER in summary["disclaimer"]


def test_observation_notes_summary_note_count():
    summary = observation_notes_summary()
    assert summary["note_count"] == 5


def test_observation_notes_summary_tracks_covered():
    summary = observation_notes_summary()
    tracks = set(summary["tracks_covered"])
    assert "radio" in tracks
    assert "infrared" in tracks
    assert "anomaly" in tracks


def test_observation_notes_summary_follow_up_count():
    summary = observation_notes_summary()
    assert isinstance(summary["follow_up_recommended_count"], int)
    assert summary["follow_up_recommended_count"] >= 1


def test_observation_notes_summary_by_track():
    summary = observation_notes_summary()
    assert isinstance(summary["by_track"], dict)
    assert summary["by_track"]["radio"] >= 1
    assert summary["by_track"]["infrared"] >= 1
    assert summary["by_track"]["anomaly"] >= 1


def test_observation_notes_summary_by_outcome():
    summary = observation_notes_summary()
    assert isinstance(summary["by_outcome"], dict)
    assert len(summary["by_outcome"]) >= 2


def test_observation_notes_summary_unique_operators():
    summary = observation_notes_summary()
    assert isinstance(summary["unique_operator_count"], int)
    assert summary["unique_operator_count"] >= 2


def test_observation_notes_summary_quality_flags():
    summary = observation_notes_summary()
    assert isinstance(summary["quality_flag_total"], int)
    assert summary["quality_flag_total"] >= 1


def test_allowed_observation_outcomes():
    assert "clean" in ALLOWED_OBSERVATION_OUTCOMES
    assert "rfi_contaminated" in ALLOWED_OBSERVATION_OUTCOMES
    assert "non_detection" in ALLOWED_OBSERVATION_OUTCOMES
    assert "data_quality_issue" in ALLOWED_OBSERVATION_OUTCOMES


def test_cli_observation_notes_summary_exits_zero():
    stdout = StringIO()
    exit_code = main(["observation-notes-summary"], stdout=stdout)
    assert exit_code == 0


def test_cli_observation_notes_summary_outputs_json():
    stdout = StringIO()
    main(["observation-notes-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())
    assert result["schema_version"] == CANDIDATE_OBSERVATION_NOTES_SCHEMA_VERSION
    assert result["note_count"] == 5
    assert "by_track" in result
    assert "by_outcome" in result
    assert "disclaimer" in result


def test_cli_observation_notes_summary_with_custom_fixture(tmp_path):
    fixture = {
        "schema_version": "candidate_observation_notes_v1",
        "disclaimer": "test",
        "notes": [
            {
                "note_id": "obs-x",
                "candidate_id": "cand-x",
                "track": "radio",
                "observation_id": "obs-r-x",
                "operator_id": "op-x",
                "outcome": "clean",
                "note_text": "clean run",
                "created_utc": "2026-01-01T00:00:00Z",
            }
        ],
    }
    fp = tmp_path / "notes.json"
    fp.write_text(json.dumps(fixture), encoding="utf-8")

    stdout = StringIO()
    exit_code = main(["observation-notes-summary", "--fixture-path", str(fp)], stdout=stdout)
    result = json.loads(stdout.getvalue())
    assert exit_code == 0
    assert result["note_count"] == 1
    assert result["by_track"] == {"radio": 1}
