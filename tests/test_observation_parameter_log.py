"""Tests for observation_parameter_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.observation_parameter_log import (
    ALLOWED_PARAMETER_KINDS,
    ALLOWED_PARAMETER_STATUSES,
    OBSERVATION_PARAMETER_LOG_DISCLAIMER,
    OBSERVATION_PARAMETER_LOG_SCHEMA_VERSION,
    load_observation_parameter_entries,
    observation_parameter_log_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "observation_parameter_log.json"


def test_load_entries_returns_five() -> None:
    entries = load_observation_parameter_entries()
    assert len(entries) == 5


def test_all_parameter_kinds_present() -> None:
    entries = load_observation_parameter_entries()
    kinds = {e.parameter_kind for e in entries}
    assert "integration_time" in kinds
    assert "bandwidth" in kinds
    assert "center_frequency" in kinds
    assert "resolution" in kinds
    assert "sensitivity_target" in kinds


def test_all_statuses_present() -> None:
    entries = load_observation_parameter_entries()
    statuses = {e.status for e in entries}
    assert "applied" in statuses
    assert "overridden" in statuses
    assert "flagged" in statuses
    assert "failed" in statuses


def test_summary_entry_count_five() -> None:
    summary = observation_parameter_log_summary()
    assert summary["entry_count"] == 5


def test_applied_count_is_two() -> None:
    summary = observation_parameter_log_summary()
    assert summary["applied_count"] == 2


def test_flagged_count_is_one() -> None:
    summary = observation_parameter_log_summary()
    assert summary["flagged_count"] == 1


def test_counts_by_status_covers_all_four() -> None:
    summary = observation_parameter_log_summary()
    by_status = summary["counts_by_status"]
    assert set(by_status.keys()) == {"applied", "overridden", "flagged", "failed"}


def test_counts_by_kind_covers_all_five() -> None:
    summary = observation_parameter_log_summary()
    by_kind = summary["counts_by_kind"]
    for kind in ALLOWED_PARAMETER_KINDS:
        assert kind in by_kind


def test_schema_version() -> None:
    summary = observation_parameter_log_summary()
    assert summary["schema_version"] == OBSERVATION_PARAMETER_LOG_SCHEMA_VERSION


def test_disclaimer_present_and_provenance() -> None:
    summary = observation_parameter_log_summary()
    assert "provenance records" in summary["disclaimer"]
    assert summary["disclaimer"] == OBSERVATION_PARAMETER_LOG_DISCLAIMER


def test_disclaimer_no_detection_language() -> None:
    summary = observation_parameter_log_summary()
    assert "detection claim" in summary["disclaimer"]
    assert "discovery" not in summary["disclaimer"].lower()


def test_allowed_parameter_kinds_has_five_members() -> None:
    assert len(ALLOWED_PARAMETER_KINDS) == 5


def test_allowed_parameter_statuses_has_four_members() -> None:
    assert len(ALLOWED_PARAMETER_STATUSES) == 4


def test_fixture_parameter_kinds_in_allowed() -> None:
    entries = load_observation_parameter_entries()
    for e in entries:
        assert e.parameter_kind in ALLOWED_PARAMETER_KINDS


def test_fixture_status_values_in_allowed() -> None:
    entries = load_observation_parameter_entries()
    for e in entries:
        assert e.status in ALLOWED_PARAMETER_STATUSES


def test_value_and_unit_nullable() -> None:
    entries = load_observation_parameter_entries()
    opl001 = next(e for e in entries if e.entry_id == "opl-001")
    assert opl001.value == 300.0
    assert opl001.unit == "s"
    opl004 = next(e for e in entries if e.entry_id == "opl-004")
    assert opl004.value is None
    assert opl004.unit is None


def test_as_dict_returns_required_keys() -> None:
    entries = load_observation_parameter_entries()
    d = entries[0].as_dict()
    for key in ("entry_id", "run_id", "parameter_kind", "status",
                "set_by", "set_at", "value", "unit", "notes"):
        assert key in d


def test_custom_path_argument() -> None:
    entries = load_observation_parameter_entries(FIXTURE_PATH)
    assert len(entries) == 5
    summary = observation_parameter_log_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_run_ids_cover_two_runs() -> None:
    entries = load_observation_parameter_entries()
    run_ids = {e.run_id for e in entries}
    assert len(run_ids) == 2


def test_integration_time_count_is_one() -> None:
    summary = observation_parameter_log_summary()
    assert summary["counts_by_kind"].get("integration_time", 0) == 1
