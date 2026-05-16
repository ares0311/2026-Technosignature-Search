"""Tests for candidate triage note schema, loader, and summary."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

from techno_search.candidate_triage import (
    ALLOWED_TRIAGE_LABELS,
    CANDIDATE_TRIAGE_DISCLAIMER,
    CANDIDATE_TRIAGE_SCHEMA_VERSION,
    CandidateTriageNote,
    load_triage_notes,
    triage_summary,
)
from techno_search.cli import main


def test_triage_schema_version() -> None:
    summary = triage_summary()
    assert summary["schema_version"] == CANDIDATE_TRIAGE_SCHEMA_VERSION
    assert summary["schema_version"] == "candidate_triage_v1"


def test_triage_disclaimer_is_conservative() -> None:
    disclaimer = CANDIDATE_TRIAGE_DISCLAIMER
    assert "scheduling" in disclaimer.lower()
    assert "provenance" in disclaimer.lower()
    assert "not" in disclaimer.lower()
    assert "detection" in disclaimer.lower() or "claim" in disclaimer.lower()


def test_triage_fixture_loads_five_notes() -> None:
    notes = load_triage_notes()
    assert len(notes) == 5


def test_triage_notes_are_dataclass_instances() -> None:
    notes = load_triage_notes()
    for note in notes:
        assert isinstance(note, CandidateTriageNote)
        assert isinstance(note.note_id, str)
        assert isinstance(note.candidate_id, str)
        assert isinstance(note.track, str)
        assert isinstance(note.triage_label, str)
        assert isinstance(note.operator_id, str)
        assert isinstance(note.note_text, str)
        assert isinstance(note.created_utc, str)
        assert isinstance(note.blocking_reasons, list)
        assert isinstance(note.follow_up_required, bool)


def test_triage_note_labels_are_allowed() -> None:
    notes = load_triage_notes()
    for note in notes:
        assert note.triage_label in ALLOWED_TRIAGE_LABELS, (
            f"Unexpected label: {note.triage_label}"
        )


def test_triage_summary_note_count() -> None:
    summary = triage_summary()
    assert summary["note_count"] == 5


def test_triage_summary_unique_candidate_count() -> None:
    summary = triage_summary()
    assert summary["unique_candidate_count"] == 5


def test_triage_summary_unique_operator_count() -> None:
    summary = triage_summary()
    assert summary["unique_operator_count"] == 2


def test_triage_summary_follow_up_required_count() -> None:
    summary = triage_summary()
    assert summary["follow_up_required_count"] == 2


def test_triage_summary_by_track_covers_all_tracks() -> None:
    summary = triage_summary()
    by_track = summary["by_track"]
    assert set(summary["tracks_covered"]) == {"radio", "infrared", "anomaly"}
    assert by_track["radio"] == 2
    assert by_track["infrared"] == 2
    assert by_track["anomaly"] == 1


def test_triage_summary_by_label_covers_expected_labels() -> None:
    summary = triage_summary()
    labels = set(summary["labels_covered"])
    assert "needs_human_review" in labels
    assert "likely_false_positive" in labels
    assert "follow_up_target" in labels
    assert "known_object_annotation" in labels
    assert "insufficient_evidence" in labels


def test_triage_summary_blocking_reason_total() -> None:
    summary = triage_summary()
    assert isinstance(summary["blocking_reason_total"], int)
    assert summary["blocking_reason_total"] >= 0


def test_triage_note_as_dict() -> None:
    notes = load_triage_notes()
    d = notes[0].as_dict()
    assert "note_id" in d
    assert "candidate_id" in d
    assert "track" in d
    assert "triage_label" in d
    assert "blocking_reasons" in d
    assert "follow_up_required" in d


def test_cli_triage_summary_exits_zero() -> None:
    stdout = StringIO()
    exit_code = main(["triage-summary"], stdout=stdout)
    assert exit_code == 0


def test_cli_triage_summary_outputs_json() -> None:
    stdout = StringIO()
    main(["triage-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())
    assert result["schema_version"] == "candidate_triage_v1"
    assert result["note_count"] == 5
    assert "by_label" in result
    assert "by_track" in result
    assert "disclaimer" in result


def test_cli_triage_summary_with_custom_fixture(tmp_path: Path) -> None:
    fixture = {
        "schema_version": "candidate_triage_v1",
        "disclaimer": "test",
        "notes": [
            {
                "note_id": "triage-x",
                "candidate_id": "cand-x",
                "track": "radio",
                "triage_label": "defer",
                "operator_id": "op-x",
                "note_text": "deferred",
                "created_utc": "2026-01-01T00:00:00Z",
                "blocking_reasons": [],
                "follow_up_required": False,
            }
        ],
    }
    fixture_path = tmp_path / "custom_triage.json"
    fixture_path.write_text(json.dumps(fixture), encoding="utf-8")

    stdout = StringIO()
    exit_code = main(["triage-summary", "--fixture-path", str(fixture_path)], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["note_count"] == 1
    assert result["by_track"] == {"radio": 1}
    assert "defer" in result["labels_covered"]
