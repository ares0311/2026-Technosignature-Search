"""Operational provenance records for compute and facility resource allocation events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

RESOURCE_ALLOCATION_LOG_SCHEMA_VERSION = "resource_allocation_log_v1"

RESOURCE_ALLOCATION_LOG_DISCLAIMER = (
    "Resource allocation log entries are operational provenance records — "
    "a resource allocation event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

ALLOWED_RESOURCE_ALLOCATION_KINDS = frozenset(
    {
        "compute_allocation",
        "memory_allocation",
        "network_allocation",
        "personnel_allocation",
        "storage_allocation",
    }
)

ALLOWED_RESOURCE_ALLOCATION_STATUSES = frozenset(
    {
        "allocated",
        "deallocated",
        "exhausted",
        "pending",
    }
)


def _default_resource_allocation_log_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "resource_allocation_log.json"
    )


@dataclass(frozen=True)
class ResourceAllocationEntry:
    entry_id: str
    allocation_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.allocation_kind not in ALLOWED_RESOURCE_ALLOCATION_KINDS:
            raise ValueError(f"Invalid allocation_kind: {self.allocation_kind!r}")
        if self.status not in ALLOWED_RESOURCE_ALLOCATION_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_resource_allocation_entries(
    path: Path | None = None,
) -> list[ResourceAllocationEntry]:
    fpath = path or _default_resource_allocation_log_path()
    raw: dict[str, Any] = json.loads(fpath.read_text(encoding="utf-8"))
    return [
        ResourceAllocationEntry(
            entry_id=e["entry_id"],
            allocation_kind=e["allocation_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def resource_allocation_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_resource_allocation_entries(path)
    allocated = sum(1 for e in entries if e.status == "allocated")
    return {
        "schema_version": RESOURCE_ALLOCATION_LOG_SCHEMA_VERSION,
        "disclaimer": RESOURCE_ALLOCATION_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "allocated_count": allocated,
        "by_kind": {
            kind: sum(1 for e in entries if e.allocation_kind == kind)
            for kind in sorted(ALLOWED_RESOURCE_ALLOCATION_KINDS)
        },
        "by_status": {
            status: sum(1 for e in entries if e.status == status)
            for status in sorted(ALLOWED_RESOURCE_ALLOCATION_STATUSES)
        },
    }
