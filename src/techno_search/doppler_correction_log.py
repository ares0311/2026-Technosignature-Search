"""Operational processing provenance records for Doppler correction events."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DOPPLER_CORRECTION_LOG_SCHEMA_VERSION = "doppler_correction_log_v1"

DOPPLER_CORRECTION_LOG_DISCLAIMER = (
    "Doppler correction entries are operational processing provenance records — "
    "a correction does not modify candidate scores or pathway routing, "
    "does not authorize external submission, "
    "and does not constitute a detection claim."
)

ALLOWED_DOPPLER_CORRECTION_KINDS = frozenset({
    "barycentric",
    "topocentric",
    "heliocentric",
    "observatory_frame",
    "rest_frame",
})

ALLOWED_DOPPLER_CORRECTION_STATUSES = frozenset({
    "applied",
    "failed",
    "not_applicable",
    "flagged",
})


def _default_doppler_correction_log_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "doppler_correction_log.json"
    )


@dataclass
class DopplerCorrectionEntry:
    entry_id: str
    candidate_id: str
    track: str
    correction_kind: str
    status: str
    applied_by: str
    applied_at: str
    correction_hz: float | None = None
    reference_frame: str | None = None
    notes: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "candidate_id": self.candidate_id,
            "track": self.track,
            "correction_kind": self.correction_kind,
            "status": self.status,
            "applied_by": self.applied_by,
            "applied_at": self.applied_at,
            "correction_hz": self.correction_hz,
            "reference_frame": self.reference_frame,
            "notes": self.notes,
        }


def load_doppler_correction_entries(
    path: Path | None = None,
) -> list[DopplerCorrectionEntry]:
    fpath = path or _default_doppler_correction_log_path()
    with open(fpath) as f:
        data = json.load(f)
    entries = []
    for item in data.get("entries", []):
        entries.append(DopplerCorrectionEntry(
            entry_id=item["entry_id"],
            candidate_id=item["candidate_id"],
            track=item["track"],
            correction_kind=item["correction_kind"],
            status=item["status"],
            applied_by=item["applied_by"],
            applied_at=item["applied_at"],
            correction_hz=item.get("correction_hz"),
            reference_frame=item.get("reference_frame"),
            notes=item.get("notes"),
        ))
    return entries


def doppler_correction_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_doppler_correction_entries(path)
    by_kind: dict[str, int] = {}
    by_track: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for e in entries:
        by_kind[e.correction_kind] = by_kind.get(e.correction_kind, 0) + 1
        by_track[e.track] = by_track.get(e.track, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
    return {
        "schema_version": DOPPLER_CORRECTION_LOG_SCHEMA_VERSION,
        "disclaimer": DOPPLER_CORRECTION_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "applied_count": by_status.get("applied", 0),
        "failed_count": by_status.get("failed", 0),
        "not_applicable_count": by_status.get("not_applicable", 0),
        "flagged_count": by_status.get("flagged", 0),
        "counts_by_kind": by_kind,
        "counts_by_track": by_track,
    }
