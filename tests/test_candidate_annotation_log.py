"""Tests for candidate_annotation_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.candidate_annotation_log import (
    ALLOWED_ANNOTATION_LOG_KINDS,
    ALLOWED_ANNOTATION_LOG_STATUSES,
    CANDIDATE_ANNOTATION_LOG_DISCLAIMER,
    CANDIDATE_ANNOTATION_LOG_SCHEMA_VERSION,
    candidate_annotation_log_summary,
    load_candidate_annotation_log_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "candidate_annotation_log.json"


def test_load_entries_returns_five() -> None:
    entries = load_candidate_annotation_log_entries()
    assert len(entries) == 5


def test_all_annotation_kinds_present() -> None:
    entries = load_candidate_annotation_log_entries()
    kinds = {e.annotation_kind for e in entries}
    assert "manual_tag" in kinds
    assert "automated_flag" in kinds
    assert "cross_reference" in kinds
    assert "operator_note" in kinds
    assert "classification_hint" in kinds


def test_all_statuses_present() -> None:
    entries = load_candidate_annotation_log_entries()
    statuses = {e.status for e in entries}
    assert "active" in statuses
    assert "superseded" in statuses
    assert "withdrawn" in statuses


def test_summary_entry_count_five() -> None:
    summary = candidate_annotation_log_summary()
    assert summary["entry_count"] == 5


def test_active_count_is_three() -> None:
    summary = candidate_annotation_log_summary()
    assert summary["active_count"] == 3


def test_superseded_count_is_one() -> None:
    summary = candidate_annotation_log_summary()
    assert summary["superseded_count"] == 1


def test_withdrawn_count_is_one() -> None:
    summary = candidate_annotation_log_summary()
    assert summary["withdrawn_count"] == 1


def test_by_status_covers_all_three() -> None:
    summary = candidate_annotation_log_summary()
    by_status = summary["by_status"]
    assert set(by_status.keys()) == {"active", "superseded", "withdrawn"}


def test_by_annotation_kind_covers_all_five() -> None:
    summary = candidate_annotation_log_summary()
    by_kind = summary["by_annotation_kind"]
    assert len(by_kind) >= 5


def test_by_track_covers_three_tracks() -> None:
    summary = candidate_annotation_log_summary()
    by_track = summary["by_track"]
    assert "radio" in by_track
    assert "infrared" in by_track
    assert "anomaly" in by_track


def test_schema_version() -> None:
    summary = candidate_annotation_log_summary()
    assert summary["schema_version"] == CANDIDATE_ANNOTATION_LOG_SCHEMA_VERSION


def test_disclaimer_present_and_provenance() -> None:
    summary = candidate_annotation_log_summary()
    assert "provenance records" in summary["disclaimer"]
    assert summary["disclaimer"] == CANDIDATE_ANNOTATION_LOG_DISCLAIMER


def test_disclaimer_no_detection_language() -> None:
    summary = candidate_annotation_log_summary()
    assert "detection claim" in summary["disclaimer"]
    assert "discovery" not in summary["disclaimer"].lower()


def test_allowed_annotation_kinds_has_five_members() -> None:
    assert len(ALLOWED_ANNOTATION_LOG_KINDS) == 5


def test_allowed_annotation_statuses_has_three_members() -> None:
    assert len(ALLOWED_ANNOTATION_LOG_STATUSES) == 3


def test_fixture_annotation_kinds_in_allowed() -> None:
    entries = load_candidate_annotation_log_entries()
    for e in entries:
        assert e.annotation_kind in ALLOWED_ANNOTATION_LOG_KINDS


def test_fixture_status_values_in_allowed() -> None:
    entries = load_candidate_annotation_log_entries()
    for e in entries:
        assert e.status in ALLOWED_ANNOTATION_LOG_STATUSES


def test_supersedes_entry_id_nullable() -> None:
    entries = load_candidate_annotation_log_entries()
    ann001 = next(e for e in entries if e.entry_id == "ann-001")
    assert ann001.supersedes_entry_id is None


def test_annotation_text_is_present() -> None:
    entries = load_candidate_annotation_log_entries()
    for e in entries:
        assert len(e.annotation_text) > 0


def test_as_dict_returns_required_keys() -> None:
    entries = load_candidate_annotation_log_entries()
    d = entries[0].as_dict()
    assert "entry_id" in d
    assert "candidate_id" in d
    assert "annotation_kind" in d
    assert "status" in d
    assert "annotated_by" in d
    assert "annotated_at" in d
    assert "track" in d
    assert "annotation_text" in d
    assert "supersedes_entry_id" in d


def test_custom_path_argument() -> None:
    entries = load_candidate_annotation_log_entries(FIXTURE_PATH)
    assert len(entries) == 5
    summary = candidate_annotation_log_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_active_entries_span_three_tracks() -> None:
    entries = load_candidate_annotation_log_entries()
    active = [e for e in entries if e.status == "active"]
    tracks = {e.track for e in active}
    assert "radio" in tracks
    assert "infrared" in tracks
    assert "anomaly" in tracks
