"""Tests for instrument_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.instrument_log import (
    ALLOWED_EVENT_KINDS,
    ALLOWED_INSTRUMENT_KINDS,
    INSTRUMENT_LOG_DISCLAIMER,
    INSTRUMENT_LOG_SCHEMA_VERSION,
    instrument_log_summary,
    load_instrument_log_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "instrument_log.json"


def test_load_instrument_log_entries_returns_list() -> None:
    entries = load_instrument_log_entries()
    assert isinstance(entries, list)


def test_entry_count_is_five() -> None:
    entries = load_instrument_log_entries()
    assert len(entries) == 5


def test_all_instrument_kinds_present() -> None:
    entries = load_instrument_log_entries()
    kinds = {e.instrument_kind for e in entries}
    # Verify fixture covers all 4 instrument kinds
    assert "radio_telescope" in kinds
    assert "optical_telescope" in kinds
    assert "archive_node" in kinds
    assert "data_pipeline" in kinds


def test_all_event_kinds_present() -> None:
    entries = load_instrument_log_entries()
    event_kinds = {e.event_kind for e in entries}
    assert "online" in event_kinds
    assert "offline" in event_kinds
    assert "degraded" in event_kinds
    assert "maintenance" in event_kinds
    assert "calibrating" in event_kinds


def test_summary_entry_count() -> None:
    summary = instrument_log_summary()
    assert summary["entry_count"] == 5


def test_online_count_is_one() -> None:
    summary = instrument_log_summary()
    assert summary["online_count"] == 1


def test_offline_count_is_one() -> None:
    summary = instrument_log_summary()
    assert summary["offline_count"] == 1


def test_degraded_count_is_one() -> None:
    summary = instrument_log_summary()
    assert summary["degraded_count"] == 1


def test_maintenance_count_is_one() -> None:
    summary = instrument_log_summary()
    assert summary["maintenance_count"] == 1


def test_calibrating_count_is_one() -> None:
    summary = instrument_log_summary()
    assert summary["calibrating_count"] == 1


def test_by_event_kind_covers_all_five() -> None:
    summary = instrument_log_summary()
    by_event = summary["by_event_kind"]
    assert set(by_event.keys()) == {"online", "offline", "degraded", "maintenance", "calibrating"}


def test_by_instrument_kind_covers_at_least_four() -> None:
    summary = instrument_log_summary()
    by_kind = summary["by_instrument_kind"]
    assert len(by_kind) >= 4


def test_schema_version() -> None:
    summary = instrument_log_summary()
    assert summary["schema_version"] == INSTRUMENT_LOG_SCHEMA_VERSION


def test_disclaimer_present_and_scheduling() -> None:
    summary = instrument_log_summary()
    assert "scheduling records" in summary["disclaimer"]
    assert summary["disclaimer"] == INSTRUMENT_LOG_DISCLAIMER


def test_resolved_utc_nullable_ilog001() -> None:
    entries = load_instrument_log_entries()
    ilog001 = next(e for e in entries if e.log_id == "ilog-001")
    assert ilog001.resolved_utc is None


def test_resolved_utc_not_none_ilog002() -> None:
    entries = load_instrument_log_entries()
    ilog002 = next(e for e in entries if e.log_id == "ilog-002")
    assert ilog002.resolved_utc is not None


def test_notes_field_present() -> None:
    entries = load_instrument_log_entries()
    for e in entries:
        assert isinstance(e.notes, str)


def test_as_dict_returns_required_keys() -> None:
    entries = load_instrument_log_entries()
    d = entries[0].as_dict()
    assert "log_id" in d
    assert "instrument_id" in d
    assert "instrument_kind" in d
    assert "event_kind" in d
    assert "reported_by" in d
    assert "reported_utc" in d
    assert "resolved_utc" in d
    assert "notes" in d


def test_allowed_instrument_kinds_has_four_members() -> None:
    assert len(ALLOWED_INSTRUMENT_KINDS) == 4


def test_allowed_event_kinds_has_five_members() -> None:
    assert len(ALLOWED_EVENT_KINDS) == 5


def test_fixture_instrument_kinds_in_allowed() -> None:
    entries = load_instrument_log_entries()
    for e in entries:
        assert e.instrument_kind in ALLOWED_INSTRUMENT_KINDS


def test_fixture_event_kinds_in_allowed() -> None:
    entries = load_instrument_log_entries()
    for e in entries:
        assert e.event_kind in ALLOWED_EVENT_KINDS


def test_summary_no_detection_language() -> None:
    summary = instrument_log_summary()
    text = str(summary)
    assert "detection" not in text.lower() or "detection claim" in summary["disclaimer"]
    assert "discovery" not in summary["disclaimer"].lower()


def test_custom_path_argument() -> None:
    entries = load_instrument_log_entries(FIXTURE_PATH)
    assert len(entries) == 5
    summary = instrument_log_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5
