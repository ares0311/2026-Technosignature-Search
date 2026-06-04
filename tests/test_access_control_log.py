"""Tests for access_control_log operational provenance records."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.access_control_log import (
    ACCESS_CONTROL_LOG_DISCLAIMER,
    ACCESS_CONTROL_LOG_SCHEMA_VERSION,
    ALLOWED_ACCESS_CONTROL_KINDS,
    ALLOWED_ACCESS_CONTROL_STATUSES,
    AccessControlEntry,
    access_control_summary,
    load_access_control_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "access_control_log.json"


def test_fixture_loads() -> None:
    entries = load_access_control_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_has_allowed_status() -> None:
    entries = load_access_control_entries(FIXTURE_PATH)
    statuses = {e.status for e in entries}
    assert "allowed" in statuses


def test_fixture_has_blocked_status() -> None:
    entries = load_access_control_entries(FIXTURE_PATH)
    statuses = {e.status for e in entries}
    assert "blocked" in statuses


def test_fixture_has_expired_status() -> None:
    entries = load_access_control_entries(FIXTURE_PATH)
    statuses = {e.status for e in entries}
    assert "expired" in statuses


def test_fixture_has_pending_status() -> None:
    entries = load_access_control_entries(FIXTURE_PATH)
    statuses = {e.status for e in entries}
    assert "pending" in statuses


def test_allowed_kinds_count() -> None:
    assert len(ALLOWED_ACCESS_CONTROL_KINDS) == 5


def test_allowed_statuses_count() -> None:
    assert len(ALLOWED_ACCESS_CONTROL_STATUSES) == 4


def test_invalid_kind_raises() -> None:
    with pytest.raises(ValueError, match="access_kind"):
        AccessControlEntry(
            entry_id="x",
            access_kind="invalid_kind",
            status="allowed",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-06-01T00:00:00Z",
            notes=None,
        )


def test_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="status"):
        AccessControlEntry(
            entry_id="x",
            access_kind="access_grant",
            status="invalid_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-06-01T00:00:00Z",
            notes=None,
        )


def test_dataclass_is_frozen() -> None:
    entry = AccessControlEntry(
        entry_id="x",
        access_kind="access_grant",
        status="allowed",
        actor_id="op",
        resource_id="res",
        timestamp_utc="2026-06-01T00:00:00Z",
        notes=None,
    )
    with pytest.raises((AttributeError, TypeError)):
        entry.status = "blocked"  # type: ignore[misc]


def test_summary_entry_count() -> None:
    result = access_control_summary(FIXTURE_PATH)
    assert result["entry_count"] == 5


def test_summary_allowed_count() -> None:
    result = access_control_summary(FIXTURE_PATH)
    assert result["allowed_count"] == 2


def test_summary_by_kind() -> None:
    result = access_control_summary(FIXTURE_PATH)
    assert isinstance(result["by_kind"], dict)
    assert sum(result["by_kind"].values()) == 5


def test_summary_by_status() -> None:
    result = access_control_summary(FIXTURE_PATH)
    assert isinstance(result["by_status"], dict)
    assert sum(result["by_status"].values()) == 5


def test_summary_schema_version() -> None:
    result = access_control_summary(FIXTURE_PATH)
    assert result["schema_version"] == ACCESS_CONTROL_LOG_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    result = access_control_summary(FIXTURE_PATH)
    assert result["disclaimer"] == ACCESS_CONTROL_LOG_DISCLAIMER


def test_disclaimer_no_detection_claim() -> None:
    assert "does not constitute a detection claim" in ACCESS_CONTROL_LOG_DISCLAIMER


def test_disclaimer_no_external_submission() -> None:
    assert "does not authorize external submission" in ACCESS_CONTROL_LOG_DISCLAIMER


def test_disclaimer_no_score_change() -> None:
    assert "does not modify candidate scores" in ACCESS_CONTROL_LOG_DISCLAIMER


def test_schema_version_string() -> None:
    assert ACCESS_CONTROL_LOG_SCHEMA_VERSION == "access_control_log_v1"


def test_fixture_schema_version() -> None:
    raw = json.loads(FIXTURE_PATH.read_text())
    assert raw["schema_version"] == "access_control_log_v1"


def test_notes_optional() -> None:
    entries = load_access_control_entries(FIXTURE_PATH)
    notes_values = [e.notes for e in entries]
    assert None in notes_values
