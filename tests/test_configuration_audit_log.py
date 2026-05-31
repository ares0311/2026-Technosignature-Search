"""Tests for configuration_audit_log operational provenance records."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.configuration_audit_log import (
    ALLOWED_AUDIT_KINDS,
    ALLOWED_AUDIT_STATUSES,
    CONFIGURATION_AUDIT_LOG_SCHEMA_VERSION,
    ConfigurationAuditEntry,
    configuration_audit_summary,
    load_configuration_audit_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "configuration_audit_log.json"


def test_fixture_file_exists() -> None:
    assert FIXTURE_PATH.exists()


def test_fixture_loads_as_json() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    assert isinstance(obj, dict)
    assert "entries" in obj
    assert len(obj["entries"]) == 5


def test_fixture_top_level_schema_version() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    assert obj["schema_version"] == CONFIGURATION_AUDIT_LOG_SCHEMA_VERSION


def test_fixture_audit_kinds_valid() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    for row in obj["entries"]:
        assert row["audit_kind"] in ALLOWED_AUDIT_KINDS


def test_fixture_statuses_valid() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    for row in obj["entries"]:
        assert row["status"] in ALLOWED_AUDIT_STATUSES


def test_load_entries_returns_list() -> None:
    entries = load_configuration_audit_entries(FIXTURE_PATH)
    assert isinstance(entries, list)
    assert len(entries) == 5


def test_load_entries_are_dataclasses() -> None:
    entries = load_configuration_audit_entries(FIXTURE_PATH)
    for entry in entries:
        assert isinstance(entry, ConfigurationAuditEntry)


def test_entry_ids_unique() -> None:
    entries = load_configuration_audit_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_compliant_entries_present() -> None:
    entries = load_configuration_audit_entries(FIXTURE_PATH)
    assert any(e.status == "compliant" for e in entries)


def test_drifted_entries_present() -> None:
    entries = load_configuration_audit_entries(FIXTURE_PATH)
    assert any(e.status == "drifted" for e in entries)


def test_failed_entries_present() -> None:
    entries = load_configuration_audit_entries(FIXTURE_PATH)
    assert any(e.status == "failed" for e in entries)


def test_inconclusive_entries_present() -> None:
    entries = load_configuration_audit_entries(FIXTURE_PATH)
    assert any(e.status == "inconclusive" for e in entries)


def test_summary_entry_count() -> None:
    summary = configuration_audit_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_compliant_count() -> None:
    summary = configuration_audit_summary(FIXTURE_PATH)
    assert summary["compliant_count"] >= 1


def test_summary_has_disclaimer() -> None:
    summary = configuration_audit_summary(FIXTURE_PATH)
    assert "does not constitute a detection claim" in summary["disclaimer"]


def test_summary_by_kind_keys() -> None:
    summary = configuration_audit_summary(FIXTURE_PATH)
    assert set(summary["by_kind"].keys()) == ALLOWED_AUDIT_KINDS


def test_summary_by_status_keys() -> None:
    summary = configuration_audit_summary(FIXTURE_PATH)
    assert set(summary["by_status"].keys()) == ALLOWED_AUDIT_STATUSES


def test_summary_by_kind_total_matches_entry_count() -> None:
    summary = configuration_audit_summary(FIXTURE_PATH)
    assert sum(summary["by_kind"].values()) == summary["entry_count"]


def test_summary_by_status_total_matches_entry_count() -> None:
    summary = configuration_audit_summary(FIXTURE_PATH)
    assert sum(summary["by_status"].values()) == summary["entry_count"]


def test_invalid_audit_kind_raises() -> None:
    with pytest.raises(ValueError, match="audit_kind"):
        ConfigurationAuditEntry(
            entry_id="x",
            audit_kind="invalid_kind",
            status="compliant",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes=None,
        )


def test_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="status"):
        ConfigurationAuditEntry(
            entry_id="x",
            audit_kind="scheduled_audit",
            status="invalid_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes=None,
        )
