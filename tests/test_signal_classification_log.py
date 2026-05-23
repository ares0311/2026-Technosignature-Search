"""Tests for signal_classification_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.signal_classification_log import (
    ALLOWED_CLASSIFICATION_KINDS,
    ALLOWED_CLASSIFICATION_STATUSES,
    SIGNAL_CLASSIFICATION_DISCLAIMER,
    SIGNAL_CLASSIFICATION_SCHEMA_VERSION,
    load_signal_classification_entries,
    signal_classification_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "signal_classification_log.json"


def test_load_entries_returns_five() -> None:
    entries = load_signal_classification_entries()
    assert len(entries) == 5


def test_all_classification_kinds_present() -> None:
    entries = load_signal_classification_entries()
    kinds = {e.classification_kind for e in entries}
    assert "narrowband" in kinds
    assert "broadband" in kinds
    assert "pulsed" in kinds
    assert "intermittent" in kinds
    assert "unknown" in kinds


def test_all_statuses_present() -> None:
    entries = load_signal_classification_entries()
    statuses = {e.status for e in entries}
    assert "classified" in statuses
    assert "unclassified" in statuses
    assert "ambiguous" in statuses
    assert "reclassified" in statuses


def test_summary_entry_count_five() -> None:
    summary = signal_classification_summary()
    assert summary["entry_count"] == 5


def test_classified_count_is_two() -> None:
    summary = signal_classification_summary()
    assert summary["classified_count"] == 2


def test_unclassified_count_is_one() -> None:
    summary = signal_classification_summary()
    assert summary["unclassified_count"] == 1


def test_ambiguous_count_is_one() -> None:
    summary = signal_classification_summary()
    assert summary["ambiguous_count"] == 1


def test_reclassified_count_is_one() -> None:
    summary = signal_classification_summary()
    assert summary["reclassified_count"] == 1


def test_by_status_covers_all_four() -> None:
    summary = signal_classification_summary()
    by_status = summary["by_status"]
    assert set(by_status.keys()) == {"classified", "unclassified", "ambiguous", "reclassified"}


def test_by_classification_kind_covers_all_five() -> None:
    summary = signal_classification_summary()
    by_kind = summary["by_classification_kind"]
    assert len(by_kind) >= 5


def test_by_track_covers_three_tracks() -> None:
    summary = signal_classification_summary()
    by_track = summary["by_track"]
    assert "radio" in by_track
    assert "infrared" in by_track
    assert "anomaly" in by_track


def test_schema_version() -> None:
    summary = signal_classification_summary()
    assert summary["schema_version"] == SIGNAL_CLASSIFICATION_SCHEMA_VERSION


def test_disclaimer_present_and_provenance() -> None:
    summary = signal_classification_summary()
    assert "provenance records" in summary["disclaimer"]
    assert summary["disclaimer"] == SIGNAL_CLASSIFICATION_DISCLAIMER


def test_disclaimer_no_detection_language() -> None:
    summary = signal_classification_summary()
    assert "detection claim" in summary["disclaimer"]
    assert "discovery" not in summary["disclaimer"].lower()


def test_allowed_classification_kinds_has_five_members() -> None:
    assert len(ALLOWED_CLASSIFICATION_KINDS) == 5


def test_allowed_classification_statuses_has_four_members() -> None:
    assert len(ALLOWED_CLASSIFICATION_STATUSES) == 4


def test_fixture_classification_kinds_in_allowed() -> None:
    entries = load_signal_classification_entries()
    for e in entries:
        assert e.classification_kind in ALLOWED_CLASSIFICATION_KINDS


def test_fixture_status_values_in_allowed() -> None:
    entries = load_signal_classification_entries()
    for e in entries:
        assert e.status in ALLOWED_CLASSIFICATION_STATUSES


def test_as_dict_returns_required_keys() -> None:
    entries = load_signal_classification_entries()
    d = entries[0].as_dict()
    assert "entry_id" in d
    assert "candidate_id" in d
    assert "classification_kind" in d
    assert "status" in d
    assert "classified_by" in d
    assert "classified_at" in d
    assert "track" in d
    assert "notes" in d


def test_custom_path_argument() -> None:
    entries = load_signal_classification_entries(FIXTURE_PATH)
    assert len(entries) == 5
    summary = signal_classification_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_reclassified_entry_is_radio() -> None:
    entries = load_signal_classification_entries()
    reclassified = [e for e in entries if e.status == "reclassified"]
    assert len(reclassified) == 1
    assert reclassified[0].track == "radio"
    assert reclassified[0].classification_kind == "pulsed"
