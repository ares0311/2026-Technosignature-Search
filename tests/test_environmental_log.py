"""Tests for environmental_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.environmental_log import (
    ALLOWED_ENVIRONMENT_KINDS,
    ALLOWED_ENVIRONMENT_STATUSES,
    ENVIRONMENTAL_LOG_DISCLAIMER,
    ENVIRONMENTAL_LOG_SCHEMA_VERSION,
    EnvironmentalEntry,
    environmental_log_summary,
    load_environmental_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "environmental_log.json"


def test_schema_version() -> None:
    assert ENVIRONMENTAL_LOG_SCHEMA_VERSION == "environmental_log_v1"


def test_disclaimer_present() -> None:
    assert "does not authorize external submission" in ENVIRONMENTAL_LOG_DISCLAIMER
    assert "does not constitute a detection claim" in ENVIRONMENTAL_LOG_DISCLAIMER


def test_allowed_environment_kinds_complete() -> None:
    assert "temperature_reading" in ALLOWED_ENVIRONMENT_KINDS
    assert "humidity_reading" in ALLOWED_ENVIRONMENT_KINDS
    assert "pressure_reading" in ALLOWED_ENVIRONMENT_KINDS
    assert "vibration_reading" in ALLOWED_ENVIRONMENT_KINDS
    assert "electromagnetic_interference" in ALLOWED_ENVIRONMENT_KINDS


def test_allowed_statuses_complete() -> None:
    assert "nominal" in ALLOWED_ENVIRONMENT_STATUSES
    assert "advisory" in ALLOWED_ENVIRONMENT_STATUSES
    assert "warning" in ALLOWED_ENVIRONMENT_STATUSES
    assert "critical" in ALLOWED_ENVIRONMENT_STATUSES


def test_load_entries_count() -> None:
    entries = load_environmental_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_load_entries_types() -> None:
    entries = load_environmental_entries(FIXTURE_PATH)
    for e in entries:
        assert isinstance(e, EnvironmentalEntry)


def test_entry_ids_unique() -> None:
    entries = load_environmental_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_environment_kinds_valid() -> None:
    entries = load_environmental_entries(FIXTURE_PATH)
    for e in entries:
        assert e.environment_kind in ALLOWED_ENVIRONMENT_KINDS


def test_statuses_valid() -> None:
    entries = load_environmental_entries(FIXTURE_PATH)
    for e in entries:
        assert e.status in ALLOWED_ENVIRONMENT_STATUSES


def test_nominal_count() -> None:
    entries = load_environmental_entries(FIXTURE_PATH)
    nominal = [e for e in entries if e.status == "nominal"]
    assert len(nominal) == 2


def test_advisory_count() -> None:
    entries = load_environmental_entries(FIXTURE_PATH)
    advisory = [e for e in entries if e.status == "advisory"]
    assert len(advisory) == 1


def test_warning_count() -> None:
    entries = load_environmental_entries(FIXTURE_PATH)
    warning = [e for e in entries if e.status == "warning"]
    assert len(warning) == 1


def test_critical_count() -> None:
    entries = load_environmental_entries(FIXTURE_PATH)
    critical = [e for e in entries if e.status == "critical"]
    assert len(critical) == 1


def test_entry_as_dict() -> None:
    entries = load_environmental_entries(FIXTURE_PATH)
    d = entries[0].as_dict()
    assert "entry_id" in d
    assert "environment_kind" in d
    assert "status" in d


def test_summary_schema_version() -> None:
    summary = environmental_log_summary(FIXTURE_PATH)
    assert summary["schema_version"] == ENVIRONMENTAL_LOG_SCHEMA_VERSION


def test_summary_entry_count() -> None:
    summary = environmental_log_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_nominal_count() -> None:
    summary = environmental_log_summary(FIXTURE_PATH)
    assert summary["nominal_count"] == 2


def test_summary_advisory_count() -> None:
    summary = environmental_log_summary(FIXTURE_PATH)
    assert summary["advisory_count"] == 1


def test_summary_warning_count() -> None:
    summary = environmental_log_summary(FIXTURE_PATH)
    assert summary["warning_count"] == 1


def test_summary_critical_count() -> None:
    summary = environmental_log_summary(FIXTURE_PATH)
    assert summary["critical_count"] == 1


def test_summary_counts_by_kind() -> None:
    summary = environmental_log_summary(FIXTURE_PATH)
    assert isinstance(summary["counts_by_kind"], dict)
    assert sum(summary["counts_by_kind"].values()) == 5
