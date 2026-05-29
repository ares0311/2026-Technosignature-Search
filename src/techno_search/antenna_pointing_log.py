"""Operational provenance records for antenna pointing events."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ANTENNA_POINTING_LOG_SCHEMA_VERSION = "antenna_pointing_log_v1"

ANTENNA_POINTING_LOG_DISCLAIMER = (
    "Antenna pointing log entries are operational provenance records — "
    "a pointing record does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

ALLOWED_POINTING_KINDS = frozenset(
    {
        "target_slew",
        "park_position",
        "stow_position",
        "tracking_start",
        "tracking_end",
    }
)

ALLOWED_POINTING_STATUSES = frozenset(
    {
        "completed",
        "failed",
        "timeout",
        "cancelled",
    }
)


@dataclass
class AntennaPointingEntry:
    entry_id: str
    pointing_kind: str
    status: str
    recorded_by: str
    timestamp_utc: str
    target_id: str | None
    azimuth_deg: float | None
    elevation_deg: float | None
    notes: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "pointing_kind": self.pointing_kind,
            "status": self.status,
            "recorded_by": self.recorded_by,
            "timestamp_utc": self.timestamp_utc,
            "target_id": self.target_id,
            "azimuth_deg": self.azimuth_deg,
            "elevation_deg": self.elevation_deg,
            "notes": self.notes,
        }


def load_antenna_pointing_entries(path: Path | None = None) -> list[AntennaPointingEntry]:
    if path is None:
        path = (
            Path(__file__).parent.parent.parent
            / "tests"
            / "fixtures"
            / "antenna_pointing_log.json"
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        AntennaPointingEntry(
            entry_id=e["entry_id"],
            pointing_kind=e["pointing_kind"],
            status=e["status"],
            recorded_by=e["recorded_by"],
            timestamp_utc=e["timestamp_utc"],
            target_id=e.get("target_id"),
            azimuth_deg=e.get("azimuth_deg"),
            elevation_deg=e.get("elevation_deg"),
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def antenna_pointing_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_antenna_pointing_entries(path)
    counts_by_status: dict[str, int] = {}
    for e in entries:
        counts_by_status[e.status] = counts_by_status.get(e.status, 0) + 1
    counts_by_kind: dict[str, int] = {}
    for e in entries:
        counts_by_kind[e.pointing_kind] = counts_by_kind.get(e.pointing_kind, 0) + 1
    return {
        "schema_version": ANTENNA_POINTING_LOG_SCHEMA_VERSION,
        "disclaimer": ANTENNA_POINTING_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "completed_count": counts_by_status.get("completed", 0),
        "failed_count": counts_by_status.get("failed", 0),
        "timeout_count": counts_by_status.get("timeout", 0),
        "cancelled_count": counts_by_status.get("cancelled", 0),
        "counts_by_status": counts_by_status,
        "counts_by_kind": counts_by_kind,
    }
