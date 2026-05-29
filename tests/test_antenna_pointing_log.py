"""Tests for antenna_pointing_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.antenna_pointing_log import (
    ALLOWED_POINTING_KINDS,
    ALLOWED_POINTING_STATUSES,
    ANTENNA_POINTING_LOG_DISCLAIMER,
    ANTENNA_POINTING_LOG_SCHEMA_VERSION,
    AntennaPointingEntry,
    antenna_pointing_summary,
    load_antenna_pointing_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "antenna_pointing_log.json"


def test_schema_version() -> None:
    assert ANTENNA_POINTING_LOG_SCHEMA_VERSION == "antenna_pointing_log_v1"


def test_disclaimer_present() -> None:
    assert "does not authorize external submission" in ANTENNA_POINTING_LOG_DISCLAIMER
    assert "does not constitute a detection claim" in ANTENNA_POINTING_LOG_DISCLAIMER


def test_allowed_pointing_kinds_complete() -> None:
    assert "target_slew" in ALLOWED_POINTING_KINDS
    assert "park_position" in ALLOWED_POINTING_KINDS
    assert "stow_position" in ALLOWED_POINTING_KINDS
    assert "tracking_start" in ALLOWED_POINTING_KINDS
    assert "tracking_end" in ALLOWED_POINTING_KINDS


def test_allowed_statuses_complete() -> None:
    assert "completed" in ALLOWED_POINTING_STATUSES
    assert "failed" in ALLOWED_POINTING_STATUSES
    assert "timeout" in ALLOWED_POINTING_STATUSES
    assert "cancelled" in ALLOWED_POINTING_STATUSES


def test_load_entries_count() -> None:
    entries = load_antenna_pointing_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_load_entries_types() -> None:
    entries = load_antenna_pointing_entries(FIXTURE_PATH)
    for e in entries:
        assert isinstance(e, AntennaPointingEntry)


def test_entry_ids_unique() -> None:
    entries = load_antenna_pointing_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_pointing_kinds_valid() -> None:
    entries = load_antenna_pointing_entries(FIXTURE_PATH)
    for e in entries:
        assert e.pointing_kind in ALLOWED_POINTING_KINDS


def test_statuses_valid() -> None:
    entries = load_antenna_pointing_entries(FIXTURE_PATH)
    for e in entries:
        assert e.status in ALLOWED_POINTING_STATUSES


def test_completed_count() -> None:
    entries = load_antenna_pointing_entries(FIXTURE_PATH)
    completed = [e for e in entries if e.status == "completed"]
    assert len(completed) == 2


def test_failed_count() -> None:
    entries = load_antenna_pointing_entries(FIXTURE_PATH)
    failed = [e for e in entries if e.status == "failed"]
    assert len(failed) == 1


def test_timeout_count() -> None:
    entries = load_antenna_pointing_entries(FIXTURE_PATH)
    timeout = [e for e in entries if e.status == "timeout"]
    assert len(timeout) == 1


def test_cancelled_count() -> None:
    entries = load_antenna_pointing_entries(FIXTURE_PATH)
    cancelled = [e for e in entries if e.status == "cancelled"]
    assert len(cancelled) == 1


def test_entry_as_dict() -> None:
    entries = load_antenna_pointing_entries(FIXTURE_PATH)
    d = entries[0].as_dict()
    assert "entry_id" in d
    assert "pointing_kind" in d
    assert "status" in d


def test_summary_schema_version() -> None:
    summary = antenna_pointing_summary(FIXTURE_PATH)
    assert summary["schema_version"] == ANTENNA_POINTING_LOG_SCHEMA_VERSION


def test_summary_entry_count() -> None:
    summary = antenna_pointing_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_completed_count() -> None:
    summary = antenna_pointing_summary(FIXTURE_PATH)
    assert summary["completed_count"] == 2


def test_summary_failed_count() -> None:
    summary = antenna_pointing_summary(FIXTURE_PATH)
    assert summary["failed_count"] == 1


def test_summary_timeout_count() -> None:
    summary = antenna_pointing_summary(FIXTURE_PATH)
    assert summary["timeout_count"] == 1


def test_summary_cancelled_count() -> None:
    summary = antenna_pointing_summary(FIXTURE_PATH)
    assert summary["cancelled_count"] == 1


def test_summary_counts_by_kind() -> None:
    summary = antenna_pointing_summary(FIXTURE_PATH)
    assert isinstance(summary["counts_by_kind"], dict)
    assert sum(summary["counts_by_kind"].values()) == 5
