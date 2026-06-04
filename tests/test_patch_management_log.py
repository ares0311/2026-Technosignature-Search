from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.patch_management_log import (
    ALLOWED_PATCH_MANAGEMENT_KINDS,
    ALLOWED_PATCH_MANAGEMENT_STATUSES,
    PATCH_MANAGEMENT_LOG_DISCLAIMER,
    PATCH_MANAGEMENT_LOG_SCHEMA_VERSION,
    PatchManagementEntry,
    load_patch_management_entries,
    patch_management_summary,
)

FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "patch_management_log.json"
)


def test_allowed_kinds_not_empty() -> None:
    assert len(ALLOWED_PATCH_MANAGEMENT_KINDS) > 0


def test_allowed_statuses_not_empty() -> None:
    assert len(ALLOWED_PATCH_MANAGEMENT_STATUSES) > 0


def test_expected_kinds_present() -> None:
    assert "security_patch" in ALLOWED_PATCH_MANAGEMENT_KINDS
    assert "critical_patch" in ALLOWED_PATCH_MANAGEMENT_KINDS
    assert "hotfix" in ALLOWED_PATCH_MANAGEMENT_KINDS
    assert "rollback" in ALLOWED_PATCH_MANAGEMENT_KINDS
    assert "feature_update" in ALLOWED_PATCH_MANAGEMENT_KINDS


def test_expected_statuses_present() -> None:
    assert "applied" in ALLOWED_PATCH_MANAGEMENT_STATUSES
    assert "failed" in ALLOWED_PATCH_MANAGEMENT_STATUSES
    assert "pending" in ALLOWED_PATCH_MANAGEMENT_STATUSES
    assert "skipped" in ALLOWED_PATCH_MANAGEMENT_STATUSES


def test_schema_version_string() -> None:
    assert isinstance(PATCH_MANAGEMENT_LOG_SCHEMA_VERSION, str)
    assert len(PATCH_MANAGEMENT_LOG_SCHEMA_VERSION) > 0


def test_disclaimer_string() -> None:
    assert isinstance(PATCH_MANAGEMENT_LOG_DISCLAIMER, str)
    assert "does not" in PATCH_MANAGEMENT_LOG_DISCLAIMER


def test_entry_valid_construction() -> None:
    entry = PatchManagementEntry(
        entry_id="pm-test-001",
        patch_kind="security_patch",
        status="applied",
        actor_id="operator-x",
        resource_id="pipeline-v1",
        timestamp_utc="2026-06-01T00:00:00Z",
        notes=None,
    )
    assert entry.entry_id == "pm-test-001"
    assert entry.patch_kind == "security_patch"
    assert entry.status == "applied"


def test_entry_invalid_kind_raises() -> None:
    with pytest.raises(ValueError, match="patch_kind"):
        PatchManagementEntry(
            entry_id="pm-bad",
            patch_kind="unknown_kind",
            status="applied",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-06-01T00:00:00Z",
            notes=None,
        )


def test_entry_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="status"):
        PatchManagementEntry(
            entry_id="pm-bad",
            patch_kind="hotfix",
            status="unknown_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-06-01T00:00:00Z",
            notes=None,
        )


def test_load_fixture_returns_entries() -> None:
    entries = load_patch_management_entries(FIXTURE_PATH)
    assert len(entries) >= 1


def test_fixture_has_expected_count() -> None:
    entries = load_patch_management_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_has_applied_entries() -> None:
    entries = load_patch_management_entries(FIXTURE_PATH)
    applied = [e for e in entries if e.status == "applied"]
    assert len(applied) >= 1


def test_fixture_covers_multiple_kinds() -> None:
    entries = load_patch_management_entries(FIXTURE_PATH)
    kinds = {e.patch_kind for e in entries}
    assert len(kinds) >= 3


def test_summary_schema_version() -> None:
    summary = patch_management_summary(FIXTURE_PATH)
    assert summary["schema_version"] == PATCH_MANAGEMENT_LOG_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    summary = patch_management_summary(FIXTURE_PATH)
    assert "does not" in summary["disclaimer"]


def test_summary_entry_count() -> None:
    summary = patch_management_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_applied_count() -> None:
    summary = patch_management_summary(FIXTURE_PATH)
    assert summary["applied_count"] >= 1


def test_summary_by_kind() -> None:
    summary = patch_management_summary(FIXTURE_PATH)
    assert isinstance(summary["by_kind"], dict)
    assert len(summary["by_kind"]) >= 1


def test_summary_by_status() -> None:
    summary = patch_management_summary(FIXTURE_PATH)
    assert isinstance(summary["by_status"], dict)
    assert "applied" in summary["by_status"]


def test_fixture_json_parseable() -> None:
    raw = json.loads(FIXTURE_PATH.read_text())
    assert "entries" in raw
    assert raw["schema_version"] == PATCH_MANAGEMENT_LOG_SCHEMA_VERSION
