"""Tests for multi_epoch_summary module."""

from __future__ import annotations

from techno_search.multi_epoch_summary import (
    MULTI_EPOCH_DISCLAIMER,
    MULTI_EPOCH_SCHEMA_VERSION,
    MultiEpochRecord,
    load_multi_epoch_records,
    multi_epoch_summary,
)


def test_load_multi_epoch_records_returns_list():
    records = load_multi_epoch_records()
    assert isinstance(records, list)
    assert len(records) >= 3


def test_multi_epoch_record_is_dataclass():
    records = load_multi_epoch_records()
    for rec in records:
        assert isinstance(rec, MultiEpochRecord)
        assert rec.target_id
        assert rec.track
        assert rec.epoch_count >= 1
        assert isinstance(rec.status_per_epoch, list)


def test_multi_epoch_records_have_radio_and_infrared():
    records = load_multi_epoch_records()
    tracks = {r.track for r in records}
    assert "radio" in tracks
    assert "infrared" in tracks


def test_multi_epoch_records_have_consistent_and_inconsistent():
    records = load_multi_epoch_records()
    consistent = [r for r in records if r.consistent_detection]
    inconsistent = [r for r in records if not r.consistent_detection]
    assert len(consistent) >= 1
    assert len(inconsistent) >= 1


def test_multi_epoch_summary_schema_version():
    summary = multi_epoch_summary()
    assert summary["schema_version"] == MULTI_EPOCH_SCHEMA_VERSION


def test_multi_epoch_summary_disclaimer():
    summary = multi_epoch_summary()
    assert MULTI_EPOCH_DISCLAIMER in summary["disclaimer"]


def test_multi_epoch_summary_counts():
    summary = multi_epoch_summary()
    assert isinstance(summary["target_count"], int)
    assert summary["target_count"] >= 3
    assert isinstance(summary["multi_epoch_target_count"], int)
    assert summary["multi_epoch_target_count"] >= 3
    assert isinstance(summary["consistent_detection_count"], int)
    assert isinstance(summary["inconsistent_detection_count"], int)


def test_multi_epoch_summary_mean_epoch_count():
    summary = multi_epoch_summary()
    mean = summary["mean_epoch_count"]
    assert isinstance(mean, float)
    assert mean >= 1.0


def test_multi_epoch_summary_by_track():
    summary = multi_epoch_summary()
    by_track = summary["by_track"]
    assert isinstance(by_track, dict)
    assert len(by_track) >= 2


def test_multi_epoch_summary_consistent_detection_note():
    summary = multi_epoch_summary()
    assert "consistent_detection_count" in summary
    count = summary["consistent_detection_count"]
    assert isinstance(count, int)
    assert count >= 1


def test_multi_epoch_record_as_dict():
    records = load_multi_epoch_records()
    d = records[0].as_dict()
    for key in ("target_id", "track", "epoch_count", "first_epoch_utc",
                "latest_epoch_utc", "status_per_epoch", "consistent_detection"):
        assert key in d
