"""Operational provenance records for hardware fault events."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HARDWARE_FAULT_LOG_SCHEMA_VERSION = "hardware_fault_log_v1"

HARDWARE_FAULT_LOG_DISCLAIMER = (
    "Hardware fault log entries are operational provenance records — "
    "a hardware fault record does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

ALLOWED_FAULT_KINDS = frozenset(
    {
        "cpu_fault",
        "memory_fault",
        "disk_fault",
        "network_fault",
        "psu_fault",
    }
)

ALLOWED_FAULT_STATUSES = frozenset(
    {
        "detected",
        "diagnosed",
        "repaired",
        "deferred",
    }
)


@dataclass
class HardwareFaultEntry:
    entry_id: str
    fault_kind: str
    status: str
    recorded_by: str
    timestamp_utc: str
    component_id: str | None
    notes: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "fault_kind": self.fault_kind,
            "status": self.status,
            "recorded_by": self.recorded_by,
            "timestamp_utc": self.timestamp_utc,
            "component_id": self.component_id,
            "notes": self.notes,
        }


def load_hardware_fault_entries(path: Path | None = None) -> list[HardwareFaultEntry]:
    if path is None:
        path = (
            Path(__file__).parent.parent.parent
            / "tests"
            / "fixtures"
            / "hardware_fault_log.json"
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        HardwareFaultEntry(
            entry_id=e["entry_id"],
            fault_kind=e["fault_kind"],
            status=e["status"],
            recorded_by=e["recorded_by"],
            timestamp_utc=e["timestamp_utc"],
            component_id=e.get("component_id"),
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def hardware_fault_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_hardware_fault_entries(path)
    counts_by_status: dict[str, int] = {}
    for e in entries:
        counts_by_status[e.status] = counts_by_status.get(e.status, 0) + 1
    counts_by_kind: dict[str, int] = {}
    for e in entries:
        counts_by_kind[e.fault_kind] = counts_by_kind.get(e.fault_kind, 0) + 1
    return {
        "schema_version": HARDWARE_FAULT_LOG_SCHEMA_VERSION,
        "disclaimer": HARDWARE_FAULT_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "detected_count": counts_by_status.get("detected", 0),
        "diagnosed_count": counts_by_status.get("diagnosed", 0),
        "repaired_count": counts_by_status.get("repaired", 0),
        "deferred_count": counts_by_status.get("deferred", 0),
        "counts_by_status": counts_by_status,
        "counts_by_kind": counts_by_kind,
    }
