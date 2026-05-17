"""Escalation log — records formal workflow escalation events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ESCALATION_LOG_SCHEMA_VERSION = "escalation_log_v1"

ESCALATION_LOG_DISCLAIMER = (
    "Escalation log entries are local scheduling and workflow provenance records only. "
    "Escalation priority reflects internal operational urgency, not candidate scientific "
    "interest or discovery probability. Escalated status does not modify pathway routing "
    "or candidate posteriors."
)

ALLOWED_ESCALATION_PRIORITIES = frozenset({"low", "normal", "high", "critical"})

ALLOWED_ESCALATION_STATUSES = frozenset({"open", "in_review", "resolved", "dismissed"})


def _default_escalation_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "escalation_log.json"
    )


@dataclass
class EscalationEntry:
    entry_id: str
    candidate_id: str
    track: str
    priority: str
    status: str
    escalated_by: str
    assigned_to: str
    escalation_reason: str
    escalated_utc: str
    days_open: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "candidate_id": self.candidate_id,
            "track": self.track,
            "priority": self.priority,
            "status": self.status,
            "escalated_by": self.escalated_by,
            "assigned_to": self.assigned_to,
            "escalation_reason": self.escalation_reason,
            "escalated_utc": self.escalated_utc,
            "days_open": self.days_open,
        }


def load_escalation_entries(
    fixture_path: Path | None = None,
) -> list[EscalationEntry]:
    path = fixture_path if fixture_path is not None else _default_escalation_path()
    raw = json.loads(path.read_text())
    entries = raw.get("entries", [])
    result: list[EscalationEntry] = []
    for e in entries:
        result.append(
            EscalationEntry(
                entry_id=str(e["entry_id"]),
                candidate_id=str(e["candidate_id"]),
                track=str(e["track"]),
                priority=str(e["priority"]),
                status=str(e["status"]),
                escalated_by=str(e["escalated_by"]),
                assigned_to=str(e["assigned_to"]),
                escalation_reason=str(e["escalation_reason"]),
                escalated_utc=str(e["escalated_utc"]),
                days_open=int(e["days_open"]),
            )
        )
    return result


def escalation_log_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    entries = load_escalation_entries(fixture_path)

    by_track: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    by_status: dict[str, int] = {}
    open_count = 0
    critical_count = 0
    total_days = 0
    max_days = 0

    for entry in entries:
        by_track[entry.track] = by_track.get(entry.track, 0) + 1
        by_priority[entry.priority] = by_priority.get(entry.priority, 0) + 1
        by_status[entry.status] = by_status.get(entry.status, 0) + 1
        if entry.status in ("open", "in_review"):
            open_count += 1
        if entry.priority == "critical":
            critical_count += 1
        total_days += entry.days_open
        if entry.days_open > max_days:
            max_days = entry.days_open

    avg_days = round(total_days / len(entries), 1) if entries else 0.0
    unique_operators = {e.escalated_by for e in entries} | {e.assigned_to for e in entries}

    return {
        "schema_version": ESCALATION_LOG_SCHEMA_VERSION,
        "disclaimer": ESCALATION_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "open_count": open_count,
        "critical_count": critical_count,
        "average_days_open": avg_days,
        "max_days_open": max_days,
        "by_track": dict(sorted(by_track.items())),
        "by_priority": dict(sorted(by_priority.items())),
        "by_status": dict(sorted(by_status.items())),
        "tracks_covered": sorted(by_track.keys()),
        "unique_operator_count": len(unique_operators),
    }
