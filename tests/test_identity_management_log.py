from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.identity_management_log import (
    ALLOWED_IDENTITY_MANAGEMENT_KINDS,
    ALLOWED_IDENTITY_MANAGEMENT_STATUSES,
    IDENTITY_MANAGEMENT_LOG_DISCLAIMER,
    IDENTITY_MANAGEMENT_LOG_SCHEMA_VERSION,
    IdentityManagementEntry,
    identity_management_summary,
    load_identity_management_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "identity_management_log.json"


def test_allowed_kinds_not_empty() -> None:
    assert len(ALLOWED_IDENTITY_MANAGEMENT_KINDS) > 0


def test_allowed_statuses_not_empty() -> None:
    assert len(ALLOWED_IDENTITY_MANAGEMENT_STATUSES) > 0


def test_expected_kinds_present() -> None:
    assert "account_creation" in ALLOWED_IDENTITY_MANAGEMENT_KINDS
    assert "account_deletion" in ALLOWED_IDENTITY_MANAGEMENT_KINDS
    assert "password_reset" in ALLOWED_IDENTITY_MANAGEMENT_KINDS
    assert "privilege_change" in ALLOWED_IDENTITY_MANAGEMENT_KINDS
    assert "role_assignment" in ALLOWED_IDENTITY_MANAGEMENT_KINDS


def test_expected_statuses_present() -> None:
    assert "active" in ALLOWED_IDENTITY_MANAGEMENT_STATUSES
    assert "expired" in ALLOWED_IDENTITY_MANAGEMENT_STATUSES
    assert "pending" in ALLOWED_IDENTITY_MANAGEMENT_STATUSES
    assert "revoked" in ALLOWED_IDENTITY_MANAGEMENT_STATUSES


def test_schema_version_string() -> None:
    assert isinstance(IDENTITY_MANAGEMENT_LOG_SCHEMA_VERSION, str)
    assert len(IDENTITY_MANAGEMENT_LOG_SCHEMA_VERSION) > 0


def test_disclaimer_string() -> None:
    assert isinstance(IDENTITY_MANAGEMENT_LOG_DISCLAIMER, str)
    assert "does not" in IDENTITY_MANAGEMENT_LOG_DISCLAIMER


def test_entry_valid_construction() -> None:
    entry = IdentityManagementEntry(
        entry_id="im-test-001",
        identity_kind="account_creation",
        status="active",
        actor_id="operator-x",
        resource_id="pipeline-v1",
        timestamp_utc="2026-06-01T00:00:00Z",
        notes=None,
    )
    assert entry.entry_id == "im-test-001"
    assert entry.identity_kind == "account_creation"
    assert entry.status == "active"


def test_entry_invalid_kind_raises() -> None:
    with pytest.raises(ValueError, match="identity_kind"):
        IdentityManagementEntry(
            entry_id="im-bad",
            identity_kind="unknown_kind",
            status="active",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-06-01T00:00:00Z",
            notes=None,
        )


def test_entry_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="status"):
        IdentityManagementEntry(
            entry_id="im-bad",
            identity_kind="role_assignment",
            status="unknown_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-06-01T00:00:00Z",
            notes=None,
        )


def test_load_fixture_returns_entries() -> None:
    entries = load_identity_management_entries(FIXTURE_PATH)
    assert len(entries) >= 1


def test_fixture_has_expected_count() -> None:
    entries = load_identity_management_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_has_active_entries() -> None:
    entries = load_identity_management_entries(FIXTURE_PATH)
    active = [e for e in entries if e.status == "active"]
    assert len(active) >= 1


def test_fixture_covers_multiple_kinds() -> None:
    entries = load_identity_management_entries(FIXTURE_PATH)
    kinds = {e.identity_kind for e in entries}
    assert len(kinds) >= 3


def test_summary_schema_version() -> None:
    summary = identity_management_summary(FIXTURE_PATH)
    assert summary["schema_version"] == IDENTITY_MANAGEMENT_LOG_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    summary = identity_management_summary(FIXTURE_PATH)
    assert "does not" in summary["disclaimer"]


def test_summary_entry_count() -> None:
    summary = identity_management_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_active_count() -> None:
    summary = identity_management_summary(FIXTURE_PATH)
    assert summary["active_count"] >= 1


def test_summary_by_kind() -> None:
    summary = identity_management_summary(FIXTURE_PATH)
    assert isinstance(summary["by_kind"], dict)
    assert len(summary["by_kind"]) >= 1


def test_summary_by_status() -> None:
    summary = identity_management_summary(FIXTURE_PATH)
    assert isinstance(summary["by_status"], dict)
    assert "active" in summary["by_status"]


def test_fixture_json_parseable() -> None:
    raw = json.loads(FIXTURE_PATH.read_text())
    assert "entries" in raw
    assert raw["schema_version"] == IDENTITY_MANAGEMENT_LOG_SCHEMA_VERSION


def test_entry_has_resource_id() -> None:
    entries = load_identity_management_entries(FIXTURE_PATH)
    for entry in entries:
        assert isinstance(entry.resource_id, str)
        assert len(entry.resource_id) > 0


def test_load_returns_identity_management_entry_instances() -> None:
    entries = load_identity_management_entries(FIXTURE_PATH)
    for entry in entries:
        assert isinstance(entry, IdentityManagementEntry)
