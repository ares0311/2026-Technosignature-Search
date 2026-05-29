"""Operational provenance records for system health monitoring events."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SYSTEM_HEALTH_LOG_SCHEMA_VERSION = "system_health_log_v1"

SYSTEM_HEALTH_LOG_DISCLAIMER = (
    "System health entries are operational provenance records — "
    "a health record does not modify candidate scores or pathway routing, "
    "does not authorize external submission, "
    "and does not constitute a detection claim."
)

ALLOWED_HEALTH_KINDS = frozenset({
    "cpu_usage",
    "memory_usage",
    "disk_space",
    "network_latency",
    "process_uptime",
})

ALLOWED_HEALTH_STATUSES = frozenset({
    "healthy",
    "warning",
    "critical",
    "unknown",
})


def _default_system_health_log_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "system_health_log.json"
    )


@dataclass
class SystemHealthEntry:
    entry_id: str
    health_kind: str
    status: str
    recorded_by: str
    recorded_at: str
    metric_value: float | None = None
    metric_unit: str | None = None
    threshold: float | None = None
    notes: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "health_kind": self.health_kind,
            "status": self.status,
            "recorded_by": self.recorded_by,
            "recorded_at": self.recorded_at,
            "metric_value": self.metric_value,
            "metric_unit": self.metric_unit,
            "threshold": self.threshold,
            "notes": self.notes,
        }


def load_system_health_entries(
    path: Path | None = None,
) -> list[SystemHealthEntry]:
    fpath = path or _default_system_health_log_path()
    with open(fpath) as f:
        data = json.load(f)
    entries = []
    for item in data.get("entries", []):
        entries.append(SystemHealthEntry(
            entry_id=item["entry_id"],
            health_kind=item["health_kind"],
            status=item["status"],
            recorded_by=item["recorded_by"],
            recorded_at=item["recorded_at"],
            metric_value=item.get("metric_value"),
            metric_unit=item.get("metric_unit"),
            threshold=item.get("threshold"),
            notes=item.get("notes"),
        ))
    return entries


def system_health_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_system_health_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for e in entries:
        by_kind[e.health_kind] = by_kind.get(e.health_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
    return {
        "schema_version": SYSTEM_HEALTH_LOG_SCHEMA_VERSION,
        "disclaimer": SYSTEM_HEALTH_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "healthy_count": by_status.get("healthy", 0),
        "warning_count": by_status.get("warning", 0),
        "critical_count": by_status.get("critical", 0),
        "unknown_count": by_status.get("unknown", 0),
        "counts_by_kind": by_kind,
    }
