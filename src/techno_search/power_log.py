"""Operational provenance records for facility power system events."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

POWER_LOG_SCHEMA_VERSION = "power_log_v1"

POWER_LOG_DISCLAIMER = (
    "Power log entries are operational provenance records — "
    "a power event record does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

ALLOWED_POWER_KINDS = frozenset(
    {
        "ups_event",
        "mains_failure",
        "generator_start",
        "load_shed",
        "power_restoration",
    }
)

ALLOWED_POWER_STATUSES = frozenset(
    {
        "normal",
        "degraded",
        "critical",
        "restored",
    }
)


@dataclass
class PowerEntry:
    entry_id: str
    power_kind: str
    status: str
    recorded_by: str
    timestamp_utc: str
    facility_id: str | None
    duration_seconds: float | None
    notes: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "power_kind": self.power_kind,
            "status": self.status,
            "recorded_by": self.recorded_by,
            "timestamp_utc": self.timestamp_utc,
            "facility_id": self.facility_id,
            "duration_seconds": self.duration_seconds,
            "notes": self.notes,
        }


def load_power_entries(path: Path | None = None) -> list[PowerEntry]:
    if path is None:
        path = (
            Path(__file__).parent.parent.parent
            / "tests"
            / "fixtures"
            / "power_log.json"
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        PowerEntry(
            entry_id=e["entry_id"],
            power_kind=e["power_kind"],
            status=e["status"],
            recorded_by=e["recorded_by"],
            timestamp_utc=e["timestamp_utc"],
            facility_id=e.get("facility_id"),
            duration_seconds=e.get("duration_seconds"),
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def power_log_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_power_entries(path)
    counts_by_status: dict[str, int] = {}
    for e in entries:
        counts_by_status[e.status] = counts_by_status.get(e.status, 0) + 1
    counts_by_kind: dict[str, int] = {}
    for e in entries:
        counts_by_kind[e.power_kind] = counts_by_kind.get(e.power_kind, 0) + 1
    return {
        "schema_version": POWER_LOG_SCHEMA_VERSION,
        "disclaimer": POWER_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "normal_count": counts_by_status.get("normal", 0),
        "degraded_count": counts_by_status.get("degraded", 0),
        "critical_count": counts_by_status.get("critical", 0),
        "restored_count": counts_by_status.get("restored", 0),
        "counts_by_status": counts_by_status,
        "counts_by_kind": counts_by_kind,
    }
