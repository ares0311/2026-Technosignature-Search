"""Tests for user_activity_log operational provenance records."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.user_activity_log import (
    ALLOWED_ACTIVITY_KINDS,
    ALLOWED_ACTIVITY_STATUSES,
    USER_ACTIVITY_LOG_SCHEMA_VERSION,
    UserActivityEntry,
    load_user_activity_entries,
    user_activity_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "user_activity_log.json"


def test_fixture_file_exists() -> None:
    assert FIXTURE_PATH.exists()


def test_fixture_loads_as_json() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    assert isinstance(obj, dict)
    assert "entries" in obj
    assert len(obj["entries"]) == 5


def test_fixture_top_level_schema_version() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    assert obj["schema_version"] == USER_ACTIVITY_LOG_SCHEMA_VERSION


def test_fixture_activity_kinds_valid() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    for row in obj["entries"]:
        assert row["activity_kind"] in ALLOWED_ACTIVITY_KINDS


def test_fixture_statuses_valid() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    for row in obj["entries"]:
        assert row["status"] in ALLOWED_ACTIVITY_STATUSES


def test_load_entries_returns_list() -> None:
    entries = load_user_activity_entries(FIXTURE_PATH)
    assert isinstance(entries, list)
    assert len(entries) == 5


def test_load_entries_are_dataclasses() -> None:
    entries = load_user_activity_entries(FIXTURE_PATH)
    for entry in entries:
        assert isinstance(entry, UserActivityEntry)


def test_entry_ids_unique() -> None:
    entries = load_user_activity_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_succeeded_entries_present() -> None:
    entries = load_user_activity_entries(FIXTURE_PATH)
    assert any(e.status == "succeeded" for e in entries)


def test_failed_entries_present() -> None:
    entries = load_user_activity_entries(FIXTURE_PATH)
    assert any(e.status == "failed" for e in entries)


def test_warning_entries_present() -> None:
    entries = load_user_activity_entries(FIXTURE_PATH)
    assert any(e.status == "warning" for e in entries)


def test_blocked_entries_present() -> None:
    entries = load_user_activity_entries(FIXTURE_PATH)
    assert any(e.status == "blocked" for e in entries)


def test_summary_entry_count() -> None:
    summary = user_activity_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_succeeded_count() -> None:
    summary = user_activity_summary(FIXTURE_PATH)
    assert summary["succeeded_count"] >= 1


def test_summary_has_disclaimer() -> None:
    summary = user_activity_summary(FIXTURE_PATH)
    assert "does not constitute a detection claim" in summary["disclaimer"]


def test_summary_by_kind_keys() -> None:
    summary = user_activity_summary(FIXTURE_PATH)
    assert set(summary["by_kind"].keys()) == ALLOWED_ACTIVITY_KINDS


def test_summary_by_status_keys() -> None:
    summary = user_activity_summary(FIXTURE_PATH)
    assert set(summary["by_status"].keys()) == ALLOWED_ACTIVITY_STATUSES


def test_summary_by_kind_total_matches_entry_count() -> None:
    summary = user_activity_summary(FIXTURE_PATH)
    assert sum(summary["by_kind"].values()) == summary["entry_count"]


def test_summary_by_status_total_matches_entry_count() -> None:
    summary = user_activity_summary(FIXTURE_PATH)
    assert sum(summary["by_status"].values()) == summary["entry_count"]


def test_invalid_activity_kind_raises() -> None:
    with pytest.raises(ValueError, match="activity_kind"):
        UserActivityEntry(
            entry_id="x",
            activity_kind="invalid_kind",
            status="succeeded",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes=None,
        )


def test_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="status"):
        UserActivityEntry(
            entry_id="x",
            activity_kind="login",
            status="invalid_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes=None,
        )
