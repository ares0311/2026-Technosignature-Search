"""Tests for candidate_status_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.candidate_status_log import (
    ALLOWED_CANDIDATE_STATUSES,
    ALLOWED_STATUS_TRANSITION_KINDS,
    CANDIDATE_STATUS_LOG_DISCLAIMER,
    CANDIDATE_STATUS_LOG_SCHEMA_VERSION,
    candidate_status_log_summary,
    load_candidate_status_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "candidate_status_log.json"


def test_load_entries_returns_five() -> None:
    entries = load_candidate_status_entries()
    assert len(entries) == 5


def test_all_transition_kinds_present() -> None:
    entries = load_candidate_status_entries()
    kinds = {e.transition_kind for e in entries}
    assert "initial" in kinds
    assert "promotion" in kinds
    assert "hold" in kinds
    assert "archive" in kinds


def test_all_current_statuses_present() -> None:
    entries = load_candidate_status_entries()
    statuses = {e.current_status for e in entries}
    assert "new" in statuses
    assert "active" in statuses
    assert "under_review" in statuses
    assert "on_hold" in statuses
    assert "archived" in statuses


def test_summary_entry_count_five() -> None:
    summary = candidate_status_log_summary()
    assert summary["entry_count"] == 5


def test_active_count_is_one() -> None:
    summary = candidate_status_log_summary()
    assert summary["active_count"] == 1


def test_archived_count_is_one() -> None:
    summary = candidate_status_log_summary()
    assert summary["archived_count"] == 1


def test_counts_by_status_covers_expected_statuses() -> None:
    summary = candidate_status_log_summary()
    by_status = summary["counts_by_status"]
    assert "new" in by_status
    assert "active" in by_status
    assert "under_review" in by_status
    assert "on_hold" in by_status
    assert "archived" in by_status


def test_counts_by_kind_covers_expected_kinds() -> None:
    summary = candidate_status_log_summary()
    by_kind = summary["counts_by_kind"]
    assert "initial" in by_kind
    assert "promotion" in by_kind
    assert "hold" in by_kind
    assert "archive" in by_kind


def test_unique_candidate_count() -> None:
    summary = candidate_status_log_summary()
    assert summary["unique_candidate_count"] == 4


def test_schema_version() -> None:
    summary = candidate_status_log_summary()
    assert summary["schema_version"] == CANDIDATE_STATUS_LOG_SCHEMA_VERSION


def test_disclaimer_present_and_provenance() -> None:
    summary = candidate_status_log_summary()
    assert "provenance records" in summary["disclaimer"]
    assert summary["disclaimer"] == CANDIDATE_STATUS_LOG_DISCLAIMER


def test_disclaimer_no_detection_language() -> None:
    summary = candidate_status_log_summary()
    assert "detection claim" in summary["disclaimer"]
    assert "discovery" not in summary["disclaimer"].lower()


def test_allowed_transition_kinds_has_five_members() -> None:
    assert len(ALLOWED_STATUS_TRANSITION_KINDS) == 5


def test_allowed_candidate_statuses_has_five_members() -> None:
    assert len(ALLOWED_CANDIDATE_STATUSES) == 5


def test_fixture_transition_kinds_in_allowed() -> None:
    entries = load_candidate_status_entries()
    for e in entries:
        assert e.transition_kind in ALLOWED_STATUS_TRANSITION_KINDS


def test_fixture_current_status_values_in_allowed() -> None:
    entries = load_candidate_status_entries()
    for e in entries:
        assert e.current_status in ALLOWED_CANDIDATE_STATUSES


def test_previous_status_nullable_for_initial() -> None:
    entries = load_candidate_status_entries()
    csl001 = next(e for e in entries if e.entry_id == "csl-001")
    assert csl001.transition_kind == "initial"
    assert csl001.previous_status is None


def test_previous_status_set_for_promotion() -> None:
    entries = load_candidate_status_entries()
    csl002 = next(e for e in entries if e.entry_id == "csl-002")
    assert csl002.transition_kind == "promotion"
    assert csl002.previous_status == "new"


def test_as_dict_returns_required_keys() -> None:
    entries = load_candidate_status_entries()
    d = entries[0].as_dict()
    assert "entry_id" in d
    assert "candidate_id" in d
    assert "transition_kind" in d
    assert "current_status" in d
    assert "previous_status" in d
    assert "transitioned_by" in d
    assert "transitioned_at" in d
    assert "track" in d
    assert "reason" in d


def test_custom_path_argument() -> None:
    entries = load_candidate_status_entries(FIXTURE_PATH)
    assert len(entries) == 5
    summary = candidate_status_log_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_entries_span_three_tracks() -> None:
    entries = load_candidate_status_entries()
    tracks = {e.track for e in entries}
    assert "radio" in tracks
    assert "infrared" in tracks
    assert "anomaly" in tracks
