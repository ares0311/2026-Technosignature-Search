"""Operational provenance records for individual telescope scan events."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCAN_LOG_SCHEMA_VERSION = "scan_log_v1"

SCAN_LOG_DISCLAIMER = (
    "Scan log entries are operational provenance records — "
    "a scan record does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

ALLOWED_SCAN_KINDS = frozenset(
    {
        "on_source",
        "off_source",
        "calibrator",
        "reference_position",
        "slew",
    }
)

ALLOWED_SCAN_STATUSES = frozenset(
    {
        "completed",
        "aborted",
        "flagged",
        "pending",
    }
)


@dataclass
class ScanEntry:
    entry_id: str
    scan_kind: str
    status: str
    recorded_by: str
    scan_start: str
    track: str
    scan_duration_seconds: float | None
    target_name: str | None
    notes: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "scan_kind": self.scan_kind,
            "status": self.status,
            "recorded_by": self.recorded_by,
            "scan_start": self.scan_start,
            "track": self.track,
            "scan_duration_seconds": self.scan_duration_seconds,
            "target_name": self.target_name,
            "notes": self.notes,
        }


def load_scan_entries(path: Path | None = None) -> list[ScanEntry]:
    if path is None:
        path = (
            Path(__file__).parent.parent.parent
            / "tests"
            / "fixtures"
            / "scan_log.json"
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        ScanEntry(
            entry_id=e["entry_id"],
            scan_kind=e["scan_kind"],
            status=e["status"],
            recorded_by=e["recorded_by"],
            scan_start=e["scan_start"],
            track=e["track"],
            scan_duration_seconds=e.get("scan_duration_seconds"),
            target_name=e.get("target_name"),
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def scan_log_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_scan_entries(path)
    counts_by_status: dict[str, int] = {}
    for e in entries:
        counts_by_status[e.status] = counts_by_status.get(e.status, 0) + 1
    counts_by_kind: dict[str, int] = {}
    for e in entries:
        counts_by_kind[e.scan_kind] = counts_by_kind.get(e.scan_kind, 0) + 1
    return {
        "schema_version": SCAN_LOG_SCHEMA_VERSION,
        "disclaimer": SCAN_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "completed_count": counts_by_status.get("completed", 0),
        "aborted_count": counts_by_status.get("aborted", 0),
        "flagged_count": counts_by_status.get("flagged", 0),
        "pending_count": counts_by_status.get("pending", 0),
        "counts_by_status": counts_by_status,
        "counts_by_kind": counts_by_kind,
    }
