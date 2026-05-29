"""Tests for weather_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.weather_log import (
    ALLOWED_WEATHER_KINDS,
    ALLOWED_WEATHER_STATUSES,
    WEATHER_LOG_DISCLAIMER,
    WEATHER_LOG_SCHEMA_VERSION,
    WeatherEntry,
    load_weather_entries,
    weather_log_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "weather_log.json"


def test_schema_version() -> None:
    assert WEATHER_LOG_SCHEMA_VERSION == "weather_log_v1"


def test_disclaimer_present() -> None:
    assert "does not authorize external submission" in WEATHER_LOG_DISCLAIMER
    assert "does not constitute a detection claim" in WEATHER_LOG_DISCLAIMER


def test_allowed_weather_kinds_complete() -> None:
    assert "wind_speed" in ALLOWED_WEATHER_KINDS
    assert "temperature" in ALLOWED_WEATHER_KINDS
    assert "humidity" in ALLOWED_WEATHER_KINDS
    assert "precipitation" in ALLOWED_WEATHER_KINDS
    assert "seeing" in ALLOWED_WEATHER_KINDS


def test_allowed_statuses_complete() -> None:
    assert "nominal" in ALLOWED_WEATHER_STATUSES
    assert "advisory" in ALLOWED_WEATHER_STATUSES
    assert "warning" in ALLOWED_WEATHER_STATUSES
    assert "observation_hold" in ALLOWED_WEATHER_STATUSES


def test_load_entries_count() -> None:
    entries = load_weather_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_load_entries_types() -> None:
    entries = load_weather_entries(FIXTURE_PATH)
    for e in entries:
        assert isinstance(e, WeatherEntry)


def test_entry_ids_unique() -> None:
    entries = load_weather_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_weather_kinds_valid() -> None:
    entries = load_weather_entries(FIXTURE_PATH)
    for e in entries:
        assert e.weather_kind in ALLOWED_WEATHER_KINDS


def test_statuses_valid() -> None:
    entries = load_weather_entries(FIXTURE_PATH)
    for e in entries:
        assert e.status in ALLOWED_WEATHER_STATUSES


def test_nominal_count() -> None:
    entries = load_weather_entries(FIXTURE_PATH)
    nominal = [e for e in entries if e.status == "nominal"]
    assert len(nominal) == 2


def test_advisory_count() -> None:
    entries = load_weather_entries(FIXTURE_PATH)
    advisory = [e for e in entries if e.status == "advisory"]
    assert len(advisory) == 1


def test_warning_count() -> None:
    entries = load_weather_entries(FIXTURE_PATH)
    warning = [e for e in entries if e.status == "warning"]
    assert len(warning) == 1


def test_observation_hold_count() -> None:
    entries = load_weather_entries(FIXTURE_PATH)
    hold = [e for e in entries if e.status == "observation_hold"]
    assert len(hold) == 1


def test_entry_as_dict() -> None:
    entries = load_weather_entries(FIXTURE_PATH)
    d = entries[0].as_dict()
    assert "entry_id" in d
    assert "weather_kind" in d
    assert "status" in d


def test_summary_schema_version() -> None:
    summary = weather_log_summary(FIXTURE_PATH)
    assert summary["schema_version"] == WEATHER_LOG_SCHEMA_VERSION


def test_summary_entry_count() -> None:
    summary = weather_log_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_nominal_count() -> None:
    summary = weather_log_summary(FIXTURE_PATH)
    assert summary["nominal_count"] == 2


def test_summary_advisory_count() -> None:
    summary = weather_log_summary(FIXTURE_PATH)
    assert summary["advisory_count"] == 1


def test_summary_warning_count() -> None:
    summary = weather_log_summary(FIXTURE_PATH)
    assert summary["warning_count"] == 1


def test_summary_observation_hold_count() -> None:
    summary = weather_log_summary(FIXTURE_PATH)
    assert summary["observation_hold_count"] == 1


def test_summary_counts_by_kind() -> None:
    summary = weather_log_summary(FIXTURE_PATH)
    assert isinstance(summary["counts_by_kind"], dict)
    assert sum(summary["counts_by_kind"].values()) == 5
