"""Candidate priority queue module — ordered queue of candidates awaiting review."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CANDIDATE_PRIORITY_QUEUE_SCHEMA_VERSION = "candidate_priority_queue_v1"

CANDIDATE_PRIORITY_QUEUE_DISCLAIMER = (
    "Candidate priority queue entries are local scheduling aids only. "
    "Queue position reflects operational scheduling order — it does not "
    "indicate candidate scientific merit or likelihood of representing a "
    "technosignature. Queue reason reflects the scheduling trigger, not "
    "a scientific assessment. Priority queue records are provenance metadata."
)

ALLOWED_QUEUE_REASONS = frozenset(
    {
        "score_threshold",
        "flag_escalation",
        "deadline_pressure",
        "operator_request",
        "routine_review",
    }
)


def _default_fixture_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "candidate_priority_queue.json"
    )


@dataclass
class CandidatePriorityQueueEntry:
    queue_id: str
    candidate_id: str
    track: str
    queue_reason: str
    queue_position: int
    added_utc: str
    operator_assigned: str
    days_in_queue: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "queue_id": self.queue_id,
            "candidate_id": self.candidate_id,
            "track": self.track,
            "queue_reason": self.queue_reason,
            "queue_position": self.queue_position,
            "added_utc": self.added_utc,
            "operator_assigned": self.operator_assigned,
            "days_in_queue": self.days_in_queue,
        }


def load_priority_queue_entries(
    fixture_path: Path | None = None,
) -> list[CandidatePriorityQueueEntry]:
    path = fixture_path or _default_fixture_path()
    with Path(path).open(encoding="utf-8") as fh:
        data = json.load(fh)
    entries = []
    for item in data.get("queue_entries", []):
        entries.append(
            CandidatePriorityQueueEntry(
                queue_id=item["queue_id"],
                candidate_id=item["candidate_id"],
                track=item["track"],
                queue_reason=item["queue_reason"],
                queue_position=int(item.get("queue_position", 0)),
                added_utc=item["added_utc"],
                operator_assigned=item.get("operator_assigned", ""),
                days_in_queue=int(item.get("days_in_queue", 0)),
            )
        )
    return entries


def priority_queue_summary(fixture_path: Path | None = None) -> dict[str, Any]:
    entries = load_priority_queue_entries(fixture_path)

    days_values = [e.days_in_queue for e in entries]
    average_days = round(sum(days_values) / len(days_values), 1) if days_values else 0.0
    max_days = max(days_values) if days_values else 0

    by_track: dict[str, int] = {}
    by_reason: dict[str, int] = {}

    for e in entries:
        by_track[e.track] = by_track.get(e.track, 0) + 1
        by_reason[e.queue_reason] = by_reason.get(e.queue_reason, 0) + 1

    return {
        "schema_version": CANDIDATE_PRIORITY_QUEUE_SCHEMA_VERSION,
        "disclaimer": CANDIDATE_PRIORITY_QUEUE_DISCLAIMER,
        "queue_depth": len(entries),
        "average_days_in_queue": average_days,
        "max_days_in_queue": max_days,
        "by_track": dict(sorted(by_track.items())),
        "by_reason": dict(sorted(by_reason.items())),
        "tracks_covered": sorted(by_track.keys()),
    }
