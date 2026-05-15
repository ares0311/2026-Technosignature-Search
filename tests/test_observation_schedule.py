"""Tests for observation schedule schema, loader, summary, and CLI."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

from techno_search.cli import main
from techno_search.observation_schedule import (
    ALLOWED_OBSERVATION_STATUSES,
    OBSERVATION_SCHEDULE_DISCLAIMER,
    OBSERVATION_SCHEDULE_SCHEMA_VERSION,
    load_observation_windows,
    observation_schedule_summary,
)


def test_schedule_fixture_loads():
    windows = load_observation_windows()
    assert len(windows) >= 4


def test_schedule_fixture_all_statuses_valid():
    windows = load_observation_windows()
    for w in windows:
        assert w.status in ALLOWED_OBSERVATION_STATUSES, f"Unknown status: {w.status}"


def test_schedule_fixture_covers_multiple_tracks():
    windows = load_observation_windows()
    tracks = {w.track for w in windows}
    assert len(tracks) >= 2


def test_schedule_fixture_status_variety():
    windows = load_observation_windows()
    statuses = {w.status for w in windows}
    assert "planned" in statuses
    assert "completed" in statuses
    assert "cancelled" in statuses


def test_schedule_summary_window_count():
    summary = observation_schedule_summary()
    assert summary["window_count"] >= 4


def test_schedule_summary_counts_by_status():
    summary = observation_schedule_summary()
    assert summary["planned_count"] >= 1
    assert summary["completed_count"] >= 1
    assert summary["cancelled_count"] >= 1


def test_schedule_summary_disclaimer():
    summary = observation_schedule_summary()
    assert OBSERVATION_SCHEDULE_DISCLAIMER in summary["disclaimer"]


def test_schedule_summary_schema_version():
    summary = observation_schedule_summary()
    assert summary["schema_version"] == OBSERVATION_SCHEDULE_SCHEMA_VERSION


def test_schedule_summary_total_minutes_positive():
    summary = observation_schedule_summary()
    assert summary["total_scheduled_minutes"] > 0


def test_cli_observation_schedule_summary_exit_zero():
    out = StringIO()
    ret = main(["observation-schedule-summary"], stdout=out)
    assert ret == 0
    data = json.loads(out.getvalue())
    assert data["window_count"] >= 4


def test_observation_schedule_schema_in_schema_paths():
    out = StringIO()
    ret = main(["schema-paths"], stdout=out)
    assert ret == 0
    data = json.loads(out.getvalue())
    assert "observation_schedule" in data


def test_observation_schedule_schema_file_exists():
    schema_path = (
        Path(__file__).resolve().parents[1] / "schemas" / "observation_schedule.schema.json"
    )
    assert schema_path.exists()
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema.get("title") == "ObservationSchedule"
    required = schema.get("required", [])
    for field in ("schema_version", "disclaimer", "windows"):
        assert field in required
