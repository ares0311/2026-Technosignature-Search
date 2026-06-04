"""Operational provenance records for change management events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CHANGE_MANAGEMENT_LOG_SCHEMA_VERSION = "change_management_log_v1"
CHANGE_MANAGEMENT_LOG_DISCLAIMER = (
    "Change management log entries are operational provenance records — "
    "a change management event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)
ALLOWED_CHANGE_MANAGEMENT_KINDS = frozenset(
    {
        "configuration_change",
        "emergency_change",
        "planned_change",
        "rollback",
        "service_change",
    }
)
ALLOWED_CHANGE_MANAGEMENT_STATUSES = frozenset(
    {
        "approved",
        "completed",
        "pending",
        "rejected",
    }
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "change_management_log.json"
)


@dataclass(frozen=True)
class ChangeManagementEntry:
    entry_id: str
    change_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.change_kind not in ALLOWED_CHANGE_MANAGEMENT_KINDS:
            raise ValueError(f"Invalid change_kind: {self.change_kind!r}")
        if self.status not in ALLOWED_CHANGE_MANAGEMENT_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_change_management_entries(path: Path | None = None) -> list[ChangeManagementEntry]:
    fixture_path = path if path is not None else _DEFAULT_FIXTURE
    raw = json.loads(Path(fixture_path).read_text())
    return [
        ChangeManagementEntry(
            entry_id=e["entry_id"],
            change_kind=e["change_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def change_management_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_change_management_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    completed_count = 0
    for e in entries:
        by_kind[e.change_kind] = by_kind.get(e.change_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
        if e.status == "completed":
            completed_count += 1
    return {
        "schema_version": CHANGE_MANAGEMENT_LOG_SCHEMA_VERSION,
        "disclaimer": CHANGE_MANAGEMENT_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "completed_count": completed_count,
        "by_kind": by_kind,
        "by_status": by_status,
    }
