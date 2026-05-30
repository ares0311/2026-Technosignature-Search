"""Tests for security_event_log operational provenance records."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.security_event_log import (
    ALLOWED_SECURITY_EVENT_KINDS,
    ALLOWED_SECURITY_EVENT_STATUSES,
    SECURITY_EVENT_LOG_SCHEMA_VERSION,
    SecurityEventEntry,
    load_security_event_entries,
    security_event_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "security_event_log.json"


def test_fixture_file_exists() -> None:
    assert FIXTURE_PATH.exists()


def test_fixture_loads_as_json() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    assert isinstance(obj, dict)
    assert "entries" in obj
    assert len(obj["entries"]) == 5


def test_fixture_top_level_schema_version() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    assert obj["schema_version"] == SECURITY_EVENT_LOG_SCHEMA_VERSION


def test_fixture_event_kinds_valid() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    for row in obj["entries"]:
        assert row["event_kind"] in ALLOWED_SECURITY_EVENT_KINDS


def test_fixture_statuses_valid() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    for row in obj["entries"]:
        assert row["status"] in ALLOWED_SECURITY_EVENT_STATUSES


def test_load_entries_returns_list() -> None:
    entries = load_security_event_entries(FIXTURE_PATH)
    assert isinstance(entries, list)
    assert len(entries) == 5


def test_load_entries_are_dataclasses() -> None:
    entries = load_security_event_entries(FIXTURE_PATH)
    for entry in entries:
        assert isinstance(entry, SecurityEventEntry)


def test_entry_ids_unique() -> None:
    entries = load_security_event_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_detected_entries_present() -> None:
    entries = load_security_event_entries(FIXTURE_PATH)
    assert any(e.status == "detected" for e in entries)


def test_investigated_entries_present() -> None:
    entries = load_security_event_entries(FIXTURE_PATH)
    assert any(e.status == "investigated" for e in entries)


def test_resolved_entries_present() -> None:
    entries = load_security_event_entries(FIXTURE_PATH)
    assert any(e.status == "resolved" for e in entries)


def test_escalated_entries_present() -> None:
    entries = load_security_event_entries(FIXTURE_PATH)
    assert any(e.status == "escalated" for e in entries)


def test_summary_entry_count() -> None:
    summary = security_event_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_detected_count() -> None:
    summary = security_event_summary(FIXTURE_PATH)
    assert summary["detected_count"] >= 1


def test_summary_has_disclaimer() -> None:
    summary = security_event_summary(FIXTURE_PATH)
    assert "does not constitute a detection claim" in summary["disclaimer"]


def test_summary_by_kind_keys() -> None:
    summary = security_event_summary(FIXTURE_PATH)
    assert set(summary["by_kind"].keys()) == ALLOWED_SECURITY_EVENT_KINDS


def test_summary_by_status_keys() -> None:
    summary = security_event_summary(FIXTURE_PATH)
    assert set(summary["by_status"].keys()) == ALLOWED_SECURITY_EVENT_STATUSES


def test_summary_by_kind_total_matches_entry_count() -> None:
    summary = security_event_summary(FIXTURE_PATH)
    assert sum(summary["by_kind"].values()) == summary["entry_count"]


def test_summary_by_status_total_matches_entry_count() -> None:
    summary = security_event_summary(FIXTURE_PATH)
    assert sum(summary["by_status"].values()) == summary["entry_count"]


def test_invalid_event_kind_raises() -> None:
    with pytest.raises(ValueError, match="event_kind"):
        SecurityEventEntry(
            entry_id="x",
            event_kind="invalid_kind",
            status="detected",
            severity="low",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes=None,
        )


def test_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="status"):
        SecurityEventEntry(
            entry_id="x",
            event_kind="intrusion_attempt",
            status="invalid_status",
            severity="low",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes=None,
        )
