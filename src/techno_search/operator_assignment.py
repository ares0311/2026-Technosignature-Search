"""Operator assignment — tracks which operators are assigned to review candidates."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

OPERATOR_ASSIGNMENT_SCHEMA_VERSION = "operator_assignment_v1"

OPERATOR_ASSIGNMENT_DISCLAIMER = (
    "Operator assignment records are local scheduling aids only. "
    "They track which operators are responsible for reviewing which candidates "
    "and do not constitute evidence of a technosignature, detection, or discovery. "
    "Assignment status reflects operational workflow state, not candidate quality."
)

ALLOWED_ASSIGNMENT_STATUSES = frozenset(
    {
        "pending",
        "in_progress",
        "completed",
        "deferred",
        "reassigned",
        "escalated",
    }
)

ALLOWED_ASSIGNMENT_PRIORITIES = frozenset({"high", "medium", "low"})


def _default_operator_assignment_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "operator_assignments.json"
    )


@dataclass
class OperatorAssignment:
    assignment_id: str
    candidate_id: str
    track: str
    operator_id: str
    assignment_status: str
    priority: str
    assigned_utc: str
    due_utc: str
    completed_utc: str
    notes: str = ""
    escalation_reason: str = ""
    review_tags: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "assignment_id": self.assignment_id,
            "candidate_id": self.candidate_id,
            "track": self.track,
            "operator_id": self.operator_id,
            "assignment_status": self.assignment_status,
            "priority": self.priority,
            "assigned_utc": self.assigned_utc,
            "due_utc": self.due_utc,
            "completed_utc": self.completed_utc,
            "notes": self.notes,
            "escalation_reason": self.escalation_reason,
            "review_tags": list(self.review_tags),
        }


def load_operator_assignments(
    fixture_path: Path | None = None,
) -> list[OperatorAssignment]:
    path = fixture_path if fixture_path is not None else _default_operator_assignment_path()
    raw = json.loads(path.read_text())
    assignments = raw.get("assignments", [])
    result: list[OperatorAssignment] = []
    for a in assignments:
        result.append(
            OperatorAssignment(
                assignment_id=str(a["assignment_id"]),
                candidate_id=str(a["candidate_id"]),
                track=str(a["track"]),
                operator_id=str(a["operator_id"]),
                assignment_status=str(a["assignment_status"]),
                priority=str(a["priority"]),
                assigned_utc=str(a["assigned_utc"]),
                due_utc=str(a["due_utc"]),
                completed_utc=str(a.get("completed_utc", "")),
                notes=str(a.get("notes", "")),
                escalation_reason=str(a.get("escalation_reason", "")),
                review_tags=list(a.get("review_tags", [])),
            )
        )
    return result


def operator_assignment_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    assignments = load_operator_assignments(fixture_path)

    by_track: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    by_operator: dict[str, int] = {}

    pending_count = 0
    escalated_count = 0
    completed_count = 0

    for a in assignments:
        by_track[a.track] = by_track.get(a.track, 0) + 1
        by_status[a.assignment_status] = by_status.get(a.assignment_status, 0) + 1
        by_priority[a.priority] = by_priority.get(a.priority, 0) + 1
        by_operator[a.operator_id] = by_operator.get(a.operator_id, 0) + 1
        if a.assignment_status == "pending":
            pending_count += 1
        if a.assignment_status == "escalated":
            escalated_count += 1
        if a.assignment_status == "completed":
            completed_count += 1

    return {
        "schema_version": OPERATOR_ASSIGNMENT_SCHEMA_VERSION,
        "disclaimer": OPERATOR_ASSIGNMENT_DISCLAIMER,
        "assignment_count": len(assignments),
        "unique_candidate_count": len({a.candidate_id for a in assignments}),
        "unique_operator_count": len(by_operator),
        "pending_count": pending_count,
        "escalated_count": escalated_count,
        "completed_count": completed_count,
        "by_track": dict(sorted(by_track.items())),
        "by_status": dict(sorted(by_status.items())),
        "by_priority": dict(sorted(by_priority.items())),
        "by_operator": dict(sorted(by_operator.items())),
        "tracks_covered": sorted(by_track.keys()),
    }
