"""Tests for change_management_log operational provenance records."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.change_management_log import (
    ALLOWED_CHANGE_KINDS,
    ALLOWED_CHANGE_STATUSES,
    CHANGE_MANAGEMENT_LOG_SCHEMA_VERSION,
    ChangeManagementEntry,
    change_management_summary,
    load_change_management_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "change_management_log.json"


def test_fixture_file_exists() -> None:
    assert FIXTURE_PATH.exists()


def test_fixture_loads_as_json() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    assert isinstance(obj, dict)
    assert "entries" in obj
    assert len(obj["entries"]) == 5


def test_fixture_top_level_schema_version() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    assert obj["schema_version"] == CHANGE_MANAGEMENT_LOG_SCHEMA_VERSION


def test_fixture_change_kinds_valid() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    for row in obj["entries"]:
        assert row["change_kind"] in ALLOWED_CHANGE_KINDS


def test_fixture_statuses_valid() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    for row in obj["entries"]:
        assert row["status"] in ALLOWED_CHANGE_STATUSES


def test_load_entries_returns_list() -> None:
    entries = load_change_management_entries(FIXTURE_PATH)
    assert isinstance(entries, list)
    assert len(entries) == 5


def test_load_entries_are_dataclasses() -> None:
    entries = load_change_management_entries(FIXTURE_PATH)
    for entry in entries:
        assert isinstance(entry, ChangeManagementEntry)


def test_entry_ids_unique() -> None:
    entries = load_change_management_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_requested_entries_present() -> None:
    entries = load_change_management_entries(FIXTURE_PATH)
    assert any(e.status == "requested" for e in entries)


def test_approved_entries_present() -> None:
    entries = load_change_management_entries(FIXTURE_PATH)
    assert any(e.status == "approved" for e in entries)


def test_implemented_entries_present() -> None:
    entries = load_change_management_entries(FIXTURE_PATH)
    assert any(e.status == "implemented" for e in entries)


def test_rolled_back_entries_present() -> None:
    entries = load_change_management_entries(FIXTURE_PATH)
    assert any(e.status == "rolled_back" for e in entries)


def test_summary_entry_count() -> None:
    summary = change_management_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_implemented_count() -> None:
    summary = change_management_summary(FIXTURE_PATH)
    assert summary["implemented_count"] >= 1


def test_summary_has_disclaimer() -> None:
    summary = change_management_summary(FIXTURE_PATH)
    assert "does not constitute a detection claim" in summary["disclaimer"]


def test_summary_by_kind_keys() -> None:
    summary = change_management_summary(FIXTURE_PATH)
    assert set(summary["by_kind"].keys()) == ALLOWED_CHANGE_KINDS


def test_summary_by_status_keys() -> None:
    summary = change_management_summary(FIXTURE_PATH)
    assert set(summary["by_status"].keys()) == ALLOWED_CHANGE_STATUSES


def test_summary_by_kind_total_matches_entry_count() -> None:
    summary = change_management_summary(FIXTURE_PATH)
    assert sum(summary["by_kind"].values()) == summary["entry_count"]


def test_summary_by_status_total_matches_entry_count() -> None:
    summary = change_management_summary(FIXTURE_PATH)
    assert sum(summary["by_status"].values()) == summary["entry_count"]


def test_invalid_change_kind_raises() -> None:
    with pytest.raises(ValueError, match="change_kind"):
        ChangeManagementEntry(
            entry_id="x",
            change_kind="invalid_kind",
            status="requested",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes=None,
        )


def test_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="status"):
        ChangeManagementEntry(
            entry_id="x",
            change_kind="planned_change",
            status="invalid_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes=None,
        )
