"""Tests for capacity_planning_log operational provenance records."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.capacity_planning_log import (
    ALLOWED_CAPACITY_KINDS,
    ALLOWED_CAPACITY_STATUSES,
    CAPACITY_PLANNING_LOG_SCHEMA_VERSION,
    CapacityPlanningEntry,
    capacity_planning_summary,
    load_capacity_planning_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "capacity_planning_log.json"


def test_fixture_file_exists() -> None:
    assert FIXTURE_PATH.exists()


def test_fixture_loads_as_json() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    assert isinstance(obj, dict)
    assert "entries" in obj
    assert len(obj["entries"]) == 5


def test_fixture_top_level_schema_version() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    assert obj["schema_version"] == CAPACITY_PLANNING_LOG_SCHEMA_VERSION


def test_fixture_capacity_kinds_valid() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    for row in obj["entries"]:
        assert row["capacity_kind"] in ALLOWED_CAPACITY_KINDS


def test_fixture_statuses_valid() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    for row in obj["entries"]:
        assert row["status"] in ALLOWED_CAPACITY_STATUSES


def test_load_entries_returns_list() -> None:
    entries = load_capacity_planning_entries(FIXTURE_PATH)
    assert isinstance(entries, list)
    assert len(entries) == 5


def test_load_entries_are_dataclasses() -> None:
    entries = load_capacity_planning_entries(FIXTURE_PATH)
    for entry in entries:
        assert isinstance(entry, CapacityPlanningEntry)


def test_entry_ids_unique() -> None:
    entries = load_capacity_planning_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_adequate_entries_present() -> None:
    entries = load_capacity_planning_entries(FIXTURE_PATH)
    assert any(e.status == "adequate" for e in entries)


def test_warning_entries_present() -> None:
    entries = load_capacity_planning_entries(FIXTURE_PATH)
    assert any(e.status == "warning" for e in entries)


def test_critical_entries_present() -> None:
    entries = load_capacity_planning_entries(FIXTURE_PATH)
    assert any(e.status == "critical" for e in entries)


def test_planned_expansion_entries_present() -> None:
    entries = load_capacity_planning_entries(FIXTURE_PATH)
    assert any(e.status == "planned_expansion" for e in entries)


def test_summary_entry_count() -> None:
    summary = capacity_planning_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_adequate_count() -> None:
    summary = capacity_planning_summary(FIXTURE_PATH)
    assert summary["adequate_count"] >= 1


def test_summary_has_disclaimer() -> None:
    summary = capacity_planning_summary(FIXTURE_PATH)
    assert "does not constitute a detection claim" in summary["disclaimer"]


def test_summary_by_kind_keys() -> None:
    summary = capacity_planning_summary(FIXTURE_PATH)
    assert set(summary["by_kind"].keys()) == ALLOWED_CAPACITY_KINDS


def test_summary_by_status_keys() -> None:
    summary = capacity_planning_summary(FIXTURE_PATH)
    assert set(summary["by_status"].keys()) == ALLOWED_CAPACITY_STATUSES


def test_summary_by_kind_total_matches_entry_count() -> None:
    summary = capacity_planning_summary(FIXTURE_PATH)
    assert sum(summary["by_kind"].values()) == summary["entry_count"]


def test_summary_by_status_total_matches_entry_count() -> None:
    summary = capacity_planning_summary(FIXTURE_PATH)
    assert sum(summary["by_status"].values()) == summary["entry_count"]


def test_invalid_capacity_kind_raises() -> None:
    with pytest.raises(ValueError, match="capacity_kind"):
        CapacityPlanningEntry(
            entry_id="x",
            capacity_kind="invalid_kind",
            status="adequate",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes=None,
        )


def test_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="status"):
        CapacityPlanningEntry(
            entry_id="x",
            capacity_kind="storage_capacity",
            status="invalid_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes=None,
        )
