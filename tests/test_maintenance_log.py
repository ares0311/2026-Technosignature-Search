"""Tests for maintenance_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.maintenance_log import (
    ALLOWED_MAINTENANCE_KINDS,
    ALLOWED_MAINTENANCE_STATUSES,
    MAINTENANCE_LOG_DISCLAIMER,
    MAINTENANCE_LOG_SCHEMA_VERSION,
    MaintenanceEntry,
    load_maintenance_entries,
    maintenance_log_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "maintenance_log.json"


def test_schema_version() -> None:
    assert MAINTENANCE_LOG_SCHEMA_VERSION == "maintenance_log_v1"


def test_disclaimer_present() -> None:
    assert "does not authorize external submission" in MAINTENANCE_LOG_DISCLAIMER
    assert "does not constitute a detection claim" in MAINTENANCE_LOG_DISCLAIMER


def test_allowed_maintenance_kinds_complete() -> None:
    assert "scheduled_maintenance" in ALLOWED_MAINTENANCE_KINDS
    assert "emergency_repair" in ALLOWED_MAINTENANCE_KINDS
    assert "calibration_service" in ALLOWED_MAINTENANCE_KINDS
    assert "firmware_service" in ALLOWED_MAINTENANCE_KINDS
    assert "inspection" in ALLOWED_MAINTENANCE_KINDS


def test_allowed_statuses_complete() -> None:
    assert "planned" in ALLOWED_MAINTENANCE_STATUSES
    assert "in_progress" in ALLOWED_MAINTENANCE_STATUSES
    assert "completed" in ALLOWED_MAINTENANCE_STATUSES
    assert "deferred" in ALLOWED_MAINTENANCE_STATUSES


def test_load_entries_count() -> None:
    entries = load_maintenance_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_load_entries_types() -> None:
    entries = load_maintenance_entries(FIXTURE_PATH)
    for e in entries:
        assert isinstance(e, MaintenanceEntry)


def test_entry_ids_unique() -> None:
    entries = load_maintenance_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_maintenance_kinds_valid() -> None:
    entries = load_maintenance_entries(FIXTURE_PATH)
    for e in entries:
        assert e.maintenance_kind in ALLOWED_MAINTENANCE_KINDS


def test_statuses_valid() -> None:
    entries = load_maintenance_entries(FIXTURE_PATH)
    for e in entries:
        assert e.status in ALLOWED_MAINTENANCE_STATUSES


def test_completed_count() -> None:
    entries = load_maintenance_entries(FIXTURE_PATH)
    completed = [e for e in entries if e.status == "completed"]
    assert len(completed) == 2


def test_in_progress_count() -> None:
    entries = load_maintenance_entries(FIXTURE_PATH)
    in_progress = [e for e in entries if e.status == "in_progress"]
    assert len(in_progress) == 1


def test_planned_count() -> None:
    entries = load_maintenance_entries(FIXTURE_PATH)
    planned = [e for e in entries if e.status == "planned"]
    assert len(planned) == 1


def test_deferred_count() -> None:
    entries = load_maintenance_entries(FIXTURE_PATH)
    deferred = [e for e in entries if e.status == "deferred"]
    assert len(deferred) == 1


def test_entry_as_dict() -> None:
    entries = load_maintenance_entries(FIXTURE_PATH)
    d = entries[0].as_dict()
    assert "entry_id" in d
    assert "maintenance_kind" in d
    assert "status" in d


def test_summary_schema_version() -> None:
    summary = maintenance_log_summary(FIXTURE_PATH)
    assert summary["schema_version"] == MAINTENANCE_LOG_SCHEMA_VERSION


def test_summary_entry_count() -> None:
    summary = maintenance_log_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_completed_count() -> None:
    summary = maintenance_log_summary(FIXTURE_PATH)
    assert summary["completed_count"] == 2


def test_summary_in_progress_count() -> None:
    summary = maintenance_log_summary(FIXTURE_PATH)
    assert summary["in_progress_count"] == 1


def test_summary_planned_count() -> None:
    summary = maintenance_log_summary(FIXTURE_PATH)
    assert summary["planned_count"] == 1


def test_summary_deferred_count() -> None:
    summary = maintenance_log_summary(FIXTURE_PATH)
    assert summary["deferred_count"] == 1


def test_summary_counts_by_kind() -> None:
    summary = maintenance_log_summary(FIXTURE_PATH)
    assert isinstance(summary["counts_by_kind"], dict)
    assert sum(summary["counts_by_kind"].values()) == 5
