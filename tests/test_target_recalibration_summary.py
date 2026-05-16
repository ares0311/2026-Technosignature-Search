"""Tests for target_recalibration_summary module."""

from __future__ import annotations

from techno_search.target_recalibration_summary import (
    TARGET_RECALIBRATION_DISCLAIMER,
    TARGET_RECALIBRATION_SCHEMA_VERSION,
    TargetPrioritySnapshot,
    load_priority_snapshots,
    target_recalibration_summary,
)


def test_load_priority_snapshots_returns_list():
    snapshots = load_priority_snapshots()
    assert isinstance(snapshots, list)
    assert len(snapshots) >= 2


def test_snapshot_is_dataclass():
    snapshots = load_priority_snapshots()
    for snap in snapshots:
        assert isinstance(snap, TargetPrioritySnapshot)
        assert snap.snapshot_id
        assert snap.snapshot_utc
        assert isinstance(snap.ordered_target_ids, list)
        assert isinstance(snap.priority_scores, dict)


def test_snapshots_have_ordered_targets():
    snapshots = load_priority_snapshots()
    for snap in snapshots:
        assert len(snap.ordered_target_ids) >= 1
        for tid in snap.ordered_target_ids:
            assert tid in snap.priority_scores


def test_target_recalibration_summary_schema_version():
    summary = target_recalibration_summary()
    assert summary["schema_version"] == TARGET_RECALIBRATION_SCHEMA_VERSION


def test_target_recalibration_summary_disclaimer():
    summary = target_recalibration_summary()
    assert TARGET_RECALIBRATION_DISCLAIMER in summary["disclaimer"]


def test_target_recalibration_summary_ok():
    summary = target_recalibration_summary()
    assert summary["ok"] is True
    assert summary["snapshot_count"] >= 2


def test_target_recalibration_summary_rank_fields():
    summary = target_recalibration_summary()
    assert "rank_change_count" in summary
    assert "new_top_target_id" in summary
    assert "previous_top_target_id" in summary
    assert "top_changed" in summary
    assert "mean_absolute_rank_change" in summary


def test_target_recalibration_summary_top_target():
    summary = target_recalibration_summary()
    new_top = summary["new_top_target_id"]
    prev_top = summary["previous_top_target_id"]
    assert new_top is not None
    assert prev_top is not None


def test_target_recalibration_summary_top_changed_reflects_fixtures():
    snapshots = load_priority_snapshots()
    summary = target_recalibration_summary()
    current_top = snapshots[-1].ordered_target_ids[0]
    previous_top = snapshots[-2].ordered_target_ids[0]
    expected_changed = current_top != previous_top
    assert summary["top_changed"] == expected_changed


def test_target_recalibration_summary_mean_rank_change_type():
    summary = target_recalibration_summary()
    assert isinstance(summary["mean_absolute_rank_change"], float)


def test_snapshot_as_dict():
    snapshots = load_priority_snapshots()
    d = snapshots[0].as_dict()
    for key in ("snapshot_id", "snapshot_utc", "ordered_target_ids", "priority_scores"):
        assert key in d


def test_recalibration_summary_insufficient_snapshots(tmp_path):
    import json

    fixture = tmp_path / "single_snapshot.json"
    fixture.write_text(json.dumps({
        "schema_version": TARGET_RECALIBRATION_SCHEMA_VERSION,
        "disclaimer": TARGET_RECALIBRATION_DISCLAIMER,
        "snapshots": [
            {
                "snapshot_id": "snap-1",
                "snapshot_utc": "2026-01-01T00:00:00Z",
                "ordered_target_ids": ["target-a"],
                "priority_scores": {"target-a": 0.9},
            }
        ],
    }))
    summary = target_recalibration_summary(fixture)
    assert summary["ok"] is False
    assert summary["snapshot_count"] == 1
    assert summary["rank_change_count"] == 0
