"""Operational provenance records for storage lifecycle events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

STORAGE_MANAGEMENT_LOG_SCHEMA_VERSION = "storage_management_log_v1"

ALLOWED_STORAGE_KINDS = frozenset(
    {
        "allocation",
        "cleanup",
        "deallocation",
        "migration",
        "quota_change",
    }
)

ALLOWED_STORAGE_STATUSES = frozenset(
    {
        "completed",
        "failed",
        "in_progress",
        "pending",
    }
)

_DISCLAIMER = (
    "Storage management log entries are operational provenance records — "
    "a storage management event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "storage_management_log.json"
)


@dataclass(frozen=True)
class StorageManagementEntry:
    entry_id: str
    storage_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.storage_kind not in ALLOWED_STORAGE_KINDS:
            raise ValueError(f"Invalid storage_kind: {self.storage_kind!r}")
        if self.status not in ALLOWED_STORAGE_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_storage_management_entries(
    path: Path | None = None,
) -> list[StorageManagementEntry]:
    if path is None:
        path = _DEFAULT_FIXTURE
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return [
        StorageManagementEntry(
            entry_id=e["entry_id"],
            storage_kind=e["storage_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def storage_management_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_storage_management_entries(path)
    completed = sum(1 for e in entries if e.status == "completed")
    return {
        "schema_version": STORAGE_MANAGEMENT_LOG_SCHEMA_VERSION,
        "disclaimer": _DISCLAIMER,
        "entry_count": len(entries),
        "completed_count": completed,
        "by_kind": {
            kind: sum(1 for e in entries if e.storage_kind == kind)
            for kind in sorted(ALLOWED_STORAGE_KINDS)
        },
        "by_status": {
            status: sum(1 for e in entries if e.status == status)
            for status in sorted(ALLOWED_STORAGE_STATUSES)
        },
    }
