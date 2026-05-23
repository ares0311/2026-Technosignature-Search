"""Tests for beam_configuration_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.beam_configuration_log import (
    ALLOWED_BEAM_KINDS,
    ALLOWED_BEAM_STATUSES,
    BEAM_CONFIGURATION_LOG_DISCLAIMER,
    BEAM_CONFIGURATION_LOG_SCHEMA_VERSION,
    beam_configuration_log_summary,
    load_beam_configuration_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "beam_configuration_log.json"


def test_load_entries_returns_five() -> None:
    entries = load_beam_configuration_entries()
    assert len(entries) == 5


def test_all_beam_kinds_present() -> None:
    entries = load_beam_configuration_entries()
    kinds = {e.beam_kind for e in entries}
    assert "primary_beam" in kinds
    assert "sidelobe" in kinds
    assert "calibrator_beam" in kinds
    assert "off_source" in kinds


def test_all_statuses_present() -> None:
    entries = load_beam_configuration_entries()
    statuses = {e.status for e in entries}
    assert "applied" in statuses
    assert "configured" in statuses
    assert "superseded" in statuses
    assert "failed" in statuses


def test_summary_entry_count_five() -> None:
    summary = beam_configuration_log_summary()
    assert summary["entry_count"] == 5


def test_applied_count_is_two() -> None:
    summary = beam_configuration_log_summary()
    assert summary["applied_count"] == 2


def test_configured_count_is_one() -> None:
    summary = beam_configuration_log_summary()
    assert summary["configured_count"] == 1


def test_counts_by_status_covers_all_four() -> None:
    summary = beam_configuration_log_summary()
    by_status = summary["counts_by_status"]
    assert set(by_status.keys()) == {"applied", "configured", "superseded", "failed"}


def test_counts_by_kind_covers_expected_kinds() -> None:
    summary = beam_configuration_log_summary()
    by_kind = summary["counts_by_kind"]
    assert "primary_beam" in by_kind
    assert "sidelobe" in by_kind
    assert "calibrator_beam" in by_kind
    assert "off_source" in by_kind


def test_schema_version() -> None:
    summary = beam_configuration_log_summary()
    assert summary["schema_version"] == BEAM_CONFIGURATION_LOG_SCHEMA_VERSION


def test_disclaimer_present_and_provenance() -> None:
    summary = beam_configuration_log_summary()
    assert "provenance records" in summary["disclaimer"]
    assert summary["disclaimer"] == BEAM_CONFIGURATION_LOG_DISCLAIMER


def test_disclaimer_no_detection_language() -> None:
    summary = beam_configuration_log_summary()
    assert "detection claim" in summary["disclaimer"]
    assert "discovery" not in summary["disclaimer"].lower()


def test_allowed_beam_kinds_has_five_members() -> None:
    assert len(ALLOWED_BEAM_KINDS) == 5


def test_allowed_beam_statuses_has_four_members() -> None:
    assert len(ALLOWED_BEAM_STATUSES) == 4


def test_fixture_beam_kinds_in_allowed() -> None:
    entries = load_beam_configuration_entries()
    for e in entries:
        assert e.beam_kind in ALLOWED_BEAM_KINDS


def test_fixture_status_values_in_allowed() -> None:
    entries = load_beam_configuration_entries()
    for e in entries:
        assert e.status in ALLOWED_BEAM_STATUSES


def test_azimuth_nullable() -> None:
    entries = load_beam_configuration_entries()
    bcl001 = next(e for e in entries if e.entry_id == "bcl-001")
    assert bcl001.azimuth_deg == 45.0
    bcl004 = next(e for e in entries if e.entry_id == "bcl-004")
    assert bcl004.azimuth_deg is None


def test_elevation_nullable() -> None:
    entries = load_beam_configuration_entries()
    bcl001 = next(e for e in entries if e.entry_id == "bcl-001")
    assert bcl001.elevation_deg == 30.0
    bcl005 = next(e for e in entries if e.entry_id == "bcl-005")
    assert bcl005.elevation_deg is None


def test_as_dict_returns_required_keys() -> None:
    entries = load_beam_configuration_entries()
    d = entries[0].as_dict()
    for key in ("entry_id", "candidate_id", "beam_kind", "status",
                "configured_by", "configured_at", "track",
                "azimuth_deg", "elevation_deg", "notes"):
        assert key in d


def test_custom_path_argument() -> None:
    entries = load_beam_configuration_entries(FIXTURE_PATH)
    assert len(entries) == 5
    summary = beam_configuration_log_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_all_entries_are_radio_track() -> None:
    entries = load_beam_configuration_entries()
    tracks = {e.track for e in entries}
    assert tracks == {"radio"}


def test_primary_beam_count_is_two() -> None:
    summary = beam_configuration_log_summary()
    assert summary["counts_by_kind"].get("primary_beam", 0) == 2
