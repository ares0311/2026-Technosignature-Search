"""Tests for system_health_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.system_health_log import (
    ALLOWED_HEALTH_KINDS,
    ALLOWED_HEALTH_STATUSES,
    SYSTEM_HEALTH_LOG_DISCLAIMER,
    SYSTEM_HEALTH_LOG_SCHEMA_VERSION,
    SystemHealthEntry,
    load_system_health_entries,
    system_health_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "system_health_log.json"


def test_schema_version() -> None:
    assert SYSTEM_HEALTH_LOG_SCHEMA_VERSION == "system_health_log_v1"


def test_disclaimer_present() -> None:
    assert "does not authorize external submission" in SYSTEM_HEALTH_LOG_DISCLAIMER
    assert "does not constitute a detection claim" in SYSTEM_HEALTH_LOG_DISCLAIMER


def test_allowed_health_kinds_complete() -> None:
    assert "cpu_usage" in ALLOWED_HEALTH_KINDS
    assert "memory_usage" in ALLOWED_HEALTH_KINDS
    assert "disk_space" in ALLOWED_HEALTH_KINDS
    assert "network_latency" in ALLOWED_HEALTH_KINDS
    assert "process_uptime" in ALLOWED_HEALTH_KINDS


def test_allowed_statuses_complete() -> None:
    assert "healthy" in ALLOWED_HEALTH_STATUSES
    assert "warning" in ALLOWED_HEALTH_STATUSES
    assert "critical" in ALLOWED_HEALTH_STATUSES
    assert "unknown" in ALLOWED_HEALTH_STATUSES


def test_load_entries_count() -> None:
    entries = load_system_health_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_load_entries_types() -> None:
    entries = load_system_health_entries(FIXTURE_PATH)
    for e in entries:
        assert isinstance(e, SystemHealthEntry)


def test_entry_ids_unique() -> None:
    entries = load_system_health_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_health_kinds_valid() -> None:
    entries = load_system_health_entries(FIXTURE_PATH)
    for e in entries:
        assert e.health_kind in ALLOWED_HEALTH_KINDS


def test_statuses_valid() -> None:
    entries = load_system_health_entries(FIXTURE_PATH)
    for e in entries:
        assert e.status in ALLOWED_HEALTH_STATUSES


def test_healthy_count() -> None:
    entries = load_system_health_entries(FIXTURE_PATH)
    healthy = [e for e in entries if e.status == "healthy"]
    assert len(healthy) == 2


def test_warning_count() -> None:
    entries = load_system_health_entries(FIXTURE_PATH)
    warning = [e for e in entries if e.status == "warning"]
    assert len(warning) == 1


def test_critical_count() -> None:
    entries = load_system_health_entries(FIXTURE_PATH)
    critical = [e for e in entries if e.status == "critical"]
    assert len(critical) == 1


def test_unknown_count() -> None:
    entries = load_system_health_entries(FIXTURE_PATH)
    unknown = [e for e in entries if e.status == "unknown"]
    assert len(unknown) == 1


def test_entry_as_dict() -> None:
    entries = load_system_health_entries(FIXTURE_PATH)
    d = entries[0].as_dict()
    assert "entry_id" in d
    assert "health_kind" in d
    assert "status" in d


def test_summary_schema_version() -> None:
    summary = system_health_summary(FIXTURE_PATH)
    assert summary["schema_version"] == SYSTEM_HEALTH_LOG_SCHEMA_VERSION


def test_summary_entry_count() -> None:
    summary = system_health_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_healthy_count() -> None:
    summary = system_health_summary(FIXTURE_PATH)
    assert summary["healthy_count"] == 2


def test_summary_warning_count() -> None:
    summary = system_health_summary(FIXTURE_PATH)
    assert summary["warning_count"] == 1


def test_summary_critical_count() -> None:
    summary = system_health_summary(FIXTURE_PATH)
    assert summary["critical_count"] == 1


def test_summary_unknown_count() -> None:
    summary = system_health_summary(FIXTURE_PATH)
    assert summary["unknown_count"] == 1


def test_summary_counts_by_kind() -> None:
    summary = system_health_summary(FIXTURE_PATH)
    assert isinstance(summary["counts_by_kind"], dict)
    assert sum(summary["counts_by_kind"].values()) == 5


def test_summary_disclaimer() -> None:
    summary = system_health_summary(FIXTURE_PATH)
    assert "does not authorize external submission" in summary["disclaimer"]
