"""Tests for software_update_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.software_update_log import (
    ALLOWED_UPDATE_KINDS,
    ALLOWED_UPDATE_STATUSES,
    SOFTWARE_UPDATE_LOG_DISCLAIMER,
    SOFTWARE_UPDATE_LOG_SCHEMA_VERSION,
    SoftwareUpdateEntry,
    load_software_update_entries,
    software_update_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "software_update_log.json"


def test_schema_version() -> None:
    assert SOFTWARE_UPDATE_LOG_SCHEMA_VERSION == "software_update_log_v1"


def test_disclaimer_present() -> None:
    assert "does not authorize external submission" in SOFTWARE_UPDATE_LOG_DISCLAIMER
    assert "does not constitute a detection claim" in SOFTWARE_UPDATE_LOG_DISCLAIMER


def test_allowed_update_kinds_complete() -> None:
    assert "pipeline_update" in ALLOWED_UPDATE_KINDS
    assert "firmware_update" in ALLOWED_UPDATE_KINDS
    assert "os_patch" in ALLOWED_UPDATE_KINDS
    assert "driver_update" in ALLOWED_UPDATE_KINDS
    assert "config_deploy" in ALLOWED_UPDATE_KINDS


def test_allowed_statuses_complete() -> None:
    assert "deployed" in ALLOWED_UPDATE_STATUSES
    assert "failed" in ALLOWED_UPDATE_STATUSES
    assert "rolled_back" in ALLOWED_UPDATE_STATUSES
    assert "pending" in ALLOWED_UPDATE_STATUSES


def test_load_entries_count() -> None:
    entries = load_software_update_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_load_entries_types() -> None:
    entries = load_software_update_entries(FIXTURE_PATH)
    for e in entries:
        assert isinstance(e, SoftwareUpdateEntry)


def test_entry_ids_unique() -> None:
    entries = load_software_update_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_update_kinds_valid() -> None:
    entries = load_software_update_entries(FIXTURE_PATH)
    for e in entries:
        assert e.update_kind in ALLOWED_UPDATE_KINDS


def test_statuses_valid() -> None:
    entries = load_software_update_entries(FIXTURE_PATH)
    for e in entries:
        assert e.status in ALLOWED_UPDATE_STATUSES


def test_deployed_count() -> None:
    entries = load_software_update_entries(FIXTURE_PATH)
    deployed = [e for e in entries if e.status == "deployed"]
    assert len(deployed) == 2


def test_failed_count() -> None:
    entries = load_software_update_entries(FIXTURE_PATH)
    failed = [e for e in entries if e.status == "failed"]
    assert len(failed) == 1


def test_rolled_back_count() -> None:
    entries = load_software_update_entries(FIXTURE_PATH)
    rolled_back = [e for e in entries if e.status == "rolled_back"]
    assert len(rolled_back) == 1


def test_pending_count() -> None:
    entries = load_software_update_entries(FIXTURE_PATH)
    pending = [e for e in entries if e.status == "pending"]
    assert len(pending) == 1


def test_entry_as_dict() -> None:
    entries = load_software_update_entries(FIXTURE_PATH)
    d = entries[0].as_dict()
    assert "entry_id" in d
    assert "update_kind" in d
    assert "status" in d


def test_summary_schema_version() -> None:
    summary = software_update_summary(FIXTURE_PATH)
    assert summary["schema_version"] == SOFTWARE_UPDATE_LOG_SCHEMA_VERSION


def test_summary_entry_count() -> None:
    summary = software_update_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_deployed_count() -> None:
    summary = software_update_summary(FIXTURE_PATH)
    assert summary["deployed_count"] == 2


def test_summary_failed_count() -> None:
    summary = software_update_summary(FIXTURE_PATH)
    assert summary["failed_count"] == 1


def test_summary_rolled_back_count() -> None:
    summary = software_update_summary(FIXTURE_PATH)
    assert summary["rolled_back_count"] == 1


def test_summary_pending_count() -> None:
    summary = software_update_summary(FIXTURE_PATH)
    assert summary["pending_count"] == 1


def test_summary_counts_by_kind() -> None:
    summary = software_update_summary(FIXTURE_PATH)
    assert isinstance(summary["counts_by_kind"], dict)
    assert sum(summary["counts_by_kind"].values()) == 5
