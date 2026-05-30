"""Operational provenance records for facility performance monitoring events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PERFORMANCE_MONITORING_LOG_SCHEMA_VERSION = "performance_monitoring_log_v1"

ALLOWED_PERFORMANCE_KINDS = frozenset(
    {
        "cpu_utilization",
        "disk_io",
        "memory_utilization",
        "network_throughput",
        "response_time",
    }
)

ALLOWED_PERFORMANCE_STATUSES = frozenset(
    {
        "alert",
        "critical",
        "degraded",
        "normal",
    }
)

_DISCLAIMER = (
    "Performance monitoring log entries are operational provenance records — "
    "a performance monitoring event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "performance_monitoring_log.json"
)


@dataclass(frozen=True)
class PerformanceMonitoringEntry:
    entry_id: str
    performance_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.performance_kind not in ALLOWED_PERFORMANCE_KINDS:
            raise ValueError(f"Invalid performance_kind: {self.performance_kind!r}")
        if self.status not in ALLOWED_PERFORMANCE_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_performance_monitoring_entries(
    path: Path | None = None,
) -> list[PerformanceMonitoringEntry]:
    if path is None:
        path = _DEFAULT_FIXTURE
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return [
        PerformanceMonitoringEntry(
            entry_id=e["entry_id"],
            performance_kind=e["performance_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def performance_monitoring_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_performance_monitoring_entries(path)
    normal = sum(1 for e in entries if e.status == "normal")
    return {
        "schema_version": PERFORMANCE_MONITORING_LOG_SCHEMA_VERSION,
        "disclaimer": _DISCLAIMER,
        "entry_count": len(entries),
        "normal_count": normal,
        "by_kind": {
            kind: sum(1 for e in entries if e.performance_kind == kind)
            for kind in sorted(ALLOWED_PERFORMANCE_KINDS)
        },
        "by_status": {
            status: sum(1 for e in entries if e.status == status)
            for status in sorted(ALLOWED_PERFORMANCE_STATUSES)
        },
    }
