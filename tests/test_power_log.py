"""Tests for power_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.power_log import (
    ALLOWED_POWER_KINDS,
    ALLOWED_POWER_STATUSES,
    POWER_LOG_DISCLAIMER,
    POWER_LOG_SCHEMA_VERSION,
    PowerEntry,
    load_power_entries,
    power_log_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "power_log.json"


def test_schema_version() -> None:
    assert POWER_LOG_SCHEMA_VERSION == "power_log_v1"


def test_disclaimer_present() -> None:
    assert "does not authorize external submission" in POWER_LOG_DISCLAIMER
    assert "does not constitute a detection claim" in POWER_LOG_DISCLAIMER


def test_allowed_power_kinds_complete() -> None:
    assert "ups_event" in ALLOWED_POWER_KINDS
    assert "mains_failure" in ALLOWED_POWER_KINDS
    assert "generator_start" in ALLOWED_POWER_KINDS
    assert "load_shed" in ALLOWED_POWER_KINDS
    assert "power_restoration" in ALLOWED_POWER_KINDS


def test_allowed_statuses_complete() -> None:
    assert "normal" in ALLOWED_POWER_STATUSES
    assert "degraded" in ALLOWED_POWER_STATUSES
    assert "critical" in ALLOWED_POWER_STATUSES
    assert "restored" in ALLOWED_POWER_STATUSES


def test_load_entries_count() -> None:
    entries = load_power_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_load_entries_types() -> None:
    entries = load_power_entries(FIXTURE_PATH)
    for e in entries:
        assert isinstance(e, PowerEntry)


def test_entry_ids_unique() -> None:
    entries = load_power_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_power_kinds_valid() -> None:
    entries = load_power_entries(FIXTURE_PATH)
    for e in entries:
        assert e.power_kind in ALLOWED_POWER_KINDS


def test_statuses_valid() -> None:
    entries = load_power_entries(FIXTURE_PATH)
    for e in entries:
        assert e.status in ALLOWED_POWER_STATUSES


def test_normal_count() -> None:
    entries = load_power_entries(FIXTURE_PATH)
    normal = [e for e in entries if e.status == "normal"]
    assert len(normal) == 2


def test_degraded_count() -> None:
    entries = load_power_entries(FIXTURE_PATH)
    degraded = [e for e in entries if e.status == "degraded"]
    assert len(degraded) == 1


def test_critical_count() -> None:
    entries = load_power_entries(FIXTURE_PATH)
    critical = [e for e in entries if e.status == "critical"]
    assert len(critical) == 1


def test_restored_count() -> None:
    entries = load_power_entries(FIXTURE_PATH)
    restored = [e for e in entries if e.status == "restored"]
    assert len(restored) == 1


def test_entry_as_dict() -> None:
    entries = load_power_entries(FIXTURE_PATH)
    d = entries[0].as_dict()
    assert "entry_id" in d
    assert "power_kind" in d
    assert "status" in d


def test_summary_schema_version() -> None:
    summary = power_log_summary(FIXTURE_PATH)
    assert summary["schema_version"] == POWER_LOG_SCHEMA_VERSION


def test_summary_entry_count() -> None:
    summary = power_log_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_normal_count() -> None:
    summary = power_log_summary(FIXTURE_PATH)
    assert summary["normal_count"] == 2


def test_summary_degraded_count() -> None:
    summary = power_log_summary(FIXTURE_PATH)
    assert summary["degraded_count"] == 1


def test_summary_critical_count() -> None:
    summary = power_log_summary(FIXTURE_PATH)
    assert summary["critical_count"] == 1


def test_summary_restored_count() -> None:
    summary = power_log_summary(FIXTURE_PATH)
    assert summary["restored_count"] == 1


def test_summary_counts_by_kind() -> None:
    summary = power_log_summary(FIXTURE_PATH)
    assert isinstance(summary["counts_by_kind"], dict)
    assert sum(summary["counts_by_kind"].values()) == 5
