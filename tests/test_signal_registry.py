"""Tests for signal_registry module."""

from __future__ import annotations

from techno_search.signal_registry import (
    ALLOWED_PRIORITY_TIERS,
    SIGNAL_REGISTRY_DISCLAIMER,
    SIGNAL_REGISTRY_SCHEMA_VERSION,
    SignalOfInterest,
    load_signal_registry,
    signal_registry_summary,
    signal_registry_track_summary,
)


def test_load_signal_registry_returns_list():
    signals = load_signal_registry()
    assert isinstance(signals, list)
    assert len(signals) >= 1


def test_signal_of_interest_is_dataclass():
    signals = load_signal_registry()
    for sig in signals:
        assert isinstance(sig, SignalOfInterest)
        assert sig.signal_id
        assert sig.candidate_id
        assert sig.track
        assert sig.priority_tier in ALLOWED_PRIORITY_TIERS


def test_signal_registry_has_radio_infrared_anomaly():
    signals = load_signal_registry()
    tracks = {s.track for s in signals}
    assert "radio" in tracks
    assert "infrared" in tracks
    assert "anomaly" in tracks


def test_signal_registry_has_active_signals():
    signals = load_signal_registry()
    active = [s for s in signals if s.is_active]
    assert len(active) >= 4


def test_signal_registry_has_tier_1():
    signals = load_signal_registry()
    tier_1 = [s for s in signals if s.priority_tier == "tier_1"]
    assert len(tier_1) >= 1


def test_signal_registry_summary_schema_version():
    summary = signal_registry_summary()
    assert summary["schema_version"] == SIGNAL_REGISTRY_SCHEMA_VERSION


def test_signal_registry_summary_disclaimer():
    summary = signal_registry_summary()
    assert SIGNAL_REGISTRY_DISCLAIMER in summary["disclaimer"]


def test_signal_registry_summary_counts():
    summary = signal_registry_summary()
    assert isinstance(summary["signal_count"], int)
    assert summary["signal_count"] >= 4
    assert isinstance(summary["active_count"], int)
    assert summary["active_count"] >= 4
    assert isinstance(summary["by_track"], dict)
    assert isinstance(summary["by_priority_tier"], dict)


def test_signal_registry_summary_tracks_covered():
    summary = signal_registry_summary()
    tracks = summary["tracks_covered"]
    assert isinstance(tracks, list)
    assert "radio" in tracks
    assert "infrared" in tracks
    assert "anomaly" in tracks


def test_signal_registry_track_summary_structure():
    summary = signal_registry_track_summary()
    assert "schema_version" in summary
    assert "disclaimer" in summary
    assert "by_track" in summary
    by_track = summary["by_track"]
    assert isinstance(by_track, dict)
    assert len(by_track) >= 3


def test_signal_registry_track_summary_per_track_fields():
    summary = signal_registry_track_summary()
    for _track, stats in summary["by_track"].items():
        assert "total" in stats
        assert "active" in stats
        assert "tier_1" in stats
        assert "tier_2" in stats
        assert "tier_3" in stats


def test_signal_of_interest_as_dict():
    signals = load_signal_registry()
    d = signals[0].as_dict()
    for key in (
        "signal_id", "candidate_id", "track", "priority_tier",
        "rationale", "added_utc", "is_active",
    ):
        assert key in d


def test_allowed_priority_tiers():
    assert "tier_1" in ALLOWED_PRIORITY_TIERS
    assert "tier_2" in ALLOWED_PRIORITY_TIERS
    assert "tier_3" in ALLOWED_PRIORITY_TIERS
