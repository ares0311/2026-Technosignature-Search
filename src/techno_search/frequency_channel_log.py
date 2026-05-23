"""Operational processing provenance records for frequency channel configuration."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FREQUENCY_CHANNEL_LOG_SCHEMA_VERSION = "frequency_channel_log_v1"

FREQUENCY_CHANNEL_LOG_DISCLAIMER = (
    "Frequency channel entries are operational processing provenance records. "
    "Channel configuration does not modify candidate scores or pathway routing "
    "and does not authorize external submission or constitute a detection claim."
)

ALLOWED_CHANNEL_KINDS = frozenset({
    "primary", "backup", "rfi_free", "reserved", "calibration",
})

ALLOWED_CHANNEL_STATUSES = frozenset({
    "active", "flagged", "reserved", "disabled",
})


def _default_frequency_channel_log_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "frequency_channel_log.json"
    )


@dataclass
class FrequencyChannelEntry:
    entry_id: str
    candidate_id: str
    channel_kind: str
    status: str
    frequency_mhz: float
    recorded_by: str
    recorded_at: str
    track: str
    bandwidth_mhz: float | None = None
    notes: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "candidate_id": self.candidate_id,
            "channel_kind": self.channel_kind,
            "status": self.status,
            "frequency_mhz": self.frequency_mhz,
            "recorded_by": self.recorded_by,
            "recorded_at": self.recorded_at,
            "track": self.track,
            "bandwidth_mhz": self.bandwidth_mhz,
            "notes": self.notes,
        }


def load_frequency_channel_entries(
    path: Path | None = None,
) -> list[FrequencyChannelEntry]:
    fpath = path or _default_frequency_channel_log_path()
    with open(fpath) as f:
        data = json.load(f)
    entries = []
    for item in data.get("frequency_channel_entries", []):
        entries.append(FrequencyChannelEntry(
            entry_id=item["entry_id"],
            candidate_id=item["candidate_id"],
            channel_kind=item["channel_kind"],
            status=item["status"],
            frequency_mhz=item["frequency_mhz"],
            recorded_by=item["recorded_by"],
            recorded_at=item["recorded_at"],
            track=item["track"],
            bandwidth_mhz=item.get("bandwidth_mhz"),
            notes=item.get("notes"),
        ))
    return entries


def frequency_channel_log_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_frequency_channel_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for e in entries:
        by_kind[e.channel_kind] = by_kind.get(e.channel_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
    return {
        "schema_version": FREQUENCY_CHANNEL_LOG_SCHEMA_VERSION,
        "disclaimer": FREQUENCY_CHANNEL_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "active_count": by_status.get("active", 0),
        "flagged_count": by_status.get("flagged", 0),
        "counts_by_kind": by_kind,
        "counts_by_status": by_status,
    }
