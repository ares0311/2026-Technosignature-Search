"""Operational provenance records for facility software and firmware update events."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SOFTWARE_UPDATE_LOG_SCHEMA_VERSION = "software_update_log_v1"

SOFTWARE_UPDATE_LOG_DISCLAIMER = (
    "Software update log entries are operational provenance records — "
    "a software update record does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

ALLOWED_UPDATE_KINDS = frozenset(
    {
        "pipeline_update",
        "firmware_update",
        "os_patch",
        "driver_update",
        "config_deploy",
    }
)

ALLOWED_UPDATE_STATUSES = frozenset(
    {
        "deployed",
        "failed",
        "rolled_back",
        "pending",
    }
)


@dataclass
class SoftwareUpdateEntry:
    entry_id: str
    update_kind: str
    status: str
    recorded_by: str
    timestamp_utc: str
    component_id: str | None
    version_tag: str | None
    notes: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "update_kind": self.update_kind,
            "status": self.status,
            "recorded_by": self.recorded_by,
            "timestamp_utc": self.timestamp_utc,
            "component_id": self.component_id,
            "version_tag": self.version_tag,
            "notes": self.notes,
        }


def load_software_update_entries(path: Path | None = None) -> list[SoftwareUpdateEntry]:
    if path is None:
        path = (
            Path(__file__).parent.parent.parent
            / "tests"
            / "fixtures"
            / "software_update_log.json"
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        SoftwareUpdateEntry(
            entry_id=e["entry_id"],
            update_kind=e["update_kind"],
            status=e["status"],
            recorded_by=e["recorded_by"],
            timestamp_utc=e["timestamp_utc"],
            component_id=e.get("component_id"),
            version_tag=e.get("version_tag"),
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def software_update_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_software_update_entries(path)
    counts_by_status: dict[str, int] = {}
    for e in entries:
        counts_by_status[e.status] = counts_by_status.get(e.status, 0) + 1
    counts_by_kind: dict[str, int] = {}
    for e in entries:
        counts_by_kind[e.update_kind] = counts_by_kind.get(e.update_kind, 0) + 1
    return {
        "schema_version": SOFTWARE_UPDATE_LOG_SCHEMA_VERSION,
        "disclaimer": SOFTWARE_UPDATE_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "deployed_count": counts_by_status.get("deployed", 0),
        "failed_count": counts_by_status.get("failed", 0),
        "rolled_back_count": counts_by_status.get("rolled_back", 0),
        "pending_count": counts_by_status.get("pending", 0),
        "counts_by_status": counts_by_status,
        "counts_by_kind": counts_by_kind,
    }
