"""Tests for network_connectivity_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.network_connectivity_log import (
    ALLOWED_NETWORK_KINDS,
    ALLOWED_NETWORK_STATUSES,
    NETWORK_CONNECTIVITY_LOG_DISCLAIMER,
    NETWORK_CONNECTIVITY_LOG_SCHEMA_VERSION,
    NetworkConnectivityEntry,
    load_network_connectivity_entries,
    network_connectivity_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "network_connectivity_log.json"


def test_schema_version() -> None:
    assert NETWORK_CONNECTIVITY_LOG_SCHEMA_VERSION == "network_connectivity_log_v1"


def test_disclaimer_present() -> None:
    assert "does not authorize external submission" in NETWORK_CONNECTIVITY_LOG_DISCLAIMER
    assert "does not constitute a detection claim" in NETWORK_CONNECTIVITY_LOG_DISCLAIMER


def test_allowed_network_kinds_complete() -> None:
    assert "link_up" in ALLOWED_NETWORK_KINDS
    assert "link_down" in ALLOWED_NETWORK_KINDS
    assert "latency_spike" in ALLOWED_NETWORK_KINDS
    assert "packet_loss" in ALLOWED_NETWORK_KINDS
    assert "vpn_event" in ALLOWED_NETWORK_KINDS


def test_allowed_statuses_complete() -> None:
    assert "connected" in ALLOWED_NETWORK_STATUSES
    assert "degraded" in ALLOWED_NETWORK_STATUSES
    assert "disconnected" in ALLOWED_NETWORK_STATUSES
    assert "restored" in ALLOWED_NETWORK_STATUSES


def test_load_entries_count() -> None:
    entries = load_network_connectivity_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_load_entries_types() -> None:
    entries = load_network_connectivity_entries(FIXTURE_PATH)
    for e in entries:
        assert isinstance(e, NetworkConnectivityEntry)


def test_entry_ids_unique() -> None:
    entries = load_network_connectivity_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_network_kinds_valid() -> None:
    entries = load_network_connectivity_entries(FIXTURE_PATH)
    for e in entries:
        assert e.network_kind in ALLOWED_NETWORK_KINDS


def test_statuses_valid() -> None:
    entries = load_network_connectivity_entries(FIXTURE_PATH)
    for e in entries:
        assert e.status in ALLOWED_NETWORK_STATUSES


def test_connected_count() -> None:
    entries = load_network_connectivity_entries(FIXTURE_PATH)
    connected = [e for e in entries if e.status == "connected"]
    assert len(connected) == 2


def test_degraded_count() -> None:
    entries = load_network_connectivity_entries(FIXTURE_PATH)
    degraded = [e for e in entries if e.status == "degraded"]
    assert len(degraded) == 1


def test_disconnected_count() -> None:
    entries = load_network_connectivity_entries(FIXTURE_PATH)
    disconnected = [e for e in entries if e.status == "disconnected"]
    assert len(disconnected) == 1


def test_restored_count() -> None:
    entries = load_network_connectivity_entries(FIXTURE_PATH)
    restored = [e for e in entries if e.status == "restored"]
    assert len(restored) == 1


def test_entry_as_dict() -> None:
    entries = load_network_connectivity_entries(FIXTURE_PATH)
    d = entries[0].as_dict()
    assert "entry_id" in d
    assert "network_kind" in d
    assert "status" in d


def test_summary_schema_version() -> None:
    summary = network_connectivity_summary(FIXTURE_PATH)
    assert summary["schema_version"] == NETWORK_CONNECTIVITY_LOG_SCHEMA_VERSION


def test_summary_entry_count() -> None:
    summary = network_connectivity_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_connected_count() -> None:
    summary = network_connectivity_summary(FIXTURE_PATH)
    assert summary["connected_count"] == 2


def test_summary_degraded_count() -> None:
    summary = network_connectivity_summary(FIXTURE_PATH)
    assert summary["degraded_count"] == 1


def test_summary_disconnected_count() -> None:
    summary = network_connectivity_summary(FIXTURE_PATH)
    assert summary["disconnected_count"] == 1


def test_summary_restored_count() -> None:
    summary = network_connectivity_summary(FIXTURE_PATH)
    assert summary["restored_count"] == 1


def test_summary_counts_by_kind() -> None:
    summary = network_connectivity_summary(FIXTURE_PATH)
    assert isinstance(summary["counts_by_kind"], dict)
    assert sum(summary["counts_by_kind"].values()) == 5
