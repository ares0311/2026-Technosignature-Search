"""Tests for the target watchlist scheduling aid."""

from __future__ import annotations

import json
from io import StringIO

from techno_search.cli import main
from techno_search.target_watchlist import (
    ALLOWED_WATCHLIST_KINDS,
    TARGET_WATCHLIST_DISCLAIMER,
    load_watchlist_entries,
    target_watchlist_summary,
)


def test_watchlist_fixture_loads():
    entries = load_watchlist_entries()
    assert len(entries) >= 4


def test_watchlist_entry_kinds_valid():
    entries = load_watchlist_entries()
    for entry in entries:
        assert entry.watchlist_kind in ALLOWED_WATCHLIST_KINDS


def test_watchlist_summary_counts():
    summary = target_watchlist_summary()
    assert summary["entry_count"] >= 4
    assert summary["elevated_count"] >= 1
    assert summary["deprioritized_count"] >= 1
    assert summary["blocked_count"] >= 1
    assert summary["completed_count"] >= 1


def test_watchlist_summary_disclaimer():
    summary = target_watchlist_summary()
    assert TARGET_WATCHLIST_DISCLAIMER in summary["disclaimer"]
    assert "scheduling aid" in summary["disclaimer"].lower()


def test_watchlist_summary_no_conflicts_in_fixture():
    summary = target_watchlist_summary()
    assert summary["conflict_count"] == 0
    assert summary["conflict_elevated_and_blocked"] == []


def test_watchlist_summary_conflict_detection(tmp_path):
    """Synthetic fixture with both elevated and blocked for the same target."""
    fixture = {
        "schema_version": "target_watchlist_v1",
        "disclaimer": TARGET_WATCHLIST_DISCLAIMER,
        "entries": [
            {
                "target_id": "conflict-target",
                "watchlist_kind": "elevated",
                "added_at_utc": "2026-05-01T00:00:00+00:00",
                "operator_notes": "",
                "priority_override_score": 0.9,
                "blocking_reasons": [],
            },
            {
                "target_id": "conflict-target",
                "watchlist_kind": "blocked",
                "added_at_utc": "2026-05-02T00:00:00+00:00",
                "operator_notes": "",
                "priority_override_score": None,
                "blocking_reasons": ["conflicting entry test"],
            },
        ],
    }
    fp = tmp_path / "test_watchlist.json"
    fp.write_text(json.dumps(fixture), encoding="utf-8")
    summary = target_watchlist_summary(fp)
    assert summary["conflict_count"] == 1
    assert "conflict-target" in summary["conflict_elevated_and_blocked"]


def test_watchlist_summary_blocking_reasons():
    summary = target_watchlist_summary()
    assert summary["total_blocking_reasons"] >= 2


def test_watchlist_summary_operator_notes():
    summary = target_watchlist_summary()
    assert summary["operator_note_count"] >= 3


def test_watchlist_does_not_modify_scoring():
    """Watchlist entries must never touch candidate scores — load side only."""
    from techno_search.schemas import candidate_from_mapping
    from techno_search.scoring import score_candidate

    raw_candidate = {
        "candidate_id": "watchlist-guardrail-test",
        "track": "radio",
        "features": {
            "frequency_mhz": 1420.4,
            "drift_rate_hz_s": 0.0,
            "snr": 25.0,
            "on_source_count": 3,
            "off_source_count": 3,
            "rfi_band_overlap": False,
            "known_rfi_match": False,
            "recurrence_count": 0,
            "data_quality_flag": "good",
        },
    }
    candidate = candidate_from_mapping(raw_candidate)
    scored_before = score_candidate(candidate)

    load_watchlist_entries()

    scored_after = score_candidate(candidate)
    assert (
        scored_before.scores.followup_value
        == scored_after.scores.followup_value
    )
    assert scored_before.recommended_pathway == scored_after.recommended_pathway


def test_cli_target_watchlist_summary():
    out = StringIO()
    ret = main(["target-watchlist-summary"], stdout=out)
    assert ret == 0
    data = json.loads(out.getvalue())
    assert data["entry_count"] >= 4
    assert TARGET_WATCHLIST_DISCLAIMER in data["disclaimer"]
    assert "elevated_count" in data
    assert "blocked_count" in data
    assert "conflict_count" in data
