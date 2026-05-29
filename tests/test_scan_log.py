"""Tests for scan_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.scan_log import (
    ALLOWED_SCAN_KINDS,
    ALLOWED_SCAN_STATUSES,
    SCAN_LOG_DISCLAIMER,
    SCAN_LOG_SCHEMA_VERSION,
    ScanEntry,
    load_scan_entries,
    scan_log_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "scan_log.json"


def test_schema_version() -> None:
    assert SCAN_LOG_SCHEMA_VERSION == "scan_log_v1"


def test_disclaimer_present() -> None:
    assert "does not authorize external submission" in SCAN_LOG_DISCLAIMER
    assert "does not constitute a detection claim" in SCAN_LOG_DISCLAIMER


def test_allowed_scan_kinds_complete() -> None:
    assert "on_source" in ALLOWED_SCAN_KINDS
    assert "off_source" in ALLOWED_SCAN_KINDS
    assert "calibrator" in ALLOWED_SCAN_KINDS
    assert "reference_position" in ALLOWED_SCAN_KINDS
    assert "slew" in ALLOWED_SCAN_KINDS


def test_allowed_statuses_complete() -> None:
    assert "completed" in ALLOWED_SCAN_STATUSES
    assert "aborted" in ALLOWED_SCAN_STATUSES
    assert "flagged" in ALLOWED_SCAN_STATUSES
    assert "pending" in ALLOWED_SCAN_STATUSES


def test_load_entries_count() -> None:
    entries = load_scan_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_load_entries_types() -> None:
    entries = load_scan_entries(FIXTURE_PATH)
    for e in entries:
        assert isinstance(e, ScanEntry)


def test_entry_ids_unique() -> None:
    entries = load_scan_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_scan_kinds_valid() -> None:
    entries = load_scan_entries(FIXTURE_PATH)
    for e in entries:
        assert e.scan_kind in ALLOWED_SCAN_KINDS


def test_statuses_valid() -> None:
    entries = load_scan_entries(FIXTURE_PATH)
    for e in entries:
        assert e.status in ALLOWED_SCAN_STATUSES


def test_tracks_valid() -> None:
    entries = load_scan_entries(FIXTURE_PATH)
    valid_tracks = {"radio", "infrared", "anomaly"}
    for e in entries:
        assert e.track in valid_tracks


def test_completed_count() -> None:
    entries = load_scan_entries(FIXTURE_PATH)
    completed = [e for e in entries if e.status == "completed"]
    assert len(completed) == 2


def test_aborted_count() -> None:
    entries = load_scan_entries(FIXTURE_PATH)
    aborted = [e for e in entries if e.status == "aborted"]
    assert len(aborted) == 1


def test_flagged_count() -> None:
    entries = load_scan_entries(FIXTURE_PATH)
    flagged = [e for e in entries if e.status == "flagged"]
    assert len(flagged) == 1


def test_pending_count() -> None:
    entries = load_scan_entries(FIXTURE_PATH)
    pending = [e for e in entries if e.status == "pending"]
    assert len(pending) == 1


def test_entry_as_dict() -> None:
    entries = load_scan_entries(FIXTURE_PATH)
    d = entries[0].as_dict()
    assert "entry_id" in d
    assert "scan_kind" in d
    assert "status" in d


def test_summary_schema_version() -> None:
    summary = scan_log_summary(FIXTURE_PATH)
    assert summary["schema_version"] == SCAN_LOG_SCHEMA_VERSION


def test_summary_entry_count() -> None:
    summary = scan_log_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_completed_count() -> None:
    summary = scan_log_summary(FIXTURE_PATH)
    assert summary["completed_count"] == 2


def test_summary_aborted_count() -> None:
    summary = scan_log_summary(FIXTURE_PATH)
    assert summary["aborted_count"] == 1


def test_summary_flagged_count() -> None:
    summary = scan_log_summary(FIXTURE_PATH)
    assert summary["flagged_count"] == 1


def test_summary_pending_count() -> None:
    summary = scan_log_summary(FIXTURE_PATH)
    assert summary["pending_count"] == 1


def test_summary_counts_by_kind() -> None:
    summary = scan_log_summary(FIXTURE_PATH)
    assert isinstance(summary["counts_by_kind"], dict)
    assert sum(summary["counts_by_kind"].values()) == 5
