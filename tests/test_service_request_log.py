from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.service_request_log import (
    ALLOWED_SERVICE_REQUEST_KINDS,
    ALLOWED_SERVICE_REQUEST_STATUSES,
    SERVICE_REQUEST_LOG_SCHEMA_VERSION,
    ServiceRequestEntry,
    load_service_request_entries,
    service_request_summary,
)

FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "service_request_log.json"
)


def test_fixture_loads() -> None:
    entries = load_service_request_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_schema_version() -> None:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert data["schema_version"] == SERVICE_REQUEST_LOG_SCHEMA_VERSION


def test_entry_ids_unique() -> None:
    entries = load_service_request_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_all_request_kinds_valid() -> None:
    entries = load_service_request_entries(FIXTURE_PATH)
    for entry in entries:
        assert entry.request_kind in ALLOWED_SERVICE_REQUEST_KINDS


def test_all_statuses_valid() -> None:
    entries = load_service_request_entries(FIXTURE_PATH)
    for entry in entries:
        assert entry.status in ALLOWED_SERVICE_REQUEST_STATUSES


def test_fulfilled_count() -> None:
    entries = load_service_request_entries(FIXTURE_PATH)
    fulfilled = [e for e in entries if e.status == "fulfilled"]
    assert len(fulfilled) == 2


def test_in_progress_present() -> None:
    entries = load_service_request_entries(FIXTURE_PATH)
    assert any(e.status == "in_progress" for e in entries)


def test_open_present() -> None:
    entries = load_service_request_entries(FIXTURE_PATH)
    assert any(e.status == "open" for e in entries)


def test_cancelled_present() -> None:
    entries = load_service_request_entries(FIXTURE_PATH)
    assert any(e.status == "cancelled" for e in entries)


def test_software_request_kind_present() -> None:
    entries = load_service_request_entries(FIXTURE_PATH)
    assert any(e.request_kind == "software_request" for e in entries)


def test_access_request_kind_present() -> None:
    entries = load_service_request_entries(FIXTURE_PATH)
    assert any(e.request_kind == "access_request" for e in entries)


def test_summary_entry_count() -> None:
    summary = service_request_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_fulfilled_count() -> None:
    summary = service_request_summary(FIXTURE_PATH)
    assert summary["fulfilled_count"] == 2


def test_summary_schema_version() -> None:
    summary = service_request_summary(FIXTURE_PATH)
    assert summary["schema_version"] == SERVICE_REQUEST_LOG_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    summary = service_request_summary(FIXTURE_PATH)
    assert "operational provenance records" in summary["disclaimer"]


def test_summary_disclaimer_no_detection_claim() -> None:
    summary = service_request_summary(FIXTURE_PATH)
    assert "detection claim" in summary["disclaimer"]


def test_dataclass_invalid_request_kind() -> None:
    with pytest.raises(ValueError, match="request_kind"):
        ServiceRequestEntry(
            entry_id="x",
            request_kind="invalid_kind",
            status="fulfilled",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes="",
        )


def test_dataclass_invalid_status() -> None:
    with pytest.raises(ValueError, match="status"):
        ServiceRequestEntry(
            entry_id="x",
            request_kind="software_request",
            status="invalid_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes="",
        )


def test_dataclass_frozen() -> None:
    entry = ServiceRequestEntry(
        entry_id="x",
        request_kind="hardware_request",
        status="open",
        actor_id="op",
        resource_id="res",
        timestamp_utc="2026-01-01T00:00:00Z",
        notes="",
    )
    with pytest.raises(AttributeError):
        entry.status = "fulfilled"  # type: ignore[misc]


def test_allowed_kinds_completeness() -> None:
    assert "access_request" in ALLOWED_SERVICE_REQUEST_KINDS
    assert "hardware_request" in ALLOWED_SERVICE_REQUEST_KINDS
    assert "information_request" in ALLOWED_SERVICE_REQUEST_KINDS
    assert "service_catalog_request" in ALLOWED_SERVICE_REQUEST_KINDS
    assert "software_request" in ALLOWED_SERVICE_REQUEST_KINDS


def test_allowed_statuses_completeness() -> None:
    assert "cancelled" in ALLOWED_SERVICE_REQUEST_STATUSES
    assert "fulfilled" in ALLOWED_SERVICE_REQUEST_STATUSES
    assert "in_progress" in ALLOWED_SERVICE_REQUEST_STATUSES
    assert "open" in ALLOWED_SERVICE_REQUEST_STATUSES


def test_no_external_submission_in_disclaimer() -> None:
    summary = service_request_summary(FIXTURE_PATH)
    assert "external submission" in summary["disclaimer"]
