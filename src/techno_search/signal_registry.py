"""Signal-of-interest registry — scheduling aid for candidate signals worth tracking."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SIGNAL_REGISTRY_SCHEMA_VERSION = "signal_registry_v1"

SIGNAL_REGISTRY_DISCLAIMER = (
    "Signal registry entries are scheduling-aid records of candidate signals worth "
    "tracking. They are not detection claims, discovery announcements, or "
    "authorizations for external submission. Registry priority tiers are "
    "operator scheduling metadata only."
)

ALLOWED_PRIORITY_TIERS = frozenset({"tier_1", "tier_2", "tier_3"})


def _default_signal_registry_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "signal_registry.json"
    )


@dataclass
class SignalOfInterest:
    signal_id: str
    candidate_id: str
    track: str
    priority_tier: str
    rationale: str
    added_utc: str
    is_active: bool
    source_catalog: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "candidate_id": self.candidate_id,
            "track": self.track,
            "priority_tier": self.priority_tier,
            "rationale": self.rationale,
            "added_utc": self.added_utc,
            "is_active": self.is_active,
            "source_catalog": self.source_catalog,
        }


def load_signal_registry(
    fixture_path: Path | None = None,
) -> list[SignalOfInterest]:
    path = fixture_path or _default_signal_registry_path()
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    signals = []
    for raw in data.get("signals", []):
        signals.append(
            SignalOfInterest(
                signal_id=str(raw["signal_id"]),
                candidate_id=str(raw["candidate_id"]),
                track=str(raw["track"]),
                priority_tier=str(raw["priority_tier"]),
                rationale=str(raw["rationale"]),
                added_utc=str(raw["added_utc"]),
                is_active=bool(raw.get("is_active", True)),
                source_catalog=raw.get("source_catalog"),
            )
        )
    return signals


def signal_registry_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    """Return a summary of the signal-of-interest registry."""

    signals = load_signal_registry(fixture_path)

    by_track: dict[str, int] = {}
    by_priority_tier: dict[str, int] = {}
    active_count = 0

    for sig in signals:
        by_track[sig.track] = by_track.get(sig.track, 0) + 1
        by_priority_tier[sig.priority_tier] = (
            by_priority_tier.get(sig.priority_tier, 0) + 1
        )
        if sig.is_active:
            active_count += 1

    return {
        "schema_version": SIGNAL_REGISTRY_SCHEMA_VERSION,
        "disclaimer": SIGNAL_REGISTRY_DISCLAIMER,
        "signal_count": len(signals),
        "active_count": active_count,
        "inactive_count": len(signals) - active_count,
        "by_track": dict(sorted(by_track.items())),
        "by_priority_tier": dict(sorted(by_priority_tier.items())),
        "tracks_covered": sorted(by_track.keys()),
    }


def signal_registry_track_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    """Return per-track breakdown of signal registry entries."""

    signals = load_signal_registry(fixture_path)

    by_track: dict[str, dict[str, int]] = {}
    for sig in signals:
        t = sig.track
        if t not in by_track:
            by_track[t] = {"total": 0, "active": 0, "tier_1": 0, "tier_2": 0, "tier_3": 0}
        by_track[t]["total"] += 1
        if sig.is_active:
            by_track[t]["active"] += 1
        tier_key = sig.priority_tier
        if tier_key in by_track[t]:
            by_track[t][tier_key] += 1

    tracks_covered = sorted(by_track.keys())

    return {
        "schema_version": SIGNAL_REGISTRY_SCHEMA_VERSION,
        "disclaimer": SIGNAL_REGISTRY_DISCLAIMER,
        "track_count": len(by_track),
        "tracks_covered": tracks_covered,
        "by_track": dict(sorted(by_track.items())),
    }
