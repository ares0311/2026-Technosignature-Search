"""Operational provenance records for scheduling conflict events."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEDULING_CONFLICT_LOG_SCHEMA_VERSION = "scheduling_conflict_log_v1"

SCHEDULING_CONFLICT_LOG_DISCLAIMER = (
    "Scheduling conflict entries are operational provenance records — "
    "a conflict record does not modify candidate scores or pathway routing, "
    "does not authorize external submission, "
    "and does not constitute a detection claim."
)

ALLOWED_CONFLICT_KINDS = frozenset({
    "time_slot_overlap",
    "resource_contention",
    "priority_conflict",
    "maintenance_window",
    "weather_hold",
})

ALLOWED_CONFLICT_STATUSES = frozenset({
    "detected",
    "resolved",
    "escalated",
    "deferred",
})


def _default_scheduling_conflict_log_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "scheduling_conflict_log.json"
    )


@dataclass
class SchedulingConflictEntry:
    entry_id: str
    conflict_kind: str
    status: str
    detected_by: str
    detected_at: str
    affected_candidate_id: str | None = None
    track: str | None = None
    resolution_note: str | None = None
    resolved_at: str | None = None
    notes: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "conflict_kind": self.conflict_kind,
            "status": self.status,
            "detected_by": self.detected_by,
            "detected_at": self.detected_at,
            "affected_candidate_id": self.affected_candidate_id,
            "track": self.track,
            "resolution_note": self.resolution_note,
            "resolved_at": self.resolved_at,
            "notes": self.notes,
        }


def load_scheduling_conflict_entries(
    path: Path | None = None,
) -> list[SchedulingConflictEntry]:
    fpath = path or _default_scheduling_conflict_log_path()
    with open(fpath) as f:
        data = json.load(f)
    entries = []
    for item in data.get("entries", []):
        entries.append(SchedulingConflictEntry(
            entry_id=item["entry_id"],
            conflict_kind=item["conflict_kind"],
            status=item["status"],
            detected_by=item["detected_by"],
            detected_at=item["detected_at"],
            affected_candidate_id=item.get("affected_candidate_id"),
            track=item.get("track"),
            resolution_note=item.get("resolution_note"),
            resolved_at=item.get("resolved_at"),
            notes=item.get("notes"),
        ))
    return entries


def scheduling_conflict_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_scheduling_conflict_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for e in entries:
        by_kind[e.conflict_kind] = by_kind.get(e.conflict_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
    return {
        "schema_version": SCHEDULING_CONFLICT_LOG_SCHEMA_VERSION,
        "disclaimer": SCHEDULING_CONFLICT_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "detected_count": by_status.get("detected", 0),
        "resolved_count": by_status.get("resolved", 0),
        "escalated_count": by_status.get("escalated", 0),
        "deferred_count": by_status.get("deferred", 0),
        "counts_by_kind": by_kind,
    }
