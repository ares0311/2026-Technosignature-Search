"""Tests for change_management_log operational provenance records."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.change_management_log import (
    ALLOWED_CHANGE_MANAGEMENT_KINDS,
    ALLOWED_CHANGE_MANAGEMENT_STATUSES,
    CHANGE_MANAGEMENT_LOG_DISCLAIMER,
    CHANGE_MANAGEMENT_LOG_SCHEMA_VERSION,
    ChangeManagementEntry,
    change_management_summary,
    load_change_management_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "change_management_log.json"


def test_fixture_loads() -> None:
    entries = load_change_management_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_has_completed_status() -> None:
    entries = load_change_management_entries(FIXTURE_PATH)
    statuses = {e.status for e in entries}
    assert "completed" in statuses


def test_fixture_has_approved_status() -> None:
    entries = load_change_management_entries(FIXTURE_PATH)
    statuses = {e.status for e in entries}
    assert "approved" in statuses


def test_fixture_has_pending_status() -> None:
    entries = load_change_management_entries(FIXTURE_PATH)
    statuses = {e.status for e in entries}
    assert "pending" in statuses


def test_fixture_has_rejected_status() -> None:
    entries = load_change_management_entries(FIXTURE_PATH)
    statuses = {e.status for e in entries}
    assert "rejected" in statuses


def test_allowed_kinds_count() -> None:
    assert len(ALLOWED_CHANGE_MANAGEMENT_KINDS) == 5


def test_allowed_statuses_count() -> None:
    assert len(ALLOWED_CHANGE_MANAGEMENT_STATUSES) == 4


def test_invalid_kind_raises() -> None:
    with pytest.raises(ValueError, match="change_kind"):
        ChangeManagementEntry(
            entry_id="x",
            change_kind="invalid_kind",
            status="completed",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-06-01T00:00:00Z",
            notes=None,
        )


def test_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="status"):
        ChangeManagementEntry(
            entry_id="x",
            change_kind="planned_change",
            status="invalid_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-06-01T00:00:00Z",
            notes=None,
        )


def test_dataclass_is_frozen() -> None:
    entry = ChangeManagementEntry(
        entry_id="x",
        change_kind="planned_change",
        status="completed",
        actor_id="op",
        resource_id="res",
        timestamp_utc="2026-06-01T00:00:00Z",
        notes=None,
    )
    with pytest.raises((AttributeError, TypeError)):
        entry.status = "pending"  # type: ignore[misc]


def test_summary_entry_count() -> None:
    result = change_management_summary(FIXTURE_PATH)
    assert result["entry_count"] == 5


def test_summary_completed_count() -> None:
    result = change_management_summary(FIXTURE_PATH)
    assert result["completed_count"] == 2


def test_summary_by_kind() -> None:
    result = change_management_summary(FIXTURE_PATH)
    assert isinstance(result["by_kind"], dict)
    assert sum(result["by_kind"].values()) == 5


def test_summary_by_status() -> None:
    result = change_management_summary(FIXTURE_PATH)
    assert isinstance(result["by_status"], dict)
    assert sum(result["by_status"].values()) == 5


def test_summary_schema_version() -> None:
    result = change_management_summary(FIXTURE_PATH)
    assert result["schema_version"] == CHANGE_MANAGEMENT_LOG_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    result = change_management_summary(FIXTURE_PATH)
    assert result["disclaimer"] == CHANGE_MANAGEMENT_LOG_DISCLAIMER


def test_disclaimer_no_detection_claim() -> None:
    assert "does not constitute a detection claim" in CHANGE_MANAGEMENT_LOG_DISCLAIMER


def test_disclaimer_no_external_submission() -> None:
    assert "does not authorize external submission" in CHANGE_MANAGEMENT_LOG_DISCLAIMER


def test_disclaimer_no_score_change() -> None:
    assert "does not modify candidate scores" in CHANGE_MANAGEMENT_LOG_DISCLAIMER


def test_schema_version_string() -> None:
    assert CHANGE_MANAGEMENT_LOG_SCHEMA_VERSION == "change_management_log_v1"


def test_fixture_schema_version() -> None:
    raw = json.loads(FIXTURE_PATH.read_text())
    assert raw["schema_version"] == "change_management_log_v1"


def test_notes_optional() -> None:
    entries = load_change_management_entries(FIXTURE_PATH)
    notes_values = [e.notes for e in entries]
    assert None in notes_values
