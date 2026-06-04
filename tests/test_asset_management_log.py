from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.asset_management_log import (
    ALLOWED_ASSET_MANAGEMENT_KINDS,
    ALLOWED_ASSET_MANAGEMENT_STATUSES,
    ASSET_MANAGEMENT_LOG_DISCLAIMER,
    ASSET_MANAGEMENT_LOG_SCHEMA_VERSION,
    AssetManagementEntry,
    asset_management_summary,
    load_asset_management_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "asset_management_log.json"


def test_allowed_kinds_not_empty() -> None:
    assert len(ALLOWED_ASSET_MANAGEMENT_KINDS) > 0


def test_allowed_statuses_not_empty() -> None:
    assert len(ALLOWED_ASSET_MANAGEMENT_STATUSES) > 0


def test_expected_kinds_present() -> None:
    assert "asset_acquisition" in ALLOWED_ASSET_MANAGEMENT_KINDS
    assert "asset_audit" in ALLOWED_ASSET_MANAGEMENT_KINDS
    assert "asset_decommission" in ALLOWED_ASSET_MANAGEMENT_KINDS
    assert "asset_maintenance" in ALLOWED_ASSET_MANAGEMENT_KINDS
    assert "asset_transfer" in ALLOWED_ASSET_MANAGEMENT_KINDS


def test_expected_statuses_present() -> None:
    assert "active" in ALLOWED_ASSET_MANAGEMENT_STATUSES
    assert "decommissioned" in ALLOWED_ASSET_MANAGEMENT_STATUSES
    assert "pending" in ALLOWED_ASSET_MANAGEMENT_STATUSES
    assert "under_maintenance" in ALLOWED_ASSET_MANAGEMENT_STATUSES


def test_schema_version_string() -> None:
    assert isinstance(ASSET_MANAGEMENT_LOG_SCHEMA_VERSION, str)
    assert len(ASSET_MANAGEMENT_LOG_SCHEMA_VERSION) > 0


def test_disclaimer_string() -> None:
    assert isinstance(ASSET_MANAGEMENT_LOG_DISCLAIMER, str)
    assert "does not" in ASSET_MANAGEMENT_LOG_DISCLAIMER


def test_entry_valid_construction() -> None:
    entry = AssetManagementEntry(
        entry_id="am-test-001",
        asset_kind="asset_audit",
        status="active",
        actor_id="operator-x",
        resource_id="server-rack-1",
        timestamp_utc="2026-06-01T00:00:00Z",
        notes=None,
    )
    assert entry.entry_id == "am-test-001"
    assert entry.asset_kind == "asset_audit"
    assert entry.status == "active"


def test_entry_invalid_kind_raises() -> None:
    with pytest.raises(ValueError, match="asset_kind"):
        AssetManagementEntry(
            entry_id="am-bad",
            asset_kind="unknown_kind",
            status="active",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-06-01T00:00:00Z",
            notes=None,
        )


def test_entry_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="status"):
        AssetManagementEntry(
            entry_id="am-bad",
            asset_kind="asset_audit",
            status="unknown_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-06-01T00:00:00Z",
            notes=None,
        )


def test_load_fixture_returns_entries() -> None:
    entries = load_asset_management_entries(FIXTURE_PATH)
    assert len(entries) >= 1


def test_fixture_has_expected_count() -> None:
    entries = load_asset_management_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_has_active_entries() -> None:
    entries = load_asset_management_entries(FIXTURE_PATH)
    active = [e for e in entries if e.status == "active"]
    assert len(active) >= 1


def test_fixture_covers_multiple_kinds() -> None:
    entries = load_asset_management_entries(FIXTURE_PATH)
    kinds = {e.asset_kind for e in entries}
    assert len(kinds) >= 3


def test_summary_schema_version() -> None:
    summary = asset_management_summary(FIXTURE_PATH)
    assert summary["schema_version"] == ASSET_MANAGEMENT_LOG_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    summary = asset_management_summary(FIXTURE_PATH)
    assert "does not" in summary["disclaimer"]


def test_summary_entry_count() -> None:
    summary = asset_management_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_active_count() -> None:
    summary = asset_management_summary(FIXTURE_PATH)
    assert summary["active_count"] >= 1


def test_summary_by_kind() -> None:
    summary = asset_management_summary(FIXTURE_PATH)
    assert isinstance(summary["by_kind"], dict)
    assert len(summary["by_kind"]) >= 1


def test_summary_by_status() -> None:
    summary = asset_management_summary(FIXTURE_PATH)
    assert isinstance(summary["by_status"], dict)
    assert "active" in summary["by_status"]


def test_fixture_json_parseable() -> None:
    raw = json.loads(FIXTURE_PATH.read_text())
    assert "entries" in raw
    assert raw["schema_version"] == ASSET_MANAGEMENT_LOG_SCHEMA_VERSION
