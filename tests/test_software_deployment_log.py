"""Tests for software_deployment_log operational provenance records."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.software_deployment_log import (
    ALLOWED_DEPLOYMENT_KINDS,
    ALLOWED_DEPLOYMENT_STATUSES,
    SOFTWARE_DEPLOYMENT_LOG_SCHEMA_VERSION,
    SoftwareDeploymentEntry,
    load_software_deployment_entries,
    software_deployment_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "software_deployment_log.json"


def test_fixture_file_exists() -> None:
    assert FIXTURE_PATH.exists()


def test_fixture_loads_as_json() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    assert isinstance(obj, dict)
    assert "entries" in obj
    assert len(obj["entries"]) == 5


def test_fixture_top_level_schema_version() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    assert obj["schema_version"] == SOFTWARE_DEPLOYMENT_LOG_SCHEMA_VERSION


def test_fixture_deployment_kinds_valid() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    for row in obj["entries"]:
        assert row["deployment_kind"] in ALLOWED_DEPLOYMENT_KINDS


def test_fixture_statuses_valid() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    for row in obj["entries"]:
        assert row["status"] in ALLOWED_DEPLOYMENT_STATUSES


def test_load_entries_returns_list() -> None:
    entries = load_software_deployment_entries(FIXTURE_PATH)
    assert isinstance(entries, list)
    assert len(entries) == 5


def test_load_entries_are_dataclasses() -> None:
    entries = load_software_deployment_entries(FIXTURE_PATH)
    for entry in entries:
        assert isinstance(entry, SoftwareDeploymentEntry)


def test_entry_ids_unique() -> None:
    entries = load_software_deployment_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_completed_entries_present() -> None:
    entries = load_software_deployment_entries(FIXTURE_PATH)
    assert any(e.status == "completed" for e in entries)


def test_failed_entries_present() -> None:
    entries = load_software_deployment_entries(FIXTURE_PATH)
    assert any(e.status == "failed" for e in entries)


def test_in_progress_entries_present() -> None:
    entries = load_software_deployment_entries(FIXTURE_PATH)
    assert any(e.status == "in_progress" for e in entries)


def test_rolled_back_entries_present() -> None:
    entries = load_software_deployment_entries(FIXTURE_PATH)
    assert any(e.status == "rolled_back" for e in entries)


def test_summary_entry_count() -> None:
    summary = software_deployment_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_completed_count() -> None:
    summary = software_deployment_summary(FIXTURE_PATH)
    assert summary["completed_count"] >= 1


def test_summary_has_disclaimer() -> None:
    summary = software_deployment_summary(FIXTURE_PATH)
    assert "does not constitute a detection claim" in summary["disclaimer"]


def test_summary_by_kind_keys() -> None:
    summary = software_deployment_summary(FIXTURE_PATH)
    assert set(summary["by_kind"].keys()) == ALLOWED_DEPLOYMENT_KINDS


def test_summary_by_status_keys() -> None:
    summary = software_deployment_summary(FIXTURE_PATH)
    assert set(summary["by_status"].keys()) == ALLOWED_DEPLOYMENT_STATUSES


def test_summary_by_kind_total_matches_entry_count() -> None:
    summary = software_deployment_summary(FIXTURE_PATH)
    assert sum(summary["by_kind"].values()) == summary["entry_count"]


def test_summary_by_status_total_matches_entry_count() -> None:
    summary = software_deployment_summary(FIXTURE_PATH)
    assert sum(summary["by_status"].values()) == summary["entry_count"]


def test_invalid_deployment_kind_raises() -> None:
    with pytest.raises(ValueError, match="deployment_kind"):
        SoftwareDeploymentEntry(
            entry_id="x",
            deployment_kind="invalid_kind",
            status="completed",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes=None,
        )


def test_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="status"):
        SoftwareDeploymentEntry(
            entry_id="x",
            deployment_kind="patch",
            status="invalid_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes=None,
        )
