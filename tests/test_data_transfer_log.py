"""Tests for data_transfer_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.data_transfer_log import (
    ALLOWED_DATA_TRANSFER_KINDS,
    ALLOWED_DATA_TRANSFER_STATUSES,
    DATA_TRANSFER_LOG_DISCLAIMER,
    DATA_TRANSFER_LOG_SCHEMA_VERSION,
    DataTransferEntry,
    data_transfer_summary,
    load_data_transfer_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "data_transfer_log.json"


def test_schema_version() -> None:
    assert DATA_TRANSFER_LOG_SCHEMA_VERSION == "data_transfer_log_v1"


def test_disclaimer_present() -> None:
    assert "does not authorize external submission" in DATA_TRANSFER_LOG_DISCLAIMER
    assert "does not constitute a detection claim" in DATA_TRANSFER_LOG_DISCLAIMER


def test_allowed_transfer_kinds_complete() -> None:
    assert "archive_transfer" in ALLOWED_DATA_TRANSFER_KINDS
    assert "inter_site_transfer" in ALLOWED_DATA_TRANSFER_KINDS
    assert "local_copy" in ALLOWED_DATA_TRANSFER_KINDS
    assert "cloud_upload" in ALLOWED_DATA_TRANSFER_KINDS
    assert "network_delivery" in ALLOWED_DATA_TRANSFER_KINDS


def test_allowed_statuses_complete() -> None:
    assert "pending" in ALLOWED_DATA_TRANSFER_STATUSES
    assert "completed" in ALLOWED_DATA_TRANSFER_STATUSES
    assert "failed" in ALLOWED_DATA_TRANSFER_STATUSES
    assert "verified" in ALLOWED_DATA_TRANSFER_STATUSES


def test_load_data_transfer_entries_count() -> None:
    entries = load_data_transfer_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_load_data_transfer_entries_types() -> None:
    entries = load_data_transfer_entries(FIXTURE_PATH)
    for e in entries:
        assert isinstance(e, DataTransferEntry)


def test_entry_ids_unique() -> None:
    entries = load_data_transfer_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_transfer_kinds_valid() -> None:
    entries = load_data_transfer_entries(FIXTURE_PATH)
    for e in entries:
        assert e.transfer_kind in ALLOWED_DATA_TRANSFER_KINDS


def test_statuses_valid() -> None:
    entries = load_data_transfer_entries(FIXTURE_PATH)
    for e in entries:
        assert e.status in ALLOWED_DATA_TRANSFER_STATUSES


def test_tracks_valid() -> None:
    entries = load_data_transfer_entries(FIXTURE_PATH)
    valid_tracks = {"radio", "infrared", "anomaly"}
    for e in entries:
        assert e.track in valid_tracks


def test_completed_count() -> None:
    entries = load_data_transfer_entries(FIXTURE_PATH)
    completed = [e for e in entries if e.status == "completed"]
    assert len(completed) == 2


def test_pending_count() -> None:
    entries = load_data_transfer_entries(FIXTURE_PATH)
    pending = [e for e in entries if e.status == "pending"]
    assert len(pending) == 1


def test_failed_count() -> None:
    entries = load_data_transfer_entries(FIXTURE_PATH)
    failed = [e for e in entries if e.status == "failed"]
    assert len(failed) == 1


def test_verified_count() -> None:
    entries = load_data_transfer_entries(FIXTURE_PATH)
    verified = [e for e in entries if e.status == "verified"]
    assert len(verified) == 1


def test_entry_as_dict() -> None:
    entries = load_data_transfer_entries(FIXTURE_PATH)
    d = entries[0].as_dict()
    assert "entry_id" in d
    assert "transfer_kind" in d
    assert "status" in d


def test_summary_schema_version() -> None:
    summary = data_transfer_summary(FIXTURE_PATH)
    assert summary["schema_version"] == DATA_TRANSFER_LOG_SCHEMA_VERSION


def test_summary_entry_count() -> None:
    summary = data_transfer_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_completed_count() -> None:
    summary = data_transfer_summary(FIXTURE_PATH)
    assert summary["completed_count"] == 2


def test_summary_pending_count() -> None:
    summary = data_transfer_summary(FIXTURE_PATH)
    assert summary["pending_count"] == 1


def test_summary_failed_count() -> None:
    summary = data_transfer_summary(FIXTURE_PATH)
    assert summary["failed_count"] == 1


def test_summary_verified_count() -> None:
    summary = data_transfer_summary(FIXTURE_PATH)
    assert summary["verified_count"] == 1


def test_summary_counts_by_kind() -> None:
    summary = data_transfer_summary(FIXTURE_PATH)
    assert isinstance(summary["counts_by_kind"], dict)
    assert sum(summary["counts_by_kind"].values()) == 5


def test_summary_disclaimer() -> None:
    summary = data_transfer_summary(FIXTURE_PATH)
    assert "does not authorize external submission" in summary["disclaimer"]
