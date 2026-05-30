"""Operational provenance records for environmental monitoring events."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ENVIRONMENTAL_LOG_SCHEMA_VERSION = "environmental_log_v1"

ENVIRONMENTAL_LOG_DISCLAIMER = (
    "Environmental log entries are operational provenance records — "
    "an environmental reading does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

ALLOWED_ENVIRONMENT_KINDS = frozenset(
    {
        "temperature_reading",
        "humidity_reading",
        "pressure_reading",
        "vibration_reading",
        "electromagnetic_interference",
    }
)

ALLOWED_ENVIRONMENT_STATUSES = frozenset(
    {
        "nominal",
        "advisory",
        "warning",
        "critical",
    }
)


@dataclass
class EnvironmentalEntry:
    entry_id: str
    environment_kind: str
    status: str
    recorded_by: str
    timestamp_utc: str
    component_id: str | None
    notes: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "environment_kind": self.environment_kind,
            "status": self.status,
            "recorded_by": self.recorded_by,
            "timestamp_utc": self.timestamp_utc,
            "component_id": self.component_id,
            "notes": self.notes,
        }


def load_environmental_entries(path: Path | None = None) -> list[EnvironmentalEntry]:
    if path is None:
        path = (
            Path(__file__).parent.parent.parent
            / "tests"
            / "fixtures"
            / "environmental_log.json"
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        EnvironmentalEntry(
            entry_id=e["entry_id"],
            environment_kind=e["environment_kind"],
            status=e["status"],
            recorded_by=e["recorded_by"],
            timestamp_utc=e["timestamp_utc"],
            component_id=e.get("component_id"),
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def environmental_log_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_environmental_entries(path)
    counts_by_status: dict[str, int] = {}
    for e in entries:
        counts_by_status[e.status] = counts_by_status.get(e.status, 0) + 1
    counts_by_kind: dict[str, int] = {}
    for e in entries:
        counts_by_kind[e.environment_kind] = counts_by_kind.get(e.environment_kind, 0) + 1
    return {
        "schema_version": ENVIRONMENTAL_LOG_SCHEMA_VERSION,
        "disclaimer": ENVIRONMENTAL_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "nominal_count": counts_by_status.get("nominal", 0),
        "advisory_count": counts_by_status.get("advisory", 0),
        "warning_count": counts_by_status.get("warning", 0),
        "critical_count": counts_by_status.get("critical", 0),
        "counts_by_status": counts_by_status,
        "counts_by_kind": counts_by_kind,
    }
