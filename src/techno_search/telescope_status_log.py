"""Operational scheduling provenance records for telescope operational status."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

TELESCOPE_STATUS_LOG_SCHEMA_VERSION = "telescope_status_log_v1"

TELESCOPE_STATUS_LOG_DISCLAIMER = (
    "Telescope status entries are operational scheduling provenance records — "
    "a telescope status does not modify candidate scores or pathway routing "
    "and does not authorize external submission or constitute a detection claim."
)

ALLOWED_TELESCOPE_STATUS_KINDS = frozenset({
    "operational", "maintenance", "degraded", "offline", "commissioning",
})

ALLOWED_TELESCOPE_STATUS_STATUSES = frozenset({
    "recorded", "updated", "superseded", "error",
})


def _default_telescope_status_log_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "telescope_status_log.json"
    )


@dataclass
class TelescopeStatusEntry:
    entry_id: str
    run_id: str
    status_kind: str
    status: str
    recorded_by: str
    recorded_at: str
    telescope_id: str | None = None
    affected_tracks: list[str] = field(default_factory=list)
    notes: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "run_id": self.run_id,
            "status_kind": self.status_kind,
            "status": self.status,
            "recorded_by": self.recorded_by,
            "recorded_at": self.recorded_at,
            "telescope_id": self.telescope_id,
            "affected_tracks": self.affected_tracks,
            "notes": self.notes,
        }


def load_telescope_status_entries(
    path: Path | None = None,
) -> list[TelescopeStatusEntry]:
    fpath = path or _default_telescope_status_log_path()
    with open(fpath) as f:
        data = json.load(f)
    entries = []
    for item in data.get("telescope_status_entries", []):
        entries.append(TelescopeStatusEntry(
            entry_id=item["entry_id"],
            run_id=item["run_id"],
            status_kind=item["status_kind"],
            status=item["status"],
            recorded_by=item["recorded_by"],
            recorded_at=item["recorded_at"],
            telescope_id=item.get("telescope_id"),
            affected_tracks=item.get("affected_tracks") or [],
            notes=item.get("notes"),
        ))
    return entries


def telescope_status_log_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_telescope_status_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for e in entries:
        by_kind[e.status_kind] = by_kind.get(e.status_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
    return {
        "schema_version": TELESCOPE_STATUS_LOG_SCHEMA_VERSION,
        "disclaimer": TELESCOPE_STATUS_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "recorded_count": by_status.get("recorded", 0),
        "operational_count": by_kind.get("operational", 0),
        "counts_by_kind": by_kind,
        "counts_by_status": by_status,
    }
