"""Operational scheduling provenance records for target selection events."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TARGET_SELECTION_LOG_SCHEMA_VERSION = "target_selection_log_v1"

TARGET_SELECTION_LOG_DISCLAIMER = (
    "Target selection entries are operational scheduling provenance records — "
    "a selection does not modify candidate scores or pathway routing, "
    "does not authorize external submission, "
    "and does not constitute a detection claim."
)

ALLOWED_TARGET_SELECTION_KINDS = frozenset({
    "priority_queue",
    "manual_selection",
    "automated_filter",
    "watchlist_trigger",
    "follow_up_request",
})

ALLOWED_TARGET_SELECTION_STATUSES = frozenset({
    "selected",
    "deferred",
    "rejected",
    "pending",
})


def _default_target_selection_log_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "target_selection_log.json"
    )


@dataclass
class TargetSelectionEntry:
    entry_id: str
    candidate_id: str
    track: str
    selection_kind: str
    status: str
    selected_by: str
    selected_at: str
    priority_score: float | None = None
    reason: str | None = None
    notes: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "candidate_id": self.candidate_id,
            "track": self.track,
            "selection_kind": self.selection_kind,
            "status": self.status,
            "selected_by": self.selected_by,
            "selected_at": self.selected_at,
            "priority_score": self.priority_score,
            "reason": self.reason,
            "notes": self.notes,
        }


def load_target_selection_entries(
    path: Path | None = None,
) -> list[TargetSelectionEntry]:
    fpath = path or _default_target_selection_log_path()
    with open(fpath) as f:
        data = json.load(f)
    entries = []
    for item in data.get("entries", []):
        entries.append(TargetSelectionEntry(
            entry_id=item["entry_id"],
            candidate_id=item["candidate_id"],
            track=item["track"],
            selection_kind=item["selection_kind"],
            status=item["status"],
            selected_by=item["selected_by"],
            selected_at=item["selected_at"],
            priority_score=item.get("priority_score"),
            reason=item.get("reason"),
            notes=item.get("notes"),
        ))
    return entries


def target_selection_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_target_selection_entries(path)
    by_kind: dict[str, int] = {}
    by_track: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for e in entries:
        by_kind[e.selection_kind] = by_kind.get(e.selection_kind, 0) + 1
        by_track[e.track] = by_track.get(e.track, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
    return {
        "schema_version": TARGET_SELECTION_LOG_SCHEMA_VERSION,
        "disclaimer": TARGET_SELECTION_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "selected_count": by_status.get("selected", 0),
        "deferred_count": by_status.get("deferred", 0),
        "rejected_count": by_status.get("rejected", 0),
        "pending_count": by_status.get("pending", 0),
        "counts_by_kind": by_kind,
        "counts_by_track": by_track,
    }
