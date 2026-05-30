"""Tests for hardware_fault_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.hardware_fault_log import (
    ALLOWED_FAULT_KINDS,
    ALLOWED_FAULT_STATUSES,
    HARDWARE_FAULT_LOG_DISCLAIMER,
    HARDWARE_FAULT_LOG_SCHEMA_VERSION,
    HardwareFaultEntry,
    hardware_fault_summary,
    load_hardware_fault_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "hardware_fault_log.json"


def test_schema_version() -> None:
    assert HARDWARE_FAULT_LOG_SCHEMA_VERSION == "hardware_fault_log_v1"


def test_disclaimer_present() -> None:
    assert "does not authorize external submission" in HARDWARE_FAULT_LOG_DISCLAIMER
    assert "does not constitute a detection claim" in HARDWARE_FAULT_LOG_DISCLAIMER


def test_allowed_fault_kinds_complete() -> None:
    assert "cpu_fault" in ALLOWED_FAULT_KINDS
    assert "memory_fault" in ALLOWED_FAULT_KINDS
    assert "disk_fault" in ALLOWED_FAULT_KINDS
    assert "network_fault" in ALLOWED_FAULT_KINDS
    assert "psu_fault" in ALLOWED_FAULT_KINDS


def test_allowed_statuses_complete() -> None:
    assert "detected" in ALLOWED_FAULT_STATUSES
    assert "diagnosed" in ALLOWED_FAULT_STATUSES
    assert "repaired" in ALLOWED_FAULT_STATUSES
    assert "deferred" in ALLOWED_FAULT_STATUSES


def test_load_entries_count() -> None:
    entries = load_hardware_fault_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_load_entries_types() -> None:
    entries = load_hardware_fault_entries(FIXTURE_PATH)
    for e in entries:
        assert isinstance(e, HardwareFaultEntry)


def test_entry_ids_unique() -> None:
    entries = load_hardware_fault_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_fault_kinds_valid() -> None:
    entries = load_hardware_fault_entries(FIXTURE_PATH)
    for e in entries:
        assert e.fault_kind in ALLOWED_FAULT_KINDS


def test_statuses_valid() -> None:
    entries = load_hardware_fault_entries(FIXTURE_PATH)
    for e in entries:
        assert e.status in ALLOWED_FAULT_STATUSES


def test_detected_count() -> None:
    entries = load_hardware_fault_entries(FIXTURE_PATH)
    detected = [e for e in entries if e.status == "detected"]
    assert len(detected) == 2


def test_diagnosed_count() -> None:
    entries = load_hardware_fault_entries(FIXTURE_PATH)
    diagnosed = [e for e in entries if e.status == "diagnosed"]
    assert len(diagnosed) == 1


def test_repaired_count() -> None:
    entries = load_hardware_fault_entries(FIXTURE_PATH)
    repaired = [e for e in entries if e.status == "repaired"]
    assert len(repaired) == 1


def test_deferred_count() -> None:
    entries = load_hardware_fault_entries(FIXTURE_PATH)
    deferred = [e for e in entries if e.status == "deferred"]
    assert len(deferred) == 1


def test_entry_as_dict() -> None:
    entries = load_hardware_fault_entries(FIXTURE_PATH)
    d = entries[0].as_dict()
    assert "entry_id" in d
    assert "fault_kind" in d
    assert "status" in d


def test_summary_schema_version() -> None:
    summary = hardware_fault_summary(FIXTURE_PATH)
    assert summary["schema_version"] == HARDWARE_FAULT_LOG_SCHEMA_VERSION


def test_summary_entry_count() -> None:
    summary = hardware_fault_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_detected_count() -> None:
    summary = hardware_fault_summary(FIXTURE_PATH)
    assert summary["detected_count"] == 2


def test_summary_diagnosed_count() -> None:
    summary = hardware_fault_summary(FIXTURE_PATH)
    assert summary["diagnosed_count"] == 1


def test_summary_repaired_count() -> None:
    summary = hardware_fault_summary(FIXTURE_PATH)
    assert summary["repaired_count"] == 1


def test_summary_deferred_count() -> None:
    summary = hardware_fault_summary(FIXTURE_PATH)
    assert summary["deferred_count"] == 1


def test_summary_counts_by_kind() -> None:
    summary = hardware_fault_summary(FIXTURE_PATH)
    assert isinstance(summary["counts_by_kind"], dict)
    assert sum(summary["counts_by_kind"].values()) == 5
