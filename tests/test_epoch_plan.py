"""Tests for epoch_plan module."""

from __future__ import annotations

import json
from io import StringIO

from techno_search.cli import main
from techno_search.epoch_plan import (
    ALLOWED_EPOCH_PLAN_STATUSES,
    ALLOWED_EPOCH_PRIORITIES,
    EPOCH_PLAN_DISCLAIMER,
    EPOCH_PLAN_SCHEMA_VERSION,
    EpochPlanEntry,
    epoch_plan_summary,
    load_epoch_plan,
)


def test_load_epoch_plan_returns_list():
    entries = load_epoch_plan()
    assert isinstance(entries, list)
    assert len(entries) >= 1


def test_epoch_plan_entries_are_dataclass_instances():
    entries = load_epoch_plan()
    for entry in entries:
        assert isinstance(entry, EpochPlanEntry)
        assert isinstance(entry.entry_id, str)
        assert isinstance(entry.target_id, str)
        assert isinstance(entry.track, str)
        assert isinstance(entry.current_epoch_count, int)
        assert isinstance(entry.requested_additional_epochs, int)
        assert isinstance(entry.rationale, str)
        assert isinstance(entry.status, str)
        assert isinstance(entry.priority, str)
        assert isinstance(entry.created_utc, str)
        assert isinstance(entry.blocking_reasons, list)


def test_epoch_plan_statuses_are_allowed():
    entries = load_epoch_plan()
    for entry in entries:
        assert entry.status in ALLOWED_EPOCH_PLAN_STATUSES, (
            f"Unexpected status: {entry.status}"
        )


def test_epoch_plan_priorities_are_allowed():
    entries = load_epoch_plan()
    for entry in entries:
        assert entry.priority in ALLOWED_EPOCH_PRIORITIES, (
            f"Unexpected priority: {entry.priority}"
        )


def test_epoch_plan_covers_multiple_tracks():
    entries = load_epoch_plan()
    tracks = {e.track for e in entries}
    assert len(tracks) >= 2


def test_epoch_plan_fixture_has_five():
    entries = load_epoch_plan()
    assert len(entries) == 5


def test_epoch_plan_entry_as_dict():
    entries = load_epoch_plan()
    d = entries[0].as_dict()
    for key in (
        "entry_id", "target_id", "track", "current_epoch_count",
        "requested_additional_epochs", "rationale", "status",
        "priority", "created_utc", "blocking_reasons",
    ):
        assert key in d


def test_epoch_plan_summary_schema_version():
    summary = epoch_plan_summary()
    assert summary["schema_version"] == EPOCH_PLAN_SCHEMA_VERSION


def test_epoch_plan_summary_disclaimer():
    summary = epoch_plan_summary()
    assert EPOCH_PLAN_DISCLAIMER in summary["disclaimer"]


def test_epoch_plan_summary_entry_count():
    summary = epoch_plan_summary()
    assert summary["entry_count"] == 5


def test_epoch_plan_summary_by_track():
    summary = epoch_plan_summary()
    assert isinstance(summary["by_track"], dict)
    assert len(summary["by_track"]) >= 2


def test_epoch_plan_summary_by_status():
    summary = epoch_plan_summary()
    assert isinstance(summary["by_status"], dict)
    assert len(summary["by_status"]) >= 2


def test_epoch_plan_summary_by_priority():
    summary = epoch_plan_summary()
    assert isinstance(summary["by_priority"], dict)
    assert len(summary["by_priority"]) >= 2


def test_epoch_plan_summary_pending_count():
    summary = epoch_plan_summary()
    assert isinstance(summary["pending_count"], int)
    assert summary["pending_count"] >= 1


def test_epoch_plan_summary_total_additional_epochs():
    summary = epoch_plan_summary()
    assert isinstance(summary["total_additional_epochs_requested"], int)
    assert summary["total_additional_epochs_requested"] >= 0


def test_epoch_plan_summary_blocked_count():
    summary = epoch_plan_summary()
    assert isinstance(summary["blocked_count"], int)
    assert summary["blocked_count"] >= 0


def test_allowed_epoch_plan_statuses():
    assert "pending" in ALLOWED_EPOCH_PLAN_STATUSES
    assert "scheduled" in ALLOWED_EPOCH_PLAN_STATUSES
    assert "completed" in ALLOWED_EPOCH_PLAN_STATUSES


def test_allowed_epoch_priorities():
    assert "high" in ALLOWED_EPOCH_PRIORITIES
    assert "medium" in ALLOWED_EPOCH_PRIORITIES
    assert "low" in ALLOWED_EPOCH_PRIORITIES


def test_cli_epoch_plan_summary_exits_zero():
    stdout = StringIO()
    exit_code = main(["epoch-plan-summary"], stdout=stdout)
    assert exit_code == 0


def test_cli_epoch_plan_summary_outputs_json():
    stdout = StringIO()
    main(["epoch-plan-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())
    assert result["schema_version"] == EPOCH_PLAN_SCHEMA_VERSION
    assert result["entry_count"] == 5
    assert "by_track" in result
    assert "by_status" in result
    assert "disclaimer" in result


def test_cli_epoch_plan_summary_with_custom_fixture(tmp_path):
    fixture = {
        "schema_version": "epoch_plan_v1",
        "disclaimer": "test",
        "entries": [
            {
                "entry_id": "ep-x",
                "target_id": "t-x",
                "track": "radio",
                "current_epoch_count": 1,
                "requested_additional_epochs": 2,
                "rationale": "needs confirmation",
                "status": "pending",
                "priority": "high",
                "created_utc": "2026-01-01T00:00:00Z",
            }
        ],
    }
    fp = tmp_path / "epoch_plan.json"
    fp.write_text(json.dumps(fixture), encoding="utf-8")

    stdout = StringIO()
    exit_code = main(["epoch-plan-summary", "--fixture-path", str(fp)], stdout=stdout)
    result = json.loads(stdout.getvalue())
    assert exit_code == 0
    assert result["entry_count"] == 1
    assert result["by_track"] == {"radio": 1}
