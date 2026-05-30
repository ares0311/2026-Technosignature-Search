"""Operational provenance records for facility capacity planning events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CAPACITY_PLANNING_LOG_SCHEMA_VERSION = "capacity_planning_log_v1"

ALLOWED_CAPACITY_KINDS = frozenset(
    {
        "compute_capacity",
        "equipment_capacity",
        "network_capacity",
        "personnel_capacity",
        "storage_capacity",
    }
)

ALLOWED_CAPACITY_STATUSES = frozenset(
    {
        "adequate",
        "critical",
        "planned_expansion",
        "warning",
    }
)

_DISCLAIMER = (
    "Capacity planning log entries are operational provenance records — "
    "a capacity planning event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "capacity_planning_log.json"
)


@dataclass(frozen=True)
class CapacityPlanningEntry:
    entry_id: str
    capacity_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.capacity_kind not in ALLOWED_CAPACITY_KINDS:
            raise ValueError(f"Invalid capacity_kind: {self.capacity_kind!r}")
        if self.status not in ALLOWED_CAPACITY_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_capacity_planning_entries(
    path: Path | None = None,
) -> list[CapacityPlanningEntry]:
    if path is None:
        path = _DEFAULT_FIXTURE
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return [
        CapacityPlanningEntry(
            entry_id=e["entry_id"],
            capacity_kind=e["capacity_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def capacity_planning_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_capacity_planning_entries(path)
    adequate = sum(1 for e in entries if e.status == "adequate")
    return {
        "schema_version": CAPACITY_PLANNING_LOG_SCHEMA_VERSION,
        "disclaimer": _DISCLAIMER,
        "entry_count": len(entries),
        "adequate_count": adequate,
        "by_kind": {
            kind: sum(1 for e in entries if e.capacity_kind == kind)
            for kind in sorted(ALLOWED_CAPACITY_KINDS)
        },
        "by_status": {
            status: sum(1 for e in entries if e.status == status)
            for status in sorted(ALLOWED_CAPACITY_STATUSES)
        },
    }
