"""Operational provenance records for structured change management events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CHANGE_MANAGEMENT_LOG_SCHEMA_VERSION = "change_management_log_v1"

ALLOWED_CHANGE_KINDS = frozenset(
    {
        "approval_request",
        "emergency_change",
        "planned_change",
        "rejection",
        "rollback",
    }
)

ALLOWED_CHANGE_STATUSES = frozenset(
    {
        "approved",
        "implemented",
        "requested",
        "rolled_back",
    }
)

_DISCLAIMER = (
    "Change management log entries are operational provenance records — "
    "a change management event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
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
        if self.change_kind not in ALLOWED_CHANGE_KINDS:
            raise ValueError(f"Invalid change_kind: {self.change_kind!r}")
        if self.status not in ALLOWED_CHANGE_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_change_management_entries(
    path: Path | None = None,
) -> list[ChangeManagementEntry]:
    if path is None:
        path = _DEFAULT_FIXTURE
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
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
    implemented = sum(1 for e in entries if e.status == "implemented")
    return {
        "schema_version": CHANGE_MANAGEMENT_LOG_SCHEMA_VERSION,
        "disclaimer": _DISCLAIMER,
        "entry_count": len(entries),
        "implemented_count": implemented,
        "by_kind": {
            kind: sum(1 for e in entries if e.change_kind == kind)
            for kind in sorted(ALLOWED_CHANGE_KINDS)
        },
        "by_status": {
            status: sum(1 for e in entries if e.status == status)
            for status in sorted(ALLOWED_CHANGE_STATUSES)
        },
    }
