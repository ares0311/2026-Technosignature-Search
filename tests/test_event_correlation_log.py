"""Tests for event_correlation_log operational provenance records."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.event_correlation_log import (
    ALLOWED_CORRELATION_KINDS,
    ALLOWED_CORRELATION_STATUSES,
    EVENT_CORRELATION_LOG_SCHEMA_VERSION,
    EventCorrelationEntry,
    event_correlation_summary,
    load_event_correlation_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "event_correlation_log.json"


def test_fixture_file_exists() -> None:
    assert FIXTURE_PATH.exists()


def test_fixture_loads_as_json() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    assert isinstance(obj, dict)
    assert "entries" in obj
    assert len(obj["entries"]) == 5


def test_fixture_top_level_schema_version() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    assert obj["schema_version"] == EVENT_CORRELATION_LOG_SCHEMA_VERSION


def test_fixture_correlation_kinds_valid() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    for row in obj["entries"]:
        assert row["correlation_kind"] in ALLOWED_CORRELATION_KINDS


def test_fixture_statuses_valid() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    for row in obj["entries"]:
        assert row["status"] in ALLOWED_CORRELATION_STATUSES


def test_load_entries_returns_list() -> None:
    entries = load_event_correlation_entries(FIXTURE_PATH)
    assert isinstance(entries, list)
    assert len(entries) == 5


def test_load_entries_are_dataclasses() -> None:
    entries = load_event_correlation_entries(FIXTURE_PATH)
    for entry in entries:
        assert isinstance(entry, EventCorrelationEntry)


def test_entry_ids_unique() -> None:
    entries = load_event_correlation_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_correlated_entries_present() -> None:
    entries = load_event_correlation_entries(FIXTURE_PATH)
    assert any(e.status == "correlated" for e in entries)


def test_inconclusive_entries_present() -> None:
    entries = load_event_correlation_entries(FIXTURE_PATH)
    assert any(e.status == "inconclusive" for e in entries)


def test_no_match_entries_present() -> None:
    entries = load_event_correlation_entries(FIXTURE_PATH)
    assert any(e.status == "no_match" for e in entries)


def test_pending_entries_present() -> None:
    entries = load_event_correlation_entries(FIXTURE_PATH)
    assert any(e.status == "pending" for e in entries)


def test_summary_entry_count() -> None:
    summary = event_correlation_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_correlated_count() -> None:
    summary = event_correlation_summary(FIXTURE_PATH)
    assert summary["correlated_count"] >= 1


def test_summary_has_disclaimer() -> None:
    summary = event_correlation_summary(FIXTURE_PATH)
    assert "does not constitute a detection claim" in summary["disclaimer"]


def test_summary_by_kind_keys() -> None:
    summary = event_correlation_summary(FIXTURE_PATH)
    assert set(summary["by_kind"].keys()) == ALLOWED_CORRELATION_KINDS


def test_summary_by_status_keys() -> None:
    summary = event_correlation_summary(FIXTURE_PATH)
    assert set(summary["by_status"].keys()) == ALLOWED_CORRELATION_STATUSES


def test_summary_by_kind_total_matches_entry_count() -> None:
    summary = event_correlation_summary(FIXTURE_PATH)
    assert sum(summary["by_kind"].values()) == summary["entry_count"]


def test_summary_by_status_total_matches_entry_count() -> None:
    summary = event_correlation_summary(FIXTURE_PATH)
    assert sum(summary["by_status"].values()) == summary["entry_count"]


def test_invalid_correlation_kind_raises() -> None:
    with pytest.raises(ValueError, match="correlation_kind"):
        EventCorrelationEntry(
            entry_id="x",
            correlation_kind="invalid_kind",
            status="correlated",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes=None,
        )


def test_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="status"):
        EventCorrelationEntry(
            entry_id="x",
            correlation_kind="alert_cluster",
            status="invalid_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes=None,
        )
