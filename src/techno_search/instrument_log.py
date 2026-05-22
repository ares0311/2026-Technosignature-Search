"""Operational records for instrument/telescope status events."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

INSTRUMENT_LOG_SCHEMA_VERSION = "instrument_log_v1"

INSTRUMENT_LOG_DISCLAIMER = (
    "Instrument log entries are operational scheduling records. "
    "Instrument status does not modify candidate scores or pathway routing "
    "and does not authorize external submission or constitute a detection claim."
)

ALLOWED_INSTRUMENT_KINDS = frozenset({
    "radio_telescope", "optical_telescope", "archive_node", "data_pipeline",
})

ALLOWED_EVENT_KINDS = frozenset({
    "online", "offline", "degraded", "maintenance", "calibrating",
})


def _default_instrument_log_path() -> Path:
    return Path(__file__).parent.parent.parent / "tests" / "fixtures" / "instrument_log.json"


@dataclass
class InstrumentLogEntry:
    log_id: str
    instrument_id: str
    instrument_kind: str
    event_kind: str
    reported_by: str
    reported_utc: str
    resolved_utc: str | None = None
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "log_id": self.log_id,
            "instrument_id": self.instrument_id,
            "instrument_kind": self.instrument_kind,
            "event_kind": self.event_kind,
            "reported_by": self.reported_by,
            "reported_utc": self.reported_utc,
            "resolved_utc": self.resolved_utc,
            "notes": self.notes,
        }


def load_instrument_log_entries(path: Path | None = None) -> list[InstrumentLogEntry]:
    fpath = path or _default_instrument_log_path()
    with open(fpath) as f:
        data = json.load(f)
    entries = []
    for item in data.get("instrument_log_entries", []):
        entries.append(InstrumentLogEntry(
            log_id=item["log_id"],
            instrument_id=item["instrument_id"],
            instrument_kind=item["instrument_kind"],
            event_kind=item["event_kind"],
            reported_by=item["reported_by"],
            reported_utc=item["reported_utc"],
            resolved_utc=item.get("resolved_utc"),
            notes=item.get("notes", ""),
        ))
    return entries


def instrument_log_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_instrument_log_entries(path)
    by_event_kind: dict[str, int] = {}
    by_instrument_kind: dict[str, int] = {}
    for e in entries:
        by_event_kind[e.event_kind] = by_event_kind.get(e.event_kind, 0) + 1
        by_instrument_kind[e.instrument_kind] = by_instrument_kind.get(e.instrument_kind, 0) + 1
    return {
        "schema_version": INSTRUMENT_LOG_SCHEMA_VERSION,
        "disclaimer": INSTRUMENT_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "online_count": by_event_kind.get("online", 0),
        "degraded_count": by_event_kind.get("degraded", 0),
        "offline_count": by_event_kind.get("offline", 0),
        "maintenance_count": by_event_kind.get("maintenance", 0),
        "calibrating_count": by_event_kind.get("calibrating", 0),
        "by_event_kind": by_event_kind,
        "by_instrument_kind": by_instrument_kind,
    }
