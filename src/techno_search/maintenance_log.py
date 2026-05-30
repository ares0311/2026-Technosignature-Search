"""Operational provenance records for maintenance events."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MAINTENANCE_LOG_SCHEMA_VERSION = "maintenance_log_v1"

MAINTENANCE_LOG_DISCLAIMER = (
    "Maintenance log entries are operational provenance records — "
    "a maintenance record does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

ALLOWED_MAINTENANCE_KINDS = frozenset(
    {
        "scheduled_maintenance",
        "emergency_repair",
        "calibration_service",
        "firmware_service",
        "inspection",
    }
)

ALLOWED_MAINTENANCE_STATUSES = frozenset(
    {
        "planned",
        "in_progress",
        "completed",
        "deferred",
    }
)


@dataclass
class MaintenanceEntry:
    entry_id: str
    maintenance_kind: str
    status: str
    recorded_by: str
    timestamp_utc: str
    component_id: str | None
    notes: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "maintenance_kind": self.maintenance_kind,
            "status": self.status,
            "recorded_by": self.recorded_by,
            "timestamp_utc": self.timestamp_utc,
            "component_id": self.component_id,
            "notes": self.notes,
        }


def load_maintenance_entries(path: Path | None = None) -> list[MaintenanceEntry]:
    if path is None:
        path = (
            Path(__file__).parent.parent.parent
            / "tests"
            / "fixtures"
            / "maintenance_log.json"
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        MaintenanceEntry(
            entry_id=e["entry_id"],
            maintenance_kind=e["maintenance_kind"],
            status=e["status"],
            recorded_by=e["recorded_by"],
            timestamp_utc=e["timestamp_utc"],
            component_id=e.get("component_id"),
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def maintenance_log_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_maintenance_entries(path)
    counts_by_status: dict[str, int] = {}
    for e in entries:
        counts_by_status[e.status] = counts_by_status.get(e.status, 0) + 1
    counts_by_kind: dict[str, int] = {}
    for e in entries:
        counts_by_kind[e.maintenance_kind] = counts_by_kind.get(e.maintenance_kind, 0) + 1
    return {
        "schema_version": MAINTENANCE_LOG_SCHEMA_VERSION,
        "disclaimer": MAINTENANCE_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "completed_count": counts_by_status.get("completed", 0),
        "in_progress_count": counts_by_status.get("in_progress", 0),
        "planned_count": counts_by_status.get("planned", 0),
        "deferred_count": counts_by_status.get("deferred", 0),
        "counts_by_status": counts_by_status,
        "counts_by_kind": counts_by_kind,
    }
