"""Tests for instrument_configuration_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.instrument_configuration_log import (
    ALLOWED_CONFIGURATION_KINDS,
    ALLOWED_CONFIGURATION_STATUSES,
    INSTRUMENT_CONFIGURATION_LOG_DISCLAIMER,
    INSTRUMENT_CONFIGURATION_LOG_SCHEMA_VERSION,
    InstrumentConfigurationEntry,
    instrument_configuration_summary,
    load_instrument_configuration_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "instrument_configuration_log.json"


def test_schema_version() -> None:
    assert INSTRUMENT_CONFIGURATION_LOG_SCHEMA_VERSION == "instrument_configuration_log_v1"


def test_disclaimer_present() -> None:
    assert "does not authorize external submission" in INSTRUMENT_CONFIGURATION_LOG_DISCLAIMER
    assert "does not constitute a detection claim" in INSTRUMENT_CONFIGURATION_LOG_DISCLAIMER


def test_allowed_configuration_kinds_complete() -> None:
    assert "frontend_swap" in ALLOWED_CONFIGURATION_KINDS
    assert "backend_change" in ALLOWED_CONFIGURATION_KINDS
    assert "receiver_install" in ALLOWED_CONFIGURATION_KINDS
    assert "filter_change" in ALLOWED_CONFIGURATION_KINDS
    assert "attenuator_set" in ALLOWED_CONFIGURATION_KINDS


def test_allowed_statuses_complete() -> None:
    assert "applied" in ALLOWED_CONFIGURATION_STATUSES
    assert "pending" in ALLOWED_CONFIGURATION_STATUSES
    assert "reverted" in ALLOWED_CONFIGURATION_STATUSES
    assert "failed" in ALLOWED_CONFIGURATION_STATUSES


def test_load_entries_count() -> None:
    entries = load_instrument_configuration_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_load_entries_types() -> None:
    entries = load_instrument_configuration_entries(FIXTURE_PATH)
    for e in entries:
        assert isinstance(e, InstrumentConfigurationEntry)


def test_entry_ids_unique() -> None:
    entries = load_instrument_configuration_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_configuration_kinds_valid() -> None:
    entries = load_instrument_configuration_entries(FIXTURE_PATH)
    for e in entries:
        assert e.configuration_kind in ALLOWED_CONFIGURATION_KINDS


def test_statuses_valid() -> None:
    entries = load_instrument_configuration_entries(FIXTURE_PATH)
    for e in entries:
        assert e.status in ALLOWED_CONFIGURATION_STATUSES


def test_tracks_valid() -> None:
    entries = load_instrument_configuration_entries(FIXTURE_PATH)
    valid_tracks = {"radio", "infrared", "anomaly"}
    for e in entries:
        assert e.track in valid_tracks


def test_applied_count() -> None:
    entries = load_instrument_configuration_entries(FIXTURE_PATH)
    applied = [e for e in entries if e.status == "applied"]
    assert len(applied) == 2


def test_pending_count() -> None:
    entries = load_instrument_configuration_entries(FIXTURE_PATH)
    pending = [e for e in entries if e.status == "pending"]
    assert len(pending) == 1


def test_reverted_count() -> None:
    entries = load_instrument_configuration_entries(FIXTURE_PATH)
    reverted = [e for e in entries if e.status == "reverted"]
    assert len(reverted) == 1


def test_failed_count() -> None:
    entries = load_instrument_configuration_entries(FIXTURE_PATH)
    failed = [e for e in entries if e.status == "failed"]
    assert len(failed) == 1


def test_entry_as_dict() -> None:
    entries = load_instrument_configuration_entries(FIXTURE_PATH)
    d = entries[0].as_dict()
    assert "entry_id" in d
    assert "configuration_kind" in d
    assert "status" in d


def test_summary_schema_version() -> None:
    summary = instrument_configuration_summary(FIXTURE_PATH)
    assert summary["schema_version"] == INSTRUMENT_CONFIGURATION_LOG_SCHEMA_VERSION


def test_summary_entry_count() -> None:
    summary = instrument_configuration_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_applied_count() -> None:
    summary = instrument_configuration_summary(FIXTURE_PATH)
    assert summary["applied_count"] == 2


def test_summary_pending_count() -> None:
    summary = instrument_configuration_summary(FIXTURE_PATH)
    assert summary["pending_count"] == 1


def test_summary_reverted_count() -> None:
    summary = instrument_configuration_summary(FIXTURE_PATH)
    assert summary["reverted_count"] == 1


def test_summary_failed_count() -> None:
    summary = instrument_configuration_summary(FIXTURE_PATH)
    assert summary["failed_count"] == 1


def test_summary_counts_by_kind() -> None:
    summary = instrument_configuration_summary(FIXTURE_PATH)
    assert isinstance(summary["counts_by_kind"], dict)
    assert sum(summary["counts_by_kind"].values()) == 5
