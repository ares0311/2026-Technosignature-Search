"""Tests for incident_log operational provenance records."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.incident_log import (
    ALLOWED_INCIDENT_KINDS,
    ALLOWED_INCIDENT_STATUSES,
    INCIDENT_LOG_DISCLAIMER,
    INCIDENT_LOG_SCHEMA_VERSION,
    IncidentEntry,
    incident_summary,
    load_incident_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "incident_log.json"


def test_fixture_loads() -> None:
    entries = load_incident_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_has_closed_status() -> None:
    entries = load_incident_entries(FIXTURE_PATH)
    statuses = {e.status for e in entries}
    assert "closed" in statuses


def test_fixture_has_open_status() -> None:
    entries = load_incident_entries(FIXTURE_PATH)
    statuses = {e.status for e in entries}
    assert "open" in statuses


def test_fixture_has_under_investigation_status() -> None:
    entries = load_incident_entries(FIXTURE_PATH)
    statuses = {e.status for e in entries}
    assert "under_investigation" in statuses


def test_fixture_has_escalated_status() -> None:
    entries = load_incident_entries(FIXTURE_PATH)
    statuses = {e.status for e in entries}
    assert "escalated" in statuses


def test_allowed_kinds_count() -> None:
    assert len(ALLOWED_INCIDENT_KINDS) == 5


def test_allowed_statuses_count() -> None:
    assert len(ALLOWED_INCIDENT_STATUSES) == 4


def test_invalid_kind_raises() -> None:
    with pytest.raises(ValueError, match="incident_kind"):
        IncidentEntry(
            entry_id="x",
            incident_kind="invalid_kind",
            status="open",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-06-01T00:00:00Z",
            notes=None,
        )


def test_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="status"):
        IncidentEntry(
            entry_id="x",
            incident_kind="software_incident",
            status="invalid_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-06-01T00:00:00Z",
            notes=None,
        )


def test_dataclass_is_frozen() -> None:
    entry = IncidentEntry(
        entry_id="x",
        incident_kind="software_incident",
        status="open",
        actor_id="op",
        resource_id="res",
        timestamp_utc="2026-06-01T00:00:00Z",
        notes=None,
    )
    with pytest.raises((AttributeError, TypeError)):
        entry.status = "closed"  # type: ignore[misc]


def test_summary_entry_count() -> None:
    result = incident_summary(FIXTURE_PATH)
    assert result["entry_count"] == 5


def test_summary_open_count() -> None:
    result = incident_summary(FIXTURE_PATH)
    assert result["open_count"] == 1


def test_summary_by_kind() -> None:
    result = incident_summary(FIXTURE_PATH)
    assert isinstance(result["by_kind"], dict)
    assert sum(result["by_kind"].values()) == 5


def test_summary_by_status() -> None:
    result = incident_summary(FIXTURE_PATH)
    assert isinstance(result["by_status"], dict)
    assert sum(result["by_status"].values()) == 5


def test_summary_schema_version() -> None:
    result = incident_summary(FIXTURE_PATH)
    assert result["schema_version"] == INCIDENT_LOG_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    result = incident_summary(FIXTURE_PATH)
    assert result["disclaimer"] == INCIDENT_LOG_DISCLAIMER


def test_disclaimer_no_detection_claim() -> None:
    assert "does not constitute a detection claim" in INCIDENT_LOG_DISCLAIMER


def test_disclaimer_no_external_submission() -> None:
    assert "does not authorize external submission" in INCIDENT_LOG_DISCLAIMER


def test_disclaimer_no_score_change() -> None:
    assert "does not modify candidate scores" in INCIDENT_LOG_DISCLAIMER


def test_schema_version_string() -> None:
    assert INCIDENT_LOG_SCHEMA_VERSION == "incident_log_v1"


def test_fixture_schema_version() -> None:
    raw = json.loads(FIXTURE_PATH.read_text())
    assert raw["schema_version"] == "incident_log_v1"


def test_notes_optional() -> None:
    entries = load_incident_entries(FIXTURE_PATH)
    notes_values = [e.notes for e in entries]
    assert None in notes_values
