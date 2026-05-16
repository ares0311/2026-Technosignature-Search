"""Epoch plan — scheduling aid for targets requiring additional observation epochs."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

EPOCH_PLAN_SCHEMA_VERSION = "epoch_plan_v1"

EPOCH_PLAN_DISCLAIMER = (
    "Epoch plan entries are local scheduling aids that identify targets needing "
    "additional observation epochs. They do not constitute detection claims, "
    "confirmation of signals, or commitments to telescope time. Entries are "
    "provenance records only."
)

ALLOWED_EPOCH_PLAN_STATUSES = frozenset(
    {
        "pending",
        "scheduled",
        "in_progress",
        "completed",
        "deferred",
        "cancelled",
    }
)

ALLOWED_EPOCH_PRIORITIES = frozenset({"high", "medium", "low"})


def _default_epoch_plan_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "epoch_plan.json"
    )


@dataclass
class EpochPlanEntry:
    entry_id: str
    target_id: str
    track: str
    current_epoch_count: int
    requested_additional_epochs: int
    rationale: str
    status: str
    priority: str
    created_utc: str
    blocking_reasons: list[str] = field(default_factory=list)
    operator_id: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "target_id": self.target_id,
            "track": self.track,
            "current_epoch_count": self.current_epoch_count,
            "requested_additional_epochs": self.requested_additional_epochs,
            "rationale": self.rationale,
            "status": self.status,
            "priority": self.priority,
            "created_utc": self.created_utc,
            "blocking_reasons": list(self.blocking_reasons),
            "operator_id": self.operator_id,
        }


def load_epoch_plan(
    fixture_path: Path | None = None,
) -> list[EpochPlanEntry]:
    path = fixture_path or _default_epoch_plan_path()
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    entries = []
    for raw in data.get("entries", []):
        entries.append(
            EpochPlanEntry(
                entry_id=str(raw["entry_id"]),
                target_id=str(raw["target_id"]),
                track=str(raw["track"]),
                current_epoch_count=int(raw["current_epoch_count"]),
                requested_additional_epochs=int(raw["requested_additional_epochs"]),
                rationale=str(raw.get("rationale", "")),
                status=str(raw["status"]),
                priority=str(raw["priority"]),
                created_utc=str(raw["created_utc"]),
                blocking_reasons=list(raw.get("blocking_reasons", [])),
                operator_id=str(raw.get("operator_id", "")),
            )
        )
    return entries


def epoch_plan_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    """Return a summary of the epoch plan entries."""

    entries = load_epoch_plan(fixture_path)

    by_track: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    total_additional_epochs = 0
    blocked_count = 0

    for entry in entries:
        by_track[entry.track] = by_track.get(entry.track, 0) + 1
        by_status[entry.status] = by_status.get(entry.status, 0) + 1
        by_priority[entry.priority] = by_priority.get(entry.priority, 0) + 1
        total_additional_epochs += entry.requested_additional_epochs
        if entry.blocking_reasons:
            blocked_count += 1

    pending_count = by_status.get("pending", 0) + by_status.get("scheduled", 0)

    return {
        "schema_version": EPOCH_PLAN_SCHEMA_VERSION,
        "disclaimer": EPOCH_PLAN_DISCLAIMER,
        "entry_count": len(entries),
        "pending_count": pending_count,
        "blocked_count": blocked_count,
        "total_additional_epochs_requested": total_additional_epochs,
        "by_track": dict(sorted(by_track.items())),
        "by_status": dict(sorted(by_status.items())),
        "by_priority": dict(sorted(by_priority.items())),
        "tracks_covered": sorted(by_track.keys()),
    }
