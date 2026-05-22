from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DATA_GAP_SCHEMA_VERSION = "data_gap_log_v1"

DATA_GAP_DISCLAIMER = (
    "Data gap log entries are operational scheduling records only. "
    "A data gap entry records that an expected observation or data delivery was "
    "missing or incomplete due to instrument downtime, weather, scheduling conflicts, "
    "or data quality failures. Gap records are scheduling coordination aids and do "
    "not modify candidate scores, do not affect pathway routing, do not identify "
    "missing technosignatures, do not authorize external submission, and do not "
    "constitute a detection claim."
)

ALLOWED_MISSING_REASONS = frozenset({
    "instrument_downtime", "weather", "scheduling_conflict",
    "data_quality_failure", "unknown",
})

ALLOWED_GAP_STATUSES = frozenset({
    "identified", "under_investigation", "resolved", "accepted",
})


def _default_data_gap_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests" / "fixtures" / "data_gap_log.json"
    )


@dataclass
class DataGapEntry:
    gap_id: str
    track: str
    missing_reason: str
    status: str
    expected_utc: str
    reported_by: str
    reported_utc: str
    resolved_utc: str | None = None
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "gap_id": self.gap_id,
            "track": self.track,
            "missing_reason": self.missing_reason,
            "status": self.status,
            "expected_utc": self.expected_utc,
            "reported_by": self.reported_by,
            "reported_utc": self.reported_utc,
            "resolved_utc": self.resolved_utc,
            "notes": self.notes,
        }


def load_data_gap_entries(fixture_path: Path | None = None) -> list[DataGapEntry]:
    path = fixture_path or _default_data_gap_path()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = []
    for raw in data.get("data_gap_entries", []):
        entries.append(DataGapEntry(
            gap_id=raw["gap_id"],
            track=raw["track"],
            missing_reason=raw["missing_reason"],
            status=raw["status"],
            expected_utc=raw["expected_utc"],
            reported_by=raw["reported_by"],
            reported_utc=raw["reported_utc"],
            resolved_utc=raw.get("resolved_utc"),
            notes=raw.get("notes", ""),
        ))
    return entries


def data_gap_summary(fixture_path: Path | None = None) -> dict[str, Any]:
    entries = load_data_gap_entries(fixture_path)
    by_status: dict[str, int] = {}
    by_reason: dict[str, int] = {}
    for e in entries:
        by_status[e.status] = by_status.get(e.status, 0) + 1
        by_reason[e.missing_reason] = by_reason.get(e.missing_reason, 0) + 1
    unresolved_count = sum(
        1 for e in entries if e.status in {"identified", "under_investigation"}
    )
    return {
        "schema_version": DATA_GAP_SCHEMA_VERSION,
        "disclaimer": DATA_GAP_DISCLAIMER,
        "entry_count": len(entries),
        "unresolved_count": unresolved_count,
        "resolved_count": by_status.get("resolved", 0),
        "accepted_count": by_status.get("accepted", 0),
        "by_status": by_status,
        "by_reason": by_reason,
    }
