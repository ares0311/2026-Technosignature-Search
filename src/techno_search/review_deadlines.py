"""Review deadlines — upcoming review deadlines with urgency levels."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REVIEW_DEADLINES_SCHEMA_VERSION = "review_deadlines_v1"

REVIEW_DEADLINES_DISCLAIMER = (
    "Review deadline records are local scheduling aids only. "
    "They track upcoming operator review obligations and do not constitute "
    "evidence of a technosignature, detection, or discovery. "
    "Urgency levels reflect scheduling priority, not candidate quality."
)

ALLOWED_DEADLINE_URGENCIES = frozenset({"immediate", "high", "medium", "low"})

ALLOWED_DEADLINE_TYPES = frozenset(
    {
        "initial_review",
        "follow_up_review",
        "escalation_review",
        "epoch_data_ready",
        "operator_handoff",
        "weekly_summary",
    }
)

ALLOWED_DEADLINE_STATUSES = frozenset({"pending", "in_progress", "completed", "overdue", "waived"})


def _default_deadlines_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "review_deadlines.json"
    )


@dataclass
class ReviewDeadline:
    deadline_id: str
    candidate_id: str
    track: str
    operator_id: str
    deadline_type: str
    urgency: str
    due_utc: str
    status: str
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "deadline_id": self.deadline_id,
            "candidate_id": self.candidate_id,
            "track": self.track,
            "operator_id": self.operator_id,
            "deadline_type": self.deadline_type,
            "urgency": self.urgency,
            "due_utc": self.due_utc,
            "status": self.status,
            "notes": self.notes,
        }


def load_review_deadlines(fixture_path: Path | None = None) -> list[ReviewDeadline]:
    path = fixture_path if fixture_path is not None else _default_deadlines_path()
    raw = json.loads(path.read_text())
    deadlines = raw.get("deadlines", [])
    result: list[ReviewDeadline] = []
    for d in deadlines:
        result.append(
            ReviewDeadline(
                deadline_id=str(d["deadline_id"]),
                candidate_id=str(d["candidate_id"]),
                track=str(d["track"]),
                operator_id=str(d["operator_id"]),
                deadline_type=str(d["deadline_type"]),
                urgency=str(d["urgency"]),
                due_utc=str(d["due_utc"]),
                status=str(d["status"]),
                notes=str(d.get("notes", "")),
            )
        )
    return result


def review_deadlines_summary(fixture_path: Path | None = None) -> dict[str, Any]:
    deadlines = load_review_deadlines(fixture_path)

    by_track: dict[str, int] = {}
    by_urgency: dict[str, int] = {}
    by_type: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_operator: dict[str, int] = {}

    pending_count = 0
    overdue_count = 0
    immediate_count = 0

    for dl in deadlines:
        by_track[dl.track] = by_track.get(dl.track, 0) + 1
        by_urgency[dl.urgency] = by_urgency.get(dl.urgency, 0) + 1
        by_type[dl.deadline_type] = by_type.get(dl.deadline_type, 0) + 1
        by_status[dl.status] = by_status.get(dl.status, 0) + 1
        by_operator[dl.operator_id] = by_operator.get(dl.operator_id, 0) + 1
        if dl.status == "pending":
            pending_count += 1
        if dl.status == "overdue":
            overdue_count += 1
        if dl.urgency == "immediate":
            immediate_count += 1

    return {
        "schema_version": REVIEW_DEADLINES_SCHEMA_VERSION,
        "disclaimer": REVIEW_DEADLINES_DISCLAIMER,
        "deadline_count": len(deadlines),
        "unique_candidate_count": len({d.candidate_id for d in deadlines}),
        "pending_count": pending_count,
        "overdue_count": overdue_count,
        "immediate_count": immediate_count,
        "by_track": dict(sorted(by_track.items())),
        "by_urgency": dict(sorted(by_urgency.items())),
        "by_type": dict(sorted(by_type.items())),
        "by_status": dict(sorted(by_status.items())),
        "by_operator": dict(sorted(by_operator.items())),
        "tracks_covered": sorted(by_track.keys()),
    }
