from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.alert_escalation_log import (
    ALERT_ESCALATION_LOG_SCHEMA_VERSION,
    ALLOWED_ALERT_ESCALATION_KINDS,
    ALLOWED_ALERT_ESCALATION_STATUSES,
    AlertEscalationEntry,
    alert_escalation_summary,
    load_alert_escalation_entries,
)

FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "alert_escalation_log.json"
)


def test_fixture_loads() -> None:
    entries = load_alert_escalation_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_schema_version() -> None:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert data["schema_version"] == ALERT_ESCALATION_LOG_SCHEMA_VERSION


def test_entry_ids_unique() -> None:
    entries = load_alert_escalation_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_all_escalation_kinds_valid() -> None:
    entries = load_alert_escalation_entries(FIXTURE_PATH)
    for entry in entries:
        assert entry.escalation_kind in ALLOWED_ALERT_ESCALATION_KINDS


def test_all_statuses_valid() -> None:
    entries = load_alert_escalation_entries(FIXTURE_PATH)
    for entry in entries:
        assert entry.status in ALLOWED_ALERT_ESCALATION_STATUSES


def test_resolved_count() -> None:
    entries = load_alert_escalation_entries(FIXTURE_PATH)
    resolved = [e for e in entries if e.status == "resolved"]
    assert len(resolved) == 2


def test_escalated_present() -> None:
    entries = load_alert_escalation_entries(FIXTURE_PATH)
    assert any(e.status == "escalated" for e in entries)


def test_acknowledged_present() -> None:
    entries = load_alert_escalation_entries(FIXTURE_PATH)
    assert any(e.status == "acknowledged" for e in entries)


def test_unacknowledged_present() -> None:
    entries = load_alert_escalation_entries(FIXTURE_PATH)
    assert any(e.status == "unacknowledged" for e in entries)


def test_automatic_escalation_kind_present() -> None:
    entries = load_alert_escalation_entries(FIXTURE_PATH)
    assert any(e.escalation_kind == "automatic_escalation" for e in entries)


def test_page_oncall_kind_present() -> None:
    entries = load_alert_escalation_entries(FIXTURE_PATH)
    assert any(e.escalation_kind == "page_oncall" for e in entries)


def test_summary_entry_count() -> None:
    summary = alert_escalation_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_resolved_count() -> None:
    summary = alert_escalation_summary(FIXTURE_PATH)
    assert summary["resolved_count"] == 2


def test_summary_schema_version() -> None:
    summary = alert_escalation_summary(FIXTURE_PATH)
    assert summary["schema_version"] == ALERT_ESCALATION_LOG_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    summary = alert_escalation_summary(FIXTURE_PATH)
    assert "operational provenance records" in summary["disclaimer"]


def test_summary_disclaimer_no_detection_claim() -> None:
    summary = alert_escalation_summary(FIXTURE_PATH)
    assert "detection claim" in summary["disclaimer"]


def test_dataclass_invalid_escalation_kind() -> None:
    with pytest.raises(ValueError, match="escalation_kind"):
        AlertEscalationEntry(
            entry_id="x",
            escalation_kind="invalid_kind",
            status="escalated",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes="",
        )


def test_dataclass_invalid_status() -> None:
    with pytest.raises(ValueError, match="status"):
        AlertEscalationEntry(
            entry_id="x",
            escalation_kind="automatic_escalation",
            status="invalid_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes="",
        )


def test_dataclass_frozen() -> None:
    entry = AlertEscalationEntry(
        entry_id="x",
        escalation_kind="reassignment",
        status="acknowledged",
        actor_id="op",
        resource_id="res",
        timestamp_utc="2026-01-01T00:00:00Z",
        notes="",
    )
    with pytest.raises(AttributeError):
        entry.status = "resolved"  # type: ignore[misc]


def test_allowed_kinds_completeness() -> None:
    assert "automatic_escalation" in ALLOWED_ALERT_ESCALATION_KINDS
    assert "manual_escalation" in ALLOWED_ALERT_ESCALATION_KINDS
    assert "page_oncall" in ALLOWED_ALERT_ESCALATION_KINDS
    assert "reassignment" in ALLOWED_ALERT_ESCALATION_KINDS
    assert "resolution_escalation" in ALLOWED_ALERT_ESCALATION_KINDS


def test_allowed_statuses_completeness() -> None:
    assert "acknowledged" in ALLOWED_ALERT_ESCALATION_STATUSES
    assert "escalated" in ALLOWED_ALERT_ESCALATION_STATUSES
    assert "resolved" in ALLOWED_ALERT_ESCALATION_STATUSES
    assert "unacknowledged" in ALLOWED_ALERT_ESCALATION_STATUSES


def test_no_external_submission_in_disclaimer() -> None:
    summary = alert_escalation_summary(FIXTURE_PATH)
    assert "external submission" in summary["disclaimer"]
