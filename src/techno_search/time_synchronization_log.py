"""Operational provenance records for time and clock synchronization events."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TIME_SYNCHRONIZATION_LOG_SCHEMA_VERSION = "time_synchronization_log_v1"

TIME_SYNCHRONIZATION_LOG_DISCLAIMER = (
    "Time synchronization entries are operational provenance records — "
    "a synchronization record does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

ALLOWED_SYNC_KINDS = frozenset(
    {
        "ntp_sync",
        "gps_sync",
        "manual_correction",
        "drift_check",
        "epoch_reset",
    }
)

ALLOWED_SYNC_STATUSES = frozenset(
    {
        "synchronized",
        "drifted",
        "failed",
        "not_required",
    }
)


@dataclass
class TimeSynchronizationEntry:
    entry_id: str
    sync_kind: str
    status: str
    recorded_by: str
    recorded_at: str
    offset_microseconds: float | None
    drift_rate_ppb: float | None
    notes: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "sync_kind": self.sync_kind,
            "status": self.status,
            "recorded_by": self.recorded_by,
            "recorded_at": self.recorded_at,
            "offset_microseconds": self.offset_microseconds,
            "drift_rate_ppb": self.drift_rate_ppb,
            "notes": self.notes,
        }


def load_time_synchronization_entries(
    path: Path | None = None,
) -> list[TimeSynchronizationEntry]:
    if path is None:
        path = (
            Path(__file__).parent.parent.parent
            / "tests"
            / "fixtures"
            / "time_synchronization_log.json"
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        TimeSynchronizationEntry(
            entry_id=e["entry_id"],
            sync_kind=e["sync_kind"],
            status=e["status"],
            recorded_by=e["recorded_by"],
            recorded_at=e["recorded_at"],
            offset_microseconds=e.get("offset_microseconds"),
            drift_rate_ppb=e.get("drift_rate_ppb"),
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def time_synchronization_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_time_synchronization_entries(path)
    counts_by_status: dict[str, int] = {}
    for e in entries:
        counts_by_status[e.status] = counts_by_status.get(e.status, 0) + 1
    counts_by_kind: dict[str, int] = {}
    for e in entries:
        counts_by_kind[e.sync_kind] = counts_by_kind.get(e.sync_kind, 0) + 1
    return {
        "schema_version": TIME_SYNCHRONIZATION_LOG_SCHEMA_VERSION,
        "disclaimer": TIME_SYNCHRONIZATION_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "synchronized_count": counts_by_status.get("synchronized", 0),
        "drifted_count": counts_by_status.get("drifted", 0),
        "failed_count": counts_by_status.get("failed", 0),
        "not_required_count": counts_by_status.get("not_required", 0),
        "counts_by_status": counts_by_status,
        "counts_by_kind": counts_by_kind,
    }
