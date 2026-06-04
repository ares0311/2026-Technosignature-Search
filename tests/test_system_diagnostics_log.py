"""Tests for system_diagnostics_log operational provenance records."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.system_diagnostics_log import (
    ALLOWED_SYSTEM_DIAGNOSTICS_KINDS,
    ALLOWED_SYSTEM_DIAGNOSTICS_STATUSES,
    SYSTEM_DIAGNOSTICS_LOG_SCHEMA_VERSION,
    SystemDiagnosticsEntry,
    load_system_diagnostics_entries,
    system_diagnostics_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "system_diagnostics_log.json"


def test_fixture_file_exists() -> None:
    assert FIXTURE_PATH.exists()


def test_fixture_loads_as_json() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    assert isinstance(obj, dict)
    assert "entries" in obj
    assert len(obj["entries"]) == 5


def test_fixture_top_level_schema_version() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    assert obj["schema_version"] == SYSTEM_DIAGNOSTICS_LOG_SCHEMA_VERSION


def test_fixture_diagnostics_kinds_valid() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    for row in obj["entries"]:
        assert row["diagnostics_kind"] in ALLOWED_SYSTEM_DIAGNOSTICS_KINDS


def test_fixture_statuses_valid() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    for row in obj["entries"]:
        assert row["status"] in ALLOWED_SYSTEM_DIAGNOSTICS_STATUSES


def test_load_entries_returns_list() -> None:
    entries = load_system_diagnostics_entries(FIXTURE_PATH)
    assert isinstance(entries, list)
    assert len(entries) == 5


def test_load_entries_are_dataclasses() -> None:
    entries = load_system_diagnostics_entries(FIXTURE_PATH)
    for entry in entries:
        assert isinstance(entry, SystemDiagnosticsEntry)


def test_entry_ids_unique() -> None:
    entries = load_system_diagnostics_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_passed_entries_present() -> None:
    entries = load_system_diagnostics_entries(FIXTURE_PATH)
    assert any(e.status == "passed" for e in entries)


def test_warning_entries_present() -> None:
    entries = load_system_diagnostics_entries(FIXTURE_PATH)
    assert any(e.status == "warning" for e in entries)


def test_failed_entries_present() -> None:
    entries = load_system_diagnostics_entries(FIXTURE_PATH)
    assert any(e.status == "failed" for e in entries)


def test_not_run_entries_present() -> None:
    entries = load_system_diagnostics_entries(FIXTURE_PATH)
    assert any(e.status == "not_run" for e in entries)


def test_summary_entry_count() -> None:
    summary = system_diagnostics_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_passed_count() -> None:
    summary = system_diagnostics_summary(FIXTURE_PATH)
    assert summary["passed_count"] >= 1


def test_summary_has_disclaimer() -> None:
    summary = system_diagnostics_summary(FIXTURE_PATH)
    assert "does not constitute a detection claim" in summary["disclaimer"]


def test_summary_by_kind_keys() -> None:
    summary = system_diagnostics_summary(FIXTURE_PATH)
    assert set(summary["by_kind"].keys()) == ALLOWED_SYSTEM_DIAGNOSTICS_KINDS


def test_summary_by_status_keys() -> None:
    summary = system_diagnostics_summary(FIXTURE_PATH)
    assert set(summary["by_status"].keys()) == ALLOWED_SYSTEM_DIAGNOSTICS_STATUSES


def test_summary_by_kind_total_matches_entry_count() -> None:
    summary = system_diagnostics_summary(FIXTURE_PATH)
    assert sum(summary["by_kind"].values()) == summary["entry_count"]


def test_summary_by_status_total_matches_entry_count() -> None:
    summary = system_diagnostics_summary(FIXTURE_PATH)
    assert sum(summary["by_status"].values()) == summary["entry_count"]


def test_invalid_diagnostics_kind_raises() -> None:
    with pytest.raises(ValueError, match="diagnostics_kind"):
        SystemDiagnosticsEntry(
            entry_id="x",
            diagnostics_kind="invalid_kind",
            status="passed",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes=None,
        )


def test_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="status"):
        SystemDiagnosticsEntry(
            entry_id="x",
            diagnostics_kind="hardware_check",
            status="invalid_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes=None,
        )
