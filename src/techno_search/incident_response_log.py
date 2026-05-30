"""Operational provenance records for facility incident response events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

INCIDENT_RESPONSE_LOG_SCHEMA_VERSION = "incident_response_log_v1"

ALLOWED_INCIDENT_KINDS = frozenset(
    {
        "containment",
        "detection",
        "eradication",
        "lessons_learned",
        "recovery",
    }
)

ALLOWED_INCIDENT_STATUSES = frozenset(
    {
        "closed",
        "contained",
        "open",
        "resolved",
    }
)

_DISCLAIMER = (
    "Incident response log entries are operational provenance records — "
    "an incident response event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "incident_response_log.json"
)


@dataclass(frozen=True)
class IncidentResponseEntry:
    entry_id: str
    incident_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.incident_kind not in ALLOWED_INCIDENT_KINDS:
            raise ValueError(f"Invalid incident_kind: {self.incident_kind!r}")
        if self.status not in ALLOWED_INCIDENT_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_incident_response_entries(
    path: Path | None = None,
) -> list[IncidentResponseEntry]:
    if path is None:
        path = _DEFAULT_FIXTURE
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return [
        IncidentResponseEntry(
            entry_id=e["entry_id"],
            incident_kind=e["incident_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def incident_response_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_incident_response_entries(path)
    resolved = sum(1 for e in entries if e.status == "resolved")
    return {
        "schema_version": INCIDENT_RESPONSE_LOG_SCHEMA_VERSION,
        "disclaimer": _DISCLAIMER,
        "entry_count": len(entries),
        "resolved_count": resolved,
        "by_kind": {
            kind: sum(1 for e in entries if e.incident_kind == kind)
            for kind in sorted(ALLOWED_INCIDENT_KINDS)
        },
        "by_status": {
            status: sum(1 for e in entries if e.status == status)
            for status in sorted(ALLOWED_INCIDENT_STATUSES)
        },
    }
