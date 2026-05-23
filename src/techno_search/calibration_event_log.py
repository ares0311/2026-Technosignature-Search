"""Operational processing provenance records for pipeline calibration events."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CALIBRATION_EVENT_LOG_SCHEMA_VERSION = "calibration_event_log_v1"

CALIBRATION_EVENT_LOG_DISCLAIMER = (
    "Calibration event entries are operational processing provenance records. "
    "A calibration event does not modify candidate scores or pathway routing "
    "and does not authorize external submission or constitute a detection claim."
)

ALLOWED_CALIBRATION_EVENT_KINDS = frozenset({
    "flux_calibration",
    "bandpass_calibration",
    "phase_calibration",
    "polarization_calibration",
    "pointing_calibration",
})

ALLOWED_CALIBRATION_EVENT_STATUSES = frozenset({
    "applied", "failed", "skipped", "deferred",
})


def _default_calibration_event_log_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "calibration_event_log.json"
    )


@dataclass
class CalibrationEventEntry:
    entry_id: str
    run_id: str
    event_kind: str
    status: str
    calibrated_by: str
    calibrated_at: str
    source_name: str | None = None
    notes: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "run_id": self.run_id,
            "event_kind": self.event_kind,
            "status": self.status,
            "calibrated_by": self.calibrated_by,
            "calibrated_at": self.calibrated_at,
            "source_name": self.source_name,
            "notes": self.notes,
        }


def load_calibration_event_entries(
    path: Path | None = None,
) -> list[CalibrationEventEntry]:
    fpath = path or _default_calibration_event_log_path()
    with open(fpath) as f:
        data = json.load(f)
    entries = []
    for item in data.get("calibration_event_entries", []):
        entries.append(CalibrationEventEntry(
            entry_id=item["entry_id"],
            run_id=item["run_id"],
            event_kind=item["event_kind"],
            status=item["status"],
            calibrated_by=item["calibrated_by"],
            calibrated_at=item["calibrated_at"],
            source_name=item.get("source_name"),
            notes=item.get("notes"),
        ))
    return entries


def calibration_event_log_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_calibration_event_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for e in entries:
        by_kind[e.event_kind] = by_kind.get(e.event_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
    return {
        "schema_version": CALIBRATION_EVENT_LOG_SCHEMA_VERSION,
        "disclaimer": CALIBRATION_EVENT_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "applied_count": by_status.get("applied", 0),
        "failed_count": by_status.get("failed", 0),
        "counts_by_kind": by_kind,
        "counts_by_status": by_status,
    }
