"""Operational provenance records for telescope cooling system events."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

COOLING_SYSTEM_LOG_SCHEMA_VERSION = "cooling_system_log_v1"

COOLING_SYSTEM_LOG_DISCLAIMER = (
    "Cooling system log entries are operational provenance records — "
    "a cooling system record does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

ALLOWED_COOLING_KINDS = frozenset(
    {
        "cooldown_start",
        "cooldown_complete",
        "warmup_event",
        "temperature_alarm",
        "helium_refill",
    }
)

ALLOWED_COOLING_STATUSES = frozenset(
    {
        "operating",
        "warning",
        "fault",
        "maintenance",
    }
)


@dataclass
class CoolingSystemEntry:
    entry_id: str
    cooling_kind: str
    status: str
    recorded_by: str
    timestamp_utc: str
    system_id: str | None
    temperature_kelvin: float | None
    notes: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "cooling_kind": self.cooling_kind,
            "status": self.status,
            "recorded_by": self.recorded_by,
            "timestamp_utc": self.timestamp_utc,
            "system_id": self.system_id,
            "temperature_kelvin": self.temperature_kelvin,
            "notes": self.notes,
        }


def load_cooling_system_entries(path: Path | None = None) -> list[CoolingSystemEntry]:
    if path is None:
        path = (
            Path(__file__).parent.parent.parent
            / "tests"
            / "fixtures"
            / "cooling_system_log.json"
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        CoolingSystemEntry(
            entry_id=e["entry_id"],
            cooling_kind=e["cooling_kind"],
            status=e["status"],
            recorded_by=e["recorded_by"],
            timestamp_utc=e["timestamp_utc"],
            system_id=e.get("system_id"),
            temperature_kelvin=e.get("temperature_kelvin"),
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def cooling_system_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_cooling_system_entries(path)
    counts_by_status: dict[str, int] = {}
    for e in entries:
        counts_by_status[e.status] = counts_by_status.get(e.status, 0) + 1
    counts_by_kind: dict[str, int] = {}
    for e in entries:
        counts_by_kind[e.cooling_kind] = counts_by_kind.get(e.cooling_kind, 0) + 1
    return {
        "schema_version": COOLING_SYSTEM_LOG_SCHEMA_VERSION,
        "disclaimer": COOLING_SYSTEM_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "operating_count": counts_by_status.get("operating", 0),
        "warning_count": counts_by_status.get("warning", 0),
        "fault_count": counts_by_status.get("fault", 0),
        "maintenance_count": counts_by_status.get("maintenance", 0),
        "counts_by_status": counts_by_status,
        "counts_by_kind": counts_by_kind,
    }
