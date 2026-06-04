from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.service_level_log import (
    ALLOWED_SERVICE_LEVEL_KINDS,
    ALLOWED_SERVICE_LEVEL_STATUSES,
    SERVICE_LEVEL_LOG_DISCLAIMER,
    SERVICE_LEVEL_LOG_SCHEMA_VERSION,
    ServiceLevelEntry,
    load_service_level_entries,
    service_level_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "service_level_log.json"


def test_allowed_kinds_not_empty() -> None:
    assert len(ALLOWED_SERVICE_LEVEL_KINDS) > 0


def test_allowed_statuses_not_empty() -> None:
    assert len(ALLOWED_SERVICE_LEVEL_STATUSES) > 0


def test_expected_kinds_present() -> None:
    assert "availability_check" in ALLOWED_SERVICE_LEVEL_KINDS
    assert "latency_check" in ALLOWED_SERVICE_LEVEL_KINDS
    assert "throughput_check" in ALLOWED_SERVICE_LEVEL_KINDS
    assert "error_rate_check" in ALLOWED_SERVICE_LEVEL_KINDS
    assert "compliance_check" in ALLOWED_SERVICE_LEVEL_KINDS


def test_expected_statuses_present() -> None:
    assert "met" in ALLOWED_SERVICE_LEVEL_STATUSES
    assert "missed" in ALLOWED_SERVICE_LEVEL_STATUSES
    assert "at_risk" in ALLOWED_SERVICE_LEVEL_STATUSES
    assert "not_applicable" in ALLOWED_SERVICE_LEVEL_STATUSES


def test_schema_version_string() -> None:
    assert isinstance(SERVICE_LEVEL_LOG_SCHEMA_VERSION, str)
    assert len(SERVICE_LEVEL_LOG_SCHEMA_VERSION) > 0


def test_disclaimer_string() -> None:
    assert isinstance(SERVICE_LEVEL_LOG_DISCLAIMER, str)
    assert "does not" in SERVICE_LEVEL_LOG_DISCLAIMER


def test_entry_valid_construction() -> None:
    entry = ServiceLevelEntry(
        entry_id="sl-test-001",
        level_kind="availability_check",
        status="met",
        actor_id="operator-x",
        resource_id="pipeline-runtime",
        timestamp_utc="2026-06-01T00:00:00Z",
        notes=None,
    )
    assert entry.entry_id == "sl-test-001"
    assert entry.level_kind == "availability_check"
    assert entry.status == "met"


def test_entry_invalid_kind_raises() -> None:
    with pytest.raises(ValueError, match="level_kind"):
        ServiceLevelEntry(
            entry_id="sl-bad",
            level_kind="unknown_kind",
            status="met",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-06-01T00:00:00Z",
            notes=None,
        )


def test_entry_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="status"):
        ServiceLevelEntry(
            entry_id="sl-bad",
            level_kind="latency_check",
            status="unknown_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-06-01T00:00:00Z",
            notes=None,
        )


def test_load_fixture_returns_entries() -> None:
    entries = load_service_level_entries(FIXTURE_PATH)
    assert len(entries) >= 1


def test_fixture_has_expected_count() -> None:
    entries = load_service_level_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_has_met_entries() -> None:
    entries = load_service_level_entries(FIXTURE_PATH)
    met = [e for e in entries if e.status == "met"]
    assert len(met) >= 1


def test_fixture_covers_multiple_kinds() -> None:
    entries = load_service_level_entries(FIXTURE_PATH)
    kinds = {e.level_kind for e in entries}
    assert len(kinds) >= 3


def test_summary_schema_version() -> None:
    summary = service_level_summary(FIXTURE_PATH)
    assert summary["schema_version"] == SERVICE_LEVEL_LOG_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    summary = service_level_summary(FIXTURE_PATH)
    assert "does not" in summary["disclaimer"]


def test_summary_entry_count() -> None:
    summary = service_level_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_met_count() -> None:
    summary = service_level_summary(FIXTURE_PATH)
    assert summary["met_count"] >= 1


def test_summary_by_kind() -> None:
    summary = service_level_summary(FIXTURE_PATH)
    assert isinstance(summary["by_kind"], dict)
    assert len(summary["by_kind"]) >= 1


def test_summary_by_status() -> None:
    summary = service_level_summary(FIXTURE_PATH)
    assert isinstance(summary["by_status"], dict)
    assert "met" in summary["by_status"]


def test_fixture_json_parseable() -> None:
    raw = json.loads(FIXTURE_PATH.read_text())
    assert "entries" in raw
    assert raw["schema_version"] == SERVICE_LEVEL_LOG_SCHEMA_VERSION
