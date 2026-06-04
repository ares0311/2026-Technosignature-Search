"""Operational provenance records for incident events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

INCIDENT_LOG_SCHEMA_VERSION = "incident_log_v1"
INCIDENT_LOG_DISCLAIMER = (
    "Incident log entries are operational provenance records — "
    "an incident event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)
ALLOWED_INCIDENT_KINDS = frozenset(
    {
        "data_integrity_incident",
        "hardware_incident",
        "network_incident",
        "security_incident",
        "software_incident",
    }
)
ALLOWED_INCIDENT_STATUSES = frozenset(
    {
        "closed",
        "escalated",
        "open",
        "under_investigation",
    }
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent / "tests" / "fixtures" / "incident_log.json"
)


@dataclass(frozen=True)
class IncidentEntry:
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


def load_incident_entries(path: Path | None = None) -> list[IncidentEntry]:
    fixture_path = path if path is not None else _DEFAULT_FIXTURE
    raw = json.loads(Path(fixture_path).read_text())
    return [
        IncidentEntry(
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


def incident_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_incident_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    open_count = 0
    for e in entries:
        by_kind[e.incident_kind] = by_kind.get(e.incident_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
        if e.status == "open":
            open_count += 1
    return {
        "schema_version": INCIDENT_LOG_SCHEMA_VERSION,
        "disclaimer": INCIDENT_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "open_count": open_count,
        "by_kind": by_kind,
        "by_status": by_status,
    }
