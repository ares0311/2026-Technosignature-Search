"""Tests for time_synchronization_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.time_synchronization_log import (
    ALLOWED_SYNC_KINDS,
    ALLOWED_SYNC_STATUSES,
    TIME_SYNCHRONIZATION_LOG_DISCLAIMER,
    TIME_SYNCHRONIZATION_LOG_SCHEMA_VERSION,
    TimeSynchronizationEntry,
    load_time_synchronization_entries,
    time_synchronization_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "time_synchronization_log.json"


def test_schema_version() -> None:
    assert TIME_SYNCHRONIZATION_LOG_SCHEMA_VERSION == "time_synchronization_log_v1"


def test_disclaimer_present() -> None:
    assert "does not authorize external submission" in TIME_SYNCHRONIZATION_LOG_DISCLAIMER
    assert "does not constitute a detection claim" in TIME_SYNCHRONIZATION_LOG_DISCLAIMER


def test_allowed_sync_kinds_complete() -> None:
    assert "ntp_sync" in ALLOWED_SYNC_KINDS
    assert "gps_sync" in ALLOWED_SYNC_KINDS
    assert "manual_correction" in ALLOWED_SYNC_KINDS
    assert "drift_check" in ALLOWED_SYNC_KINDS
    assert "epoch_reset" in ALLOWED_SYNC_KINDS


def test_allowed_statuses_complete() -> None:
    assert "synchronized" in ALLOWED_SYNC_STATUSES
    assert "drifted" in ALLOWED_SYNC_STATUSES
    assert "failed" in ALLOWED_SYNC_STATUSES
    assert "not_required" in ALLOWED_SYNC_STATUSES


def test_load_entries_count() -> None:
    entries = load_time_synchronization_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_load_entries_types() -> None:
    entries = load_time_synchronization_entries(FIXTURE_PATH)
    for e in entries:
        assert isinstance(e, TimeSynchronizationEntry)


def test_entry_ids_unique() -> None:
    entries = load_time_synchronization_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_sync_kinds_valid() -> None:
    entries = load_time_synchronization_entries(FIXTURE_PATH)
    for e in entries:
        assert e.sync_kind in ALLOWED_SYNC_KINDS


def test_statuses_valid() -> None:
    entries = load_time_synchronization_entries(FIXTURE_PATH)
    for e in entries:
        assert e.status in ALLOWED_SYNC_STATUSES


def test_synchronized_count() -> None:
    entries = load_time_synchronization_entries(FIXTURE_PATH)
    synchronized = [e for e in entries if e.status == "synchronized"]
    assert len(synchronized) == 2


def test_drifted_count() -> None:
    entries = load_time_synchronization_entries(FIXTURE_PATH)
    drifted = [e for e in entries if e.status == "drifted"]
    assert len(drifted) == 1


def test_failed_count() -> None:
    entries = load_time_synchronization_entries(FIXTURE_PATH)
    failed = [e for e in entries if e.status == "failed"]
    assert len(failed) == 1


def test_not_required_count() -> None:
    entries = load_time_synchronization_entries(FIXTURE_PATH)
    not_required = [e for e in entries if e.status == "not_required"]
    assert len(not_required) == 1


def test_entry_as_dict() -> None:
    entries = load_time_synchronization_entries(FIXTURE_PATH)
    d = entries[0].as_dict()
    assert "entry_id" in d
    assert "sync_kind" in d
    assert "status" in d


def test_summary_schema_version() -> None:
    summary = time_synchronization_summary(FIXTURE_PATH)
    assert summary["schema_version"] == TIME_SYNCHRONIZATION_LOG_SCHEMA_VERSION


def test_summary_entry_count() -> None:
    summary = time_synchronization_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_synchronized_count() -> None:
    summary = time_synchronization_summary(FIXTURE_PATH)
    assert summary["synchronized_count"] == 2


def test_summary_drifted_count() -> None:
    summary = time_synchronization_summary(FIXTURE_PATH)
    assert summary["drifted_count"] == 1


def test_summary_failed_count() -> None:
    summary = time_synchronization_summary(FIXTURE_PATH)
    assert summary["failed_count"] == 1


def test_summary_not_required_count() -> None:
    summary = time_synchronization_summary(FIXTURE_PATH)
    assert summary["not_required_count"] == 1


def test_summary_counts_by_kind() -> None:
    summary = time_synchronization_summary(FIXTURE_PATH)
    assert isinstance(summary["counts_by_kind"], dict)
    assert sum(summary["counts_by_kind"].values()) == 5
