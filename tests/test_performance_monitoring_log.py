"""Tests for performance_monitoring_log operational provenance records."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.performance_monitoring_log import (
    ALLOWED_PERFORMANCE_KINDS,
    ALLOWED_PERFORMANCE_STATUSES,
    PERFORMANCE_MONITORING_LOG_SCHEMA_VERSION,
    PerformanceMonitoringEntry,
    load_performance_monitoring_entries,
    performance_monitoring_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "performance_monitoring_log.json"


def test_fixture_file_exists() -> None:
    assert FIXTURE_PATH.exists()


def test_fixture_loads_as_json() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    assert isinstance(obj, dict)
    assert "entries" in obj
    assert len(obj["entries"]) == 5


def test_fixture_top_level_schema_version() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    assert obj["schema_version"] == PERFORMANCE_MONITORING_LOG_SCHEMA_VERSION


def test_fixture_performance_kinds_valid() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    for row in obj["entries"]:
        assert row["performance_kind"] in ALLOWED_PERFORMANCE_KINDS


def test_fixture_statuses_valid() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    for row in obj["entries"]:
        assert row["status"] in ALLOWED_PERFORMANCE_STATUSES


def test_load_entries_returns_list() -> None:
    entries = load_performance_monitoring_entries(FIXTURE_PATH)
    assert isinstance(entries, list)
    assert len(entries) == 5


def test_load_entries_are_dataclasses() -> None:
    entries = load_performance_monitoring_entries(FIXTURE_PATH)
    for entry in entries:
        assert isinstance(entry, PerformanceMonitoringEntry)


def test_entry_ids_unique() -> None:
    entries = load_performance_monitoring_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_normal_entries_present() -> None:
    entries = load_performance_monitoring_entries(FIXTURE_PATH)
    assert any(e.status == "normal" for e in entries)


def test_alert_entries_present() -> None:
    entries = load_performance_monitoring_entries(FIXTURE_PATH)
    assert any(e.status == "alert" for e in entries)


def test_degraded_entries_present() -> None:
    entries = load_performance_monitoring_entries(FIXTURE_PATH)
    assert any(e.status == "degraded" for e in entries)


def test_critical_entries_present() -> None:
    entries = load_performance_monitoring_entries(FIXTURE_PATH)
    assert any(e.status == "critical" for e in entries)


def test_summary_entry_count() -> None:
    summary = performance_monitoring_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_normal_count() -> None:
    summary = performance_monitoring_summary(FIXTURE_PATH)
    assert summary["normal_count"] >= 1


def test_summary_has_disclaimer() -> None:
    summary = performance_monitoring_summary(FIXTURE_PATH)
    assert "does not constitute a detection claim" in summary["disclaimer"]


def test_summary_by_kind_keys() -> None:
    summary = performance_monitoring_summary(FIXTURE_PATH)
    assert set(summary["by_kind"].keys()) == ALLOWED_PERFORMANCE_KINDS


def test_summary_by_status_keys() -> None:
    summary = performance_monitoring_summary(FIXTURE_PATH)
    assert set(summary["by_status"].keys()) == ALLOWED_PERFORMANCE_STATUSES


def test_summary_by_kind_total_matches_entry_count() -> None:
    summary = performance_monitoring_summary(FIXTURE_PATH)
    assert sum(summary["by_kind"].values()) == summary["entry_count"]


def test_summary_by_status_total_matches_entry_count() -> None:
    summary = performance_monitoring_summary(FIXTURE_PATH)
    assert sum(summary["by_status"].values()) == summary["entry_count"]


def test_invalid_performance_kind_raises() -> None:
    with pytest.raises(ValueError, match="performance_kind"):
        PerformanceMonitoringEntry(
            entry_id="x",
            performance_kind="invalid_kind",
            status="normal",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes=None,
        )


def test_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="status"):
        PerformanceMonitoringEntry(
            entry_id="x",
            performance_kind="cpu_utilization",
            status="invalid_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes=None,
        )
