from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.release_management_log import (
    ALLOWED_RELEASE_MANAGEMENT_KINDS,
    ALLOWED_RELEASE_MANAGEMENT_STATUSES,
    RELEASE_MANAGEMENT_LOG_SCHEMA_VERSION,
    ReleaseManagementEntry,
    load_release_management_entries,
    release_management_summary,
)

FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "release_management_log.json"
)


def test_fixture_loads() -> None:
    entries = load_release_management_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_schema_version() -> None:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert data["schema_version"] == RELEASE_MANAGEMENT_LOG_SCHEMA_VERSION


def test_entry_ids_unique() -> None:
    entries = load_release_management_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_all_release_kinds_valid() -> None:
    entries = load_release_management_entries(FIXTURE_PATH)
    for entry in entries:
        assert entry.release_kind in ALLOWED_RELEASE_MANAGEMENT_KINDS


def test_all_statuses_valid() -> None:
    entries = load_release_management_entries(FIXTURE_PATH)
    for entry in entries:
        assert entry.status in ALLOWED_RELEASE_MANAGEMENT_STATUSES


def test_deployed_count() -> None:
    entries = load_release_management_entries(FIXTURE_PATH)
    deployed = [e for e in entries if e.status == "deployed"]
    assert len(deployed) == 2


def test_approved_present() -> None:
    entries = load_release_management_entries(FIXTURE_PATH)
    assert any(e.status == "approved" for e in entries)


def test_planned_present() -> None:
    entries = load_release_management_entries(FIXTURE_PATH)
    assert any(e.status == "planned" for e in entries)


def test_rolled_back_present() -> None:
    entries = load_release_management_entries(FIXTURE_PATH)
    assert any(e.status == "rolled_back" for e in entries)


def test_minor_release_kind_present() -> None:
    entries = load_release_management_entries(FIXTURE_PATH)
    assert any(e.release_kind == "minor_release" for e in entries)


def test_rollback_kind_present() -> None:
    entries = load_release_management_entries(FIXTURE_PATH)
    assert any(e.release_kind == "rollback" for e in entries)


def test_summary_entry_count() -> None:
    summary = release_management_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_deployed_count() -> None:
    summary = release_management_summary(FIXTURE_PATH)
    assert summary["deployed_count"] == 2


def test_summary_schema_version() -> None:
    summary = release_management_summary(FIXTURE_PATH)
    assert summary["schema_version"] == RELEASE_MANAGEMENT_LOG_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    summary = release_management_summary(FIXTURE_PATH)
    assert "operational provenance records" in summary["disclaimer"]


def test_summary_disclaimer_no_detection_claim() -> None:
    summary = release_management_summary(FIXTURE_PATH)
    assert "detection claim" in summary["disclaimer"]


def test_dataclass_invalid_release_kind() -> None:
    with pytest.raises(ValueError, match="release_kind"):
        ReleaseManagementEntry(
            entry_id="x",
            release_kind="invalid_kind",
            status="deployed",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes="",
        )


def test_dataclass_invalid_status() -> None:
    with pytest.raises(ValueError, match="status"):
        ReleaseManagementEntry(
            entry_id="x",
            release_kind="patch_release",
            status="invalid_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes="",
        )


def test_dataclass_frozen() -> None:
    entry = ReleaseManagementEntry(
        entry_id="x",
        release_kind="hotfix",
        status="planned",
        actor_id="op",
        resource_id="res",
        timestamp_utc="2026-01-01T00:00:00Z",
        notes="",
    )
    with pytest.raises(AttributeError):
        entry.status = "deployed"  # type: ignore[misc]


def test_allowed_kinds_completeness() -> None:
    assert "hotfix" in ALLOWED_RELEASE_MANAGEMENT_KINDS
    assert "major_release" in ALLOWED_RELEASE_MANAGEMENT_KINDS
    assert "minor_release" in ALLOWED_RELEASE_MANAGEMENT_KINDS
    assert "patch_release" in ALLOWED_RELEASE_MANAGEMENT_KINDS
    assert "rollback" in ALLOWED_RELEASE_MANAGEMENT_KINDS


def test_allowed_statuses_completeness() -> None:
    assert "approved" in ALLOWED_RELEASE_MANAGEMENT_STATUSES
    assert "deployed" in ALLOWED_RELEASE_MANAGEMENT_STATUSES
    assert "planned" in ALLOWED_RELEASE_MANAGEMENT_STATUSES
    assert "rolled_back" in ALLOWED_RELEASE_MANAGEMENT_STATUSES


def test_no_external_submission_in_disclaimer() -> None:
    summary = release_management_summary(FIXTURE_PATH)
    assert "external submission" in summary["disclaimer"]
