"""Tests for scheduling_conflict_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.scheduling_conflict_log import (
    ALLOWED_CONFLICT_KINDS,
    ALLOWED_CONFLICT_STATUSES,
    SCHEDULING_CONFLICT_LOG_DISCLAIMER,
    SCHEDULING_CONFLICT_LOG_SCHEMA_VERSION,
    SchedulingConflictEntry,
    load_scheduling_conflict_entries,
    scheduling_conflict_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "scheduling_conflict_log.json"


def test_schema_version() -> None:
    assert SCHEDULING_CONFLICT_LOG_SCHEMA_VERSION == "scheduling_conflict_log_v1"


def test_disclaimer_present() -> None:
    assert "does not authorize external submission" in SCHEDULING_CONFLICT_LOG_DISCLAIMER
    assert "does not constitute a detection claim" in SCHEDULING_CONFLICT_LOG_DISCLAIMER


def test_allowed_conflict_kinds_complete() -> None:
    assert "time_slot_overlap" in ALLOWED_CONFLICT_KINDS
    assert "resource_contention" in ALLOWED_CONFLICT_KINDS
    assert "priority_conflict" in ALLOWED_CONFLICT_KINDS
    assert "maintenance_window" in ALLOWED_CONFLICT_KINDS
    assert "weather_hold" in ALLOWED_CONFLICT_KINDS


def test_allowed_statuses_complete() -> None:
    assert "detected" in ALLOWED_CONFLICT_STATUSES
    assert "resolved" in ALLOWED_CONFLICT_STATUSES
    assert "escalated" in ALLOWED_CONFLICT_STATUSES
    assert "deferred" in ALLOWED_CONFLICT_STATUSES


def test_load_entries_count() -> None:
    entries = load_scheduling_conflict_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_load_entries_types() -> None:
    entries = load_scheduling_conflict_entries(FIXTURE_PATH)
    for e in entries:
        assert isinstance(e, SchedulingConflictEntry)


def test_entry_ids_unique() -> None:
    entries = load_scheduling_conflict_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_conflict_kinds_valid() -> None:
    entries = load_scheduling_conflict_entries(FIXTURE_PATH)
    for e in entries:
        assert e.conflict_kind in ALLOWED_CONFLICT_KINDS


def test_statuses_valid() -> None:
    entries = load_scheduling_conflict_entries(FIXTURE_PATH)
    for e in entries:
        assert e.status in ALLOWED_CONFLICT_STATUSES


def test_detected_count() -> None:
    entries = load_scheduling_conflict_entries(FIXTURE_PATH)
    detected = [e for e in entries if e.status == "detected"]
    assert len(detected) == 2


def test_resolved_count() -> None:
    entries = load_scheduling_conflict_entries(FIXTURE_PATH)
    resolved = [e for e in entries if e.status == "resolved"]
    assert len(resolved) == 1


def test_escalated_count() -> None:
    entries = load_scheduling_conflict_entries(FIXTURE_PATH)
    escalated = [e for e in entries if e.status == "escalated"]
    assert len(escalated) == 1


def test_deferred_count() -> None:
    entries = load_scheduling_conflict_entries(FIXTURE_PATH)
    deferred = [e for e in entries if e.status == "deferred"]
    assert len(deferred) == 1


def test_entry_as_dict() -> None:
    entries = load_scheduling_conflict_entries(FIXTURE_PATH)
    d = entries[0].as_dict()
    assert "entry_id" in d
    assert "conflict_kind" in d
    assert "status" in d


def test_summary_schema_version() -> None:
    summary = scheduling_conflict_summary(FIXTURE_PATH)
    assert summary["schema_version"] == SCHEDULING_CONFLICT_LOG_SCHEMA_VERSION


def test_summary_entry_count() -> None:
    summary = scheduling_conflict_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_detected_count() -> None:
    summary = scheduling_conflict_summary(FIXTURE_PATH)
    assert summary["detected_count"] == 2


def test_summary_resolved_count() -> None:
    summary = scheduling_conflict_summary(FIXTURE_PATH)
    assert summary["resolved_count"] == 1


def test_summary_escalated_count() -> None:
    summary = scheduling_conflict_summary(FIXTURE_PATH)
    assert summary["escalated_count"] == 1


def test_summary_deferred_count() -> None:
    summary = scheduling_conflict_summary(FIXTURE_PATH)
    assert summary["deferred_count"] == 1


def test_summary_counts_by_kind() -> None:
    summary = scheduling_conflict_summary(FIXTURE_PATH)
    assert isinstance(summary["counts_by_kind"], dict)
    assert sum(summary["counts_by_kind"].values()) == 5


def test_summary_disclaimer() -> None:
    summary = scheduling_conflict_summary(FIXTURE_PATH)
    assert "does not authorize external submission" in summary["disclaimer"]
