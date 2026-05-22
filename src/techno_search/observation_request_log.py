from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

OBSERVATION_REQUEST_SCHEMA_VERSION = "observation_request_log_v1"

OBSERVATION_REQUEST_DISCLAIMER = (
    "Observation request log entries are operational scheduling records only. "
    "An observation request entry records that a follow-up observation slot was "
    "requested for a candidate in a local scheduling system. Request records are "
    "local scheduling coordination aids and do not modify candidate scores, do not "
    "affect pathway routing, do not constitute a telescope-time allocation, do not "
    "authorize external submission, and do not constitute a detection claim."
)

ALLOWED_REQUEST_KINDS = frozenset({
    "target_followup",
    "reobservation",
    "calibration_check",
    "verification",
    "archival_search",
})

ALLOWED_REQUEST_STATUSES = frozenset({
    "submitted",
    "acknowledged",
    "scheduled",
    "completed",
    "rejected",
    "withdrawn",
})


def _default_observation_request_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests" / "fixtures" / "observation_request_log.json"
    )


@dataclass
class ObservationRequestEntry:
    request_id: str
    candidate_id: str
    request_kind: str
    status: str
    requested_by: str
    requested_utc: str
    target_utc: str | None = None
    instrument: str | None = None
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "candidate_id": self.candidate_id,
            "request_kind": self.request_kind,
            "status": self.status,
            "requested_by": self.requested_by,
            "requested_utc": self.requested_utc,
            "target_utc": self.target_utc,
            "instrument": self.instrument,
            "notes": self.notes,
        }


def load_observation_request_entries(
    fixture_path: Path | None = None,
) -> list[ObservationRequestEntry]:
    path = fixture_path or _default_observation_request_path()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = []
    for raw in data.get("observation_request_entries", []):
        entries.append(ObservationRequestEntry(
            request_id=raw["request_id"],
            candidate_id=raw["candidate_id"],
            request_kind=raw["request_kind"],
            status=raw["status"],
            requested_by=raw["requested_by"],
            requested_utc=raw["requested_utc"],
            target_utc=raw.get("target_utc"),
            instrument=raw.get("instrument"),
            notes=raw.get("notes", ""),
        ))
    return entries


def observation_request_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    entries = load_observation_request_entries(fixture_path)
    by_status: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    for e in entries:
        by_status[e.status] = by_status.get(e.status, 0) + 1
        by_kind[e.request_kind] = by_kind.get(e.request_kind, 0) + 1
    pending_count = sum(
        1 for e in entries if e.status in {"submitted", "acknowledged", "scheduled"}
    )
    return {
        "schema_version": OBSERVATION_REQUEST_SCHEMA_VERSION,
        "disclaimer": OBSERVATION_REQUEST_DISCLAIMER,
        "entry_count": len(entries),
        "pending_count": pending_count,
        "completed_count": by_status.get("completed", 0),
        "rejected_count": by_status.get("rejected", 0),
        "by_status": by_status,
        "by_kind": by_kind,
    }
