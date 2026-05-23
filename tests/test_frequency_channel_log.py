"""Tests for frequency_channel_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.frequency_channel_log import (
    ALLOWED_CHANNEL_KINDS,
    ALLOWED_CHANNEL_STATUSES,
    FREQUENCY_CHANNEL_LOG_DISCLAIMER,
    FREQUENCY_CHANNEL_LOG_SCHEMA_VERSION,
    frequency_channel_log_summary,
    load_frequency_channel_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "frequency_channel_log.json"


def test_load_entries_returns_five() -> None:
    entries = load_frequency_channel_entries()
    assert len(entries) == 5


def test_all_channel_kinds_present() -> None:
    entries = load_frequency_channel_entries()
    kinds = {e.channel_kind for e in entries}
    assert "primary" in kinds
    assert "backup" in kinds
    assert "rfi_free" in kinds
    assert "calibration" in kinds


def test_all_statuses_present() -> None:
    entries = load_frequency_channel_entries()
    statuses = {e.status for e in entries}
    assert "active" in statuses
    assert "flagged" in statuses
    assert "reserved" in statuses
    assert "disabled" in statuses


def test_summary_entry_count_five() -> None:
    summary = frequency_channel_log_summary()
    assert summary["entry_count"] == 5


def test_active_count_is_two() -> None:
    summary = frequency_channel_log_summary()
    assert summary["active_count"] == 2


def test_flagged_count_is_one() -> None:
    summary = frequency_channel_log_summary()
    assert summary["flagged_count"] == 1


def test_counts_by_status_covers_all_four() -> None:
    summary = frequency_channel_log_summary()
    by_status = summary["counts_by_status"]
    assert set(by_status.keys()) == {"active", "flagged", "reserved", "disabled"}


def test_counts_by_kind_covers_expected_kinds() -> None:
    summary = frequency_channel_log_summary()
    by_kind = summary["counts_by_kind"]
    assert "primary" in by_kind
    assert "backup" in by_kind
    assert "rfi_free" in by_kind
    assert "calibration" in by_kind


def test_schema_version() -> None:
    summary = frequency_channel_log_summary()
    assert summary["schema_version"] == FREQUENCY_CHANNEL_LOG_SCHEMA_VERSION


def test_disclaimer_present_and_provenance() -> None:
    summary = frequency_channel_log_summary()
    assert "provenance records" in summary["disclaimer"]
    assert summary["disclaimer"] == FREQUENCY_CHANNEL_LOG_DISCLAIMER


def test_disclaimer_no_detection_language() -> None:
    summary = frequency_channel_log_summary()
    assert "detection claim" in summary["disclaimer"]
    assert "discovery" not in summary["disclaimer"].lower()


def test_allowed_channel_kinds_has_five_members() -> None:
    assert len(ALLOWED_CHANNEL_KINDS) == 5


def test_allowed_channel_statuses_has_four_members() -> None:
    assert len(ALLOWED_CHANNEL_STATUSES) == 4


def test_fixture_channel_kinds_in_allowed() -> None:
    entries = load_frequency_channel_entries()
    for e in entries:
        assert e.channel_kind in ALLOWED_CHANNEL_KINDS


def test_fixture_status_values_in_allowed() -> None:
    entries = load_frequency_channel_entries()
    for e in entries:
        assert e.status in ALLOWED_CHANNEL_STATUSES


def test_frequency_mhz_is_float() -> None:
    entries = load_frequency_channel_entries()
    for e in entries:
        assert isinstance(e.frequency_mhz, float)


def test_bandwidth_mhz_nullable() -> None:
    entries = load_frequency_channel_entries()
    fcl001 = next(e for e in entries if e.entry_id == "fcl-001")
    assert fcl001.bandwidth_mhz == 0.5
    fcl002 = next(e for e in entries if e.entry_id == "fcl-002")
    assert fcl002.bandwidth_mhz is None


def test_as_dict_returns_required_keys() -> None:
    entries = load_frequency_channel_entries()
    d = entries[0].as_dict()
    assert "entry_id" in d
    assert "candidate_id" in d
    assert "channel_kind" in d
    assert "status" in d
    assert "frequency_mhz" in d
    assert "bandwidth_mhz" in d
    assert "recorded_by" in d
    assert "recorded_at" in d
    assert "track" in d
    assert "notes" in d


def test_custom_path_argument() -> None:
    entries = load_frequency_channel_entries(FIXTURE_PATH)
    assert len(entries) == 5
    summary = frequency_channel_log_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_all_entries_are_radio_track() -> None:
    entries = load_frequency_channel_entries()
    tracks = {e.track for e in entries}
    assert tracks == {"radio"}


def test_primary_kind_count_is_two() -> None:
    summary = frequency_channel_log_summary()
    assert summary["counts_by_kind"].get("primary", 0) == 2
