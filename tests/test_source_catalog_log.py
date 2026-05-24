"""Tests for source_catalog_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.source_catalog_log import (
    ALLOWED_CATALOG_KINDS,
    ALLOWED_CATALOG_STATUSES,
    SOURCE_CATALOG_LOG_DISCLAIMER,
    SOURCE_CATALOG_LOG_SCHEMA_VERSION,
    load_source_catalog_entries,
    source_catalog_log_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "source_catalog_log.json"


def test_load_entries_returns_five() -> None:
    entries = load_source_catalog_entries()
    assert len(entries) == 5


def test_all_catalog_kinds_present() -> None:
    entries = load_source_catalog_entries()
    kinds = {e.catalog_kind for e in entries}
    assert "radio_source" in kinds
    assert "infrared" in kinds
    assert "stellar" in kinds
    assert "known_object" in kinds
    assert "known_rfi" in kinds


def test_all_statuses_present() -> None:
    entries = load_source_catalog_entries()
    statuses = {e.status for e in entries}
    assert "matched" in statuses
    assert "queried" in statuses
    assert "no_match" in statuses
    assert "error" in statuses


def test_summary_entry_count_five() -> None:
    summary = source_catalog_log_summary()
    assert summary["entry_count"] == 5


def test_matched_count_is_two() -> None:
    summary = source_catalog_log_summary()
    assert summary["matched_count"] == 2


def test_no_match_count_is_one() -> None:
    summary = source_catalog_log_summary()
    assert summary["no_match_count"] == 1


def test_counts_by_status_covers_all_four() -> None:
    summary = source_catalog_log_summary()
    by_status = summary["counts_by_status"]
    assert set(by_status.keys()) == {"matched", "queried", "no_match", "error"}


def test_counts_by_kind_covers_all_five() -> None:
    summary = source_catalog_log_summary()
    by_kind = summary["counts_by_kind"]
    for kind in ALLOWED_CATALOG_KINDS:
        assert kind in by_kind


def test_schema_version() -> None:
    summary = source_catalog_log_summary()
    assert summary["schema_version"] == SOURCE_CATALOG_LOG_SCHEMA_VERSION


def test_disclaimer_present_and_provenance() -> None:
    summary = source_catalog_log_summary()
    assert "provenance records" in summary["disclaimer"]
    assert summary["disclaimer"] == SOURCE_CATALOG_LOG_DISCLAIMER


def test_disclaimer_no_detection_language() -> None:
    summary = source_catalog_log_summary()
    assert "detection claim" in summary["disclaimer"]
    assert "discovery" not in summary["disclaimer"].lower()


def test_allowed_catalog_kinds_has_five_members() -> None:
    assert len(ALLOWED_CATALOG_KINDS) == 5


def test_allowed_catalog_statuses_has_four_members() -> None:
    assert len(ALLOWED_CATALOG_STATUSES) == 4


def test_fixture_catalog_kinds_in_allowed() -> None:
    entries = load_source_catalog_entries()
    for e in entries:
        assert e.catalog_kind in ALLOWED_CATALOG_KINDS


def test_fixture_status_values_in_allowed() -> None:
    entries = load_source_catalog_entries()
    for e in entries:
        assert e.status in ALLOWED_CATALOG_STATUSES


def test_match_count_nullable() -> None:
    entries = load_source_catalog_entries()
    scl001 = next(e for e in entries if e.entry_id == "scl-001")
    assert scl001.match_count == 2
    scl003 = next(e for e in entries if e.entry_id == "scl-003")
    assert scl003.match_count is None


def test_as_dict_returns_required_keys() -> None:
    entries = load_source_catalog_entries()
    d = entries[0].as_dict()
    for key in ("entry_id", "candidate_id", "catalog_kind", "status",
                "catalog_name", "queried_by", "queried_at", "track",
                "match_count", "notes"):
        assert key in d


def test_custom_path_argument() -> None:
    entries = load_source_catalog_entries(FIXTURE_PATH)
    assert len(entries) == 5
    summary = source_catalog_log_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_tracks_cover_radio_infrared_anomaly() -> None:
    entries = load_source_catalog_entries()
    tracks = {e.track for e in entries}
    assert "radio" in tracks
    assert "infrared" in tracks
    assert "anomaly" in tracks


def test_radio_source_kind_count_is_one() -> None:
    summary = source_catalog_log_summary()
    assert summary["counts_by_kind"].get("radio_source", 0) == 1
