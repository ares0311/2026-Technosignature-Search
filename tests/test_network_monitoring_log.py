from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.network_monitoring_log import (
    ALLOWED_NETWORK_MONITORING_KINDS,
    ALLOWED_NETWORK_MONITORING_STATUSES,
    NETWORK_MONITORING_LOG_DISCLAIMER,
    NETWORK_MONITORING_LOG_SCHEMA_VERSION,
    NetworkMonitoringEntry,
    load_network_monitoring_entries,
    network_monitoring_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "network_monitoring_log.json"


def test_allowed_kinds_not_empty() -> None:
    assert len(ALLOWED_NETWORK_MONITORING_KINDS) > 0


def test_allowed_statuses_not_empty() -> None:
    assert len(ALLOWED_NETWORK_MONITORING_STATUSES) > 0


def test_expected_kinds_present() -> None:
    assert "bandwidth_check" in ALLOWED_NETWORK_MONITORING_KINDS
    assert "connectivity_check" in ALLOWED_NETWORK_MONITORING_KINDS
    assert "latency_probe" in ALLOWED_NETWORK_MONITORING_KINDS
    assert "packet_loss_check" in ALLOWED_NETWORK_MONITORING_KINDS
    assert "routing_check" in ALLOWED_NETWORK_MONITORING_KINDS


def test_expected_statuses_present() -> None:
    assert "alert" in ALLOWED_NETWORK_MONITORING_STATUSES
    assert "degraded" in ALLOWED_NETWORK_MONITORING_STATUSES
    assert "healthy" in ALLOWED_NETWORK_MONITORING_STATUSES
    assert "unreachable" in ALLOWED_NETWORK_MONITORING_STATUSES


def test_schema_version_string() -> None:
    assert isinstance(NETWORK_MONITORING_LOG_SCHEMA_VERSION, str)
    assert len(NETWORK_MONITORING_LOG_SCHEMA_VERSION) > 0


def test_disclaimer_string() -> None:
    assert isinstance(NETWORK_MONITORING_LOG_DISCLAIMER, str)
    assert "does not" in NETWORK_MONITORING_LOG_DISCLAIMER


def test_entry_valid_construction() -> None:
    entry = NetworkMonitoringEntry(
        entry_id="nm-test-001",
        network_kind="connectivity_check",
        status="healthy",
        actor_id="operator-x",
        resource_id="pipeline-v1",
        timestamp_utc="2026-06-01T00:00:00Z",
        notes=None,
    )
    assert entry.entry_id == "nm-test-001"
    assert entry.network_kind == "connectivity_check"
    assert entry.status == "healthy"


def test_entry_invalid_kind_raises() -> None:
    with pytest.raises(ValueError, match="network_kind"):
        NetworkMonitoringEntry(
            entry_id="nm-bad",
            network_kind="unknown_kind",
            status="healthy",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-06-01T00:00:00Z",
            notes=None,
        )


def test_entry_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="status"):
        NetworkMonitoringEntry(
            entry_id="nm-bad",
            network_kind="latency_probe",
            status="unknown_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-06-01T00:00:00Z",
            notes=None,
        )


def test_load_fixture_returns_entries() -> None:
    entries = load_network_monitoring_entries(FIXTURE_PATH)
    assert len(entries) >= 1


def test_fixture_has_expected_count() -> None:
    entries = load_network_monitoring_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_has_healthy_entries() -> None:
    entries = load_network_monitoring_entries(FIXTURE_PATH)
    healthy = [e for e in entries if e.status == "healthy"]
    assert len(healthy) >= 1


def test_fixture_covers_multiple_kinds() -> None:
    entries = load_network_monitoring_entries(FIXTURE_PATH)
    kinds = {e.network_kind for e in entries}
    assert len(kinds) >= 3


def test_summary_schema_version() -> None:
    summary = network_monitoring_summary(FIXTURE_PATH)
    assert summary["schema_version"] == NETWORK_MONITORING_LOG_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    summary = network_monitoring_summary(FIXTURE_PATH)
    assert "does not" in summary["disclaimer"]


def test_summary_entry_count() -> None:
    summary = network_monitoring_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_healthy_count() -> None:
    summary = network_monitoring_summary(FIXTURE_PATH)
    assert summary["healthy_count"] >= 1


def test_summary_by_kind() -> None:
    summary = network_monitoring_summary(FIXTURE_PATH)
    assert isinstance(summary["by_kind"], dict)
    assert len(summary["by_kind"]) >= 1


def test_summary_by_status() -> None:
    summary = network_monitoring_summary(FIXTURE_PATH)
    assert isinstance(summary["by_status"], dict)
    assert "healthy" in summary["by_status"]


def test_fixture_json_parseable() -> None:
    raw = json.loads(FIXTURE_PATH.read_text())
    assert "entries" in raw
    assert raw["schema_version"] == NETWORK_MONITORING_LOG_SCHEMA_VERSION


def test_entry_has_resource_id() -> None:
    entries = load_network_monitoring_entries(FIXTURE_PATH)
    for entry in entries:
        assert isinstance(entry.resource_id, str)
        assert len(entry.resource_id) > 0


def test_load_returns_network_monitoring_entry_instances() -> None:
    entries = load_network_monitoring_entries(FIXTURE_PATH)
    for entry in entries:
        assert isinstance(entry, NetworkMonitoringEntry)
