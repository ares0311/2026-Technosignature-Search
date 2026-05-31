"""Operational provenance records for firmware update and rollback events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FIRMWARE_UPDATE_LOG_SCHEMA_VERSION = "firmware_update_log_v1"

ALLOWED_FIRMWARE_KINDS = frozenset(
    {
        "component_update",
        "driver_update",
        "firmware_rollback",
        "hotfix_patch",
        "scheduled_update",
    }
)

ALLOWED_FIRMWARE_STATUSES = frozenset(
    {
        "applied",
        "failed",
        "pending",
        "rolled_back",
    }
)

_DISCLAIMER = (
    "Firmware update log entries are operational provenance records — "
    "a firmware update event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "firmware_update_log.json"
)


@dataclass(frozen=True)
class FirmwareUpdateEntry:
    entry_id: str
    firmware_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.firmware_kind not in ALLOWED_FIRMWARE_KINDS:
            raise ValueError(f"Invalid firmware_kind: {self.firmware_kind!r}")
        if self.status not in ALLOWED_FIRMWARE_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_firmware_update_entries(
    path: Path | None = None,
) -> list[FirmwareUpdateEntry]:
    if path is None:
        path = _DEFAULT_FIXTURE
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return [
        FirmwareUpdateEntry(
            entry_id=e["entry_id"],
            firmware_kind=e["firmware_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def firmware_update_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_firmware_update_entries(path)
    applied = sum(1 for e in entries if e.status == "applied")
    return {
        "schema_version": FIRMWARE_UPDATE_LOG_SCHEMA_VERSION,
        "disclaimer": _DISCLAIMER,
        "entry_count": len(entries),
        "applied_count": applied,
        "by_kind": {
            kind: sum(1 for e in entries if e.firmware_kind == kind)
            for kind in sorted(ALLOWED_FIRMWARE_KINDS)
        },
        "by_status": {
            status: sum(1 for e in entries if e.status == status)
            for status in sorted(ALLOWED_FIRMWARE_STATUSES)
        },
    }
