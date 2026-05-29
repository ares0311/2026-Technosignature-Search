"""Tests for cooling_system_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.cooling_system_log import (
    ALLOWED_COOLING_KINDS,
    ALLOWED_COOLING_STATUSES,
    COOLING_SYSTEM_LOG_DISCLAIMER,
    COOLING_SYSTEM_LOG_SCHEMA_VERSION,
    CoolingSystemEntry,
    cooling_system_summary,
    load_cooling_system_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "cooling_system_log.json"


def test_schema_version() -> None:
    assert COOLING_SYSTEM_LOG_SCHEMA_VERSION == "cooling_system_log_v1"


def test_disclaimer_present() -> None:
    assert "does not authorize external submission" in COOLING_SYSTEM_LOG_DISCLAIMER
    assert "does not constitute a detection claim" in COOLING_SYSTEM_LOG_DISCLAIMER


def test_allowed_cooling_kinds_complete() -> None:
    assert "cooldown_start" in ALLOWED_COOLING_KINDS
    assert "cooldown_complete" in ALLOWED_COOLING_KINDS
    assert "warmup_event" in ALLOWED_COOLING_KINDS
    assert "temperature_alarm" in ALLOWED_COOLING_KINDS
    assert "helium_refill" in ALLOWED_COOLING_KINDS


def test_allowed_statuses_complete() -> None:
    assert "operating" in ALLOWED_COOLING_STATUSES
    assert "warning" in ALLOWED_COOLING_STATUSES
    assert "fault" in ALLOWED_COOLING_STATUSES
    assert "maintenance" in ALLOWED_COOLING_STATUSES


def test_load_entries_count() -> None:
    entries = load_cooling_system_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_load_entries_types() -> None:
    entries = load_cooling_system_entries(FIXTURE_PATH)
    for e in entries:
        assert isinstance(e, CoolingSystemEntry)


def test_entry_ids_unique() -> None:
    entries = load_cooling_system_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_cooling_kinds_valid() -> None:
    entries = load_cooling_system_entries(FIXTURE_PATH)
    for e in entries:
        assert e.cooling_kind in ALLOWED_COOLING_KINDS


def test_statuses_valid() -> None:
    entries = load_cooling_system_entries(FIXTURE_PATH)
    for e in entries:
        assert e.status in ALLOWED_COOLING_STATUSES


def test_operating_count() -> None:
    entries = load_cooling_system_entries(FIXTURE_PATH)
    operating = [e for e in entries if e.status == "operating"]
    assert len(operating) == 2


def test_warning_count() -> None:
    entries = load_cooling_system_entries(FIXTURE_PATH)
    warning = [e for e in entries if e.status == "warning"]
    assert len(warning) == 1


def test_fault_count() -> None:
    entries = load_cooling_system_entries(FIXTURE_PATH)
    fault = [e for e in entries if e.status == "fault"]
    assert len(fault) == 1


def test_maintenance_count() -> None:
    entries = load_cooling_system_entries(FIXTURE_PATH)
    maintenance = [e for e in entries if e.status == "maintenance"]
    assert len(maintenance) == 1


def test_entry_as_dict() -> None:
    entries = load_cooling_system_entries(FIXTURE_PATH)
    d = entries[0].as_dict()
    assert "entry_id" in d
    assert "cooling_kind" in d
    assert "status" in d


def test_summary_schema_version() -> None:
    summary = cooling_system_summary(FIXTURE_PATH)
    assert summary["schema_version"] == COOLING_SYSTEM_LOG_SCHEMA_VERSION


def test_summary_entry_count() -> None:
    summary = cooling_system_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_operating_count() -> None:
    summary = cooling_system_summary(FIXTURE_PATH)
    assert summary["operating_count"] == 2


def test_summary_warning_count() -> None:
    summary = cooling_system_summary(FIXTURE_PATH)
    assert summary["warning_count"] == 1


def test_summary_fault_count() -> None:
    summary = cooling_system_summary(FIXTURE_PATH)
    assert summary["fault_count"] == 1


def test_summary_maintenance_count() -> None:
    summary = cooling_system_summary(FIXTURE_PATH)
    assert summary["maintenance_count"] == 1


def test_summary_counts_by_kind() -> None:
    summary = cooling_system_summary(FIXTURE_PATH)
    assert isinstance(summary["counts_by_kind"], dict)
    assert sum(summary["counts_by_kind"].values()) == 5
