"""Tests for firmware_update_log operational provenance records."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.firmware_update_log import (
    ALLOWED_FIRMWARE_KINDS,
    ALLOWED_FIRMWARE_STATUSES,
    FIRMWARE_UPDATE_LOG_SCHEMA_VERSION,
    FirmwareUpdateEntry,
    firmware_update_summary,
    load_firmware_update_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "firmware_update_log.json"


def test_fixture_file_exists() -> None:
    assert FIXTURE_PATH.exists()


def test_fixture_loads_as_json() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    assert isinstance(obj, dict)
    assert "entries" in obj
    assert len(obj["entries"]) == 5


def test_fixture_top_level_schema_version() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    assert obj["schema_version"] == FIRMWARE_UPDATE_LOG_SCHEMA_VERSION


def test_fixture_firmware_kinds_valid() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    for row in obj["entries"]:
        assert row["firmware_kind"] in ALLOWED_FIRMWARE_KINDS


def test_fixture_statuses_valid() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    for row in obj["entries"]:
        assert row["status"] in ALLOWED_FIRMWARE_STATUSES


def test_load_entries_returns_list() -> None:
    entries = load_firmware_update_entries(FIXTURE_PATH)
    assert isinstance(entries, list)
    assert len(entries) == 5


def test_load_entries_are_dataclasses() -> None:
    entries = load_firmware_update_entries(FIXTURE_PATH)
    for entry in entries:
        assert isinstance(entry, FirmwareUpdateEntry)


def test_entry_ids_unique() -> None:
    entries = load_firmware_update_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_applied_entries_present() -> None:
    entries = load_firmware_update_entries(FIXTURE_PATH)
    assert any(e.status == "applied" for e in entries)


def test_pending_entries_present() -> None:
    entries = load_firmware_update_entries(FIXTURE_PATH)
    assert any(e.status == "pending" for e in entries)


def test_failed_entries_present() -> None:
    entries = load_firmware_update_entries(FIXTURE_PATH)
    assert any(e.status == "failed" for e in entries)


def test_rolled_back_entries_present() -> None:
    entries = load_firmware_update_entries(FIXTURE_PATH)
    assert any(e.status == "rolled_back" for e in entries)


def test_summary_entry_count() -> None:
    summary = firmware_update_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_applied_count() -> None:
    summary = firmware_update_summary(FIXTURE_PATH)
    assert summary["applied_count"] >= 1


def test_summary_has_disclaimer() -> None:
    summary = firmware_update_summary(FIXTURE_PATH)
    assert "does not constitute a detection claim" in summary["disclaimer"]


def test_summary_by_kind_keys() -> None:
    summary = firmware_update_summary(FIXTURE_PATH)
    assert set(summary["by_kind"].keys()) == ALLOWED_FIRMWARE_KINDS


def test_summary_by_status_keys() -> None:
    summary = firmware_update_summary(FIXTURE_PATH)
    assert set(summary["by_status"].keys()) == ALLOWED_FIRMWARE_STATUSES


def test_summary_by_kind_total_matches_entry_count() -> None:
    summary = firmware_update_summary(FIXTURE_PATH)
    assert sum(summary["by_kind"].values()) == summary["entry_count"]


def test_summary_by_status_total_matches_entry_count() -> None:
    summary = firmware_update_summary(FIXTURE_PATH)
    assert sum(summary["by_status"].values()) == summary["entry_count"]


def test_invalid_firmware_kind_raises() -> None:
    with pytest.raises(ValueError, match="firmware_kind"):
        FirmwareUpdateEntry(
            entry_id="x",
            firmware_kind="invalid_kind",
            status="applied",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes=None,
        )


def test_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="status"):
        FirmwareUpdateEntry(
            entry_id="x",
            firmware_kind="scheduled_update",
            status="invalid_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes=None,
        )
