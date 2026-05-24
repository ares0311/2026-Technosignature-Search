"""Tests for noise_measurement_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.noise_measurement_log import (
    ALLOWED_MEASUREMENT_KINDS,
    ALLOWED_MEASUREMENT_STATUSES,
    NOISE_MEASUREMENT_LOG_DISCLAIMER,
    NOISE_MEASUREMENT_LOG_SCHEMA_VERSION,
    load_noise_measurement_entries,
    noise_measurement_log_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "noise_measurement_log.json"


def test_load_entries_returns_five() -> None:
    entries = load_noise_measurement_entries()
    assert len(entries) == 5


def test_all_measurement_kinds_present() -> None:
    entries = load_noise_measurement_entries()
    kinds = {e.measurement_kind for e in entries}
    assert "system_temperature" in kinds
    assert "noise_floor" in kinds
    assert "rms_baseline" in kinds
    assert "sensitivity_estimate" in kinds
    assert "interference_level" in kinds


def test_all_statuses_present() -> None:
    entries = load_noise_measurement_entries()
    statuses = {e.status for e in entries}
    assert "recorded" in statuses
    assert "flagged" in statuses
    assert "superseded" in statuses
    assert "failed" in statuses


def test_summary_entry_count_five() -> None:
    summary = noise_measurement_log_summary()
    assert summary["entry_count"] == 5


def test_recorded_count_is_two() -> None:
    summary = noise_measurement_log_summary()
    assert summary["recorded_count"] == 2


def test_flagged_count_is_one() -> None:
    summary = noise_measurement_log_summary()
    assert summary["flagged_count"] == 1


def test_counts_by_status_covers_all_four() -> None:
    summary = noise_measurement_log_summary()
    by_status = summary["counts_by_status"]
    assert set(by_status.keys()) == {"recorded", "flagged", "superseded", "failed"}


def test_counts_by_kind_covers_all_five() -> None:
    summary = noise_measurement_log_summary()
    by_kind = summary["counts_by_kind"]
    for kind in ALLOWED_MEASUREMENT_KINDS:
        assert kind in by_kind


def test_schema_version() -> None:
    summary = noise_measurement_log_summary()
    assert summary["schema_version"] == NOISE_MEASUREMENT_LOG_SCHEMA_VERSION


def test_disclaimer_present_and_provenance() -> None:
    summary = noise_measurement_log_summary()
    assert "provenance records" in summary["disclaimer"]
    assert summary["disclaimer"] == NOISE_MEASUREMENT_LOG_DISCLAIMER


def test_disclaimer_no_detection_language() -> None:
    summary = noise_measurement_log_summary()
    assert "detection claim" in summary["disclaimer"]
    assert "discovery" not in summary["disclaimer"].lower()


def test_allowed_measurement_kinds_has_five_members() -> None:
    assert len(ALLOWED_MEASUREMENT_KINDS) == 5


def test_allowed_measurement_statuses_has_four_members() -> None:
    assert len(ALLOWED_MEASUREMENT_STATUSES) == 4


def test_fixture_measurement_kinds_in_allowed() -> None:
    entries = load_noise_measurement_entries()
    for e in entries:
        assert e.measurement_kind in ALLOWED_MEASUREMENT_KINDS


def test_fixture_status_values_in_allowed() -> None:
    entries = load_noise_measurement_entries()
    for e in entries:
        assert e.status in ALLOWED_MEASUREMENT_STATUSES


def test_value_and_unit_nullable() -> None:
    entries = load_noise_measurement_entries()
    nml001 = next(e for e in entries if e.entry_id == "nml-001")
    assert nml001.value == 25.0
    assert nml001.unit == "K"
    nml004 = next(e for e in entries if e.entry_id == "nml-004")
    assert nml004.value is None
    assert nml004.unit is None


def test_as_dict_returns_required_keys() -> None:
    entries = load_noise_measurement_entries()
    d = entries[0].as_dict()
    for key in ("entry_id", "run_id", "measurement_kind", "status",
                "measured_by", "measured_at", "value", "unit", "notes"):
        assert key in d


def test_custom_path_argument() -> None:
    entries = load_noise_measurement_entries(FIXTURE_PATH)
    assert len(entries) == 5
    summary = noise_measurement_log_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_run_ids_cover_two_runs() -> None:
    entries = load_noise_measurement_entries()
    run_ids = {e.run_id for e in entries}
    assert len(run_ids) == 2


def test_system_temperature_count_is_one() -> None:
    summary = noise_measurement_log_summary()
    assert summary["counts_by_kind"].get("system_temperature", 0) == 1
