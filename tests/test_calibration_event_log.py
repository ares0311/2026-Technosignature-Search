"""Tests for calibration_event_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.calibration_event_log import (
    ALLOWED_CALIBRATION_EVENT_KINDS,
    ALLOWED_CALIBRATION_EVENT_STATUSES,
    CALIBRATION_EVENT_LOG_DISCLAIMER,
    CALIBRATION_EVENT_LOG_SCHEMA_VERSION,
    calibration_event_log_summary,
    load_calibration_event_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "calibration_event_log.json"


def test_load_entries_returns_five() -> None:
    entries = load_calibration_event_entries()
    assert len(entries) == 5


def test_all_event_kinds_present() -> None:
    entries = load_calibration_event_entries()
    kinds = {e.event_kind for e in entries}
    assert "flux_calibration" in kinds
    assert "bandpass_calibration" in kinds
    assert "phase_calibration" in kinds
    assert "polarization_calibration" in kinds
    assert "pointing_calibration" in kinds


def test_all_statuses_present() -> None:
    entries = load_calibration_event_entries()
    statuses = {e.status for e in entries}
    assert "applied" in statuses
    assert "skipped" in statuses
    assert "deferred" in statuses


def test_summary_entry_count_five() -> None:
    summary = calibration_event_log_summary()
    assert summary["entry_count"] == 5


def test_applied_count_is_three() -> None:
    summary = calibration_event_log_summary()
    assert summary["applied_count"] == 3


def test_failed_count_is_zero() -> None:
    summary = calibration_event_log_summary()
    assert summary["failed_count"] == 0


def test_counts_by_status_covers_present_statuses() -> None:
    summary = calibration_event_log_summary()
    by_status = summary["counts_by_status"]
    assert "applied" in by_status
    assert "skipped" in by_status
    assert "deferred" in by_status


def test_counts_by_kind_covers_all_five() -> None:
    summary = calibration_event_log_summary()
    by_kind = summary["counts_by_kind"]
    for kind in ALLOWED_CALIBRATION_EVENT_KINDS:
        assert kind in by_kind


def test_schema_version() -> None:
    summary = calibration_event_log_summary()
    assert summary["schema_version"] == CALIBRATION_EVENT_LOG_SCHEMA_VERSION


def test_disclaimer_present_and_provenance() -> None:
    summary = calibration_event_log_summary()
    assert "provenance records" in summary["disclaimer"]
    assert summary["disclaimer"] == CALIBRATION_EVENT_LOG_DISCLAIMER


def test_disclaimer_no_detection_language() -> None:
    summary = calibration_event_log_summary()
    assert "detection claim" in summary["disclaimer"]
    assert "discovery" not in summary["disclaimer"].lower()


def test_allowed_event_kinds_has_five_members() -> None:
    assert len(ALLOWED_CALIBRATION_EVENT_KINDS) == 5


def test_allowed_statuses_has_four_members() -> None:
    assert len(ALLOWED_CALIBRATION_EVENT_STATUSES) == 4


def test_fixture_event_kinds_in_allowed() -> None:
    entries = load_calibration_event_entries()
    for e in entries:
        assert e.event_kind in ALLOWED_CALIBRATION_EVENT_KINDS


def test_fixture_status_values_in_allowed() -> None:
    entries = load_calibration_event_entries()
    for e in entries:
        assert e.status in ALLOWED_CALIBRATION_EVENT_STATUSES


def test_source_name_nullable() -> None:
    entries = load_calibration_event_entries()
    cel001 = next(e for e in entries if e.entry_id == "cel-001")
    assert cel001.source_name == "3C286"
    cel004 = next(e for e in entries if e.entry_id == "cel-004")
    assert cel004.source_name is None


def test_as_dict_returns_required_keys() -> None:
    entries = load_calibration_event_entries()
    d = entries[0].as_dict()
    for key in ("entry_id", "run_id", "event_kind", "status",
                "calibrated_by", "calibrated_at", "source_name", "notes"):
        assert key in d


def test_custom_path_argument() -> None:
    entries = load_calibration_event_entries(FIXTURE_PATH)
    assert len(entries) == 5
    summary = calibration_event_log_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_run_ids_cover_two_runs() -> None:
    entries = load_calibration_event_entries()
    run_ids = {e.run_id for e in entries}
    assert len(run_ids) == 2


def test_flux_calibration_count_is_one() -> None:
    summary = calibration_event_log_summary()
    assert summary["counts_by_kind"].get("flux_calibration", 0) == 1
