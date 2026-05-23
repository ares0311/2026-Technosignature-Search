"""Operational processing provenance records for radio telescope beam configuration."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BEAM_CONFIGURATION_LOG_SCHEMA_VERSION = "beam_configuration_log_v1"

BEAM_CONFIGURATION_LOG_DISCLAIMER = (
    "Beam configuration entries are operational processing provenance records. "
    "Beam configuration does not modify candidate scores or pathway routing "
    "and does not authorize external submission or constitute a detection claim."
)

ALLOWED_BEAM_KINDS = frozenset({
    "primary_beam", "sidelobe", "calibrator_beam", "off_source", "synthetic_beam",
})

ALLOWED_BEAM_STATUSES = frozenset({
    "configured", "applied", "superseded", "failed",
})


def _default_beam_configuration_log_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "beam_configuration_log.json"
    )


@dataclass
class BeamConfigurationEntry:
    entry_id: str
    candidate_id: str
    beam_kind: str
    status: str
    configured_by: str
    configured_at: str
    track: str
    azimuth_deg: float | None = None
    elevation_deg: float | None = None
    notes: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "candidate_id": self.candidate_id,
            "beam_kind": self.beam_kind,
            "status": self.status,
            "configured_by": self.configured_by,
            "configured_at": self.configured_at,
            "track": self.track,
            "azimuth_deg": self.azimuth_deg,
            "elevation_deg": self.elevation_deg,
            "notes": self.notes,
        }


def load_beam_configuration_entries(
    path: Path | None = None,
) -> list[BeamConfigurationEntry]:
    fpath = path or _default_beam_configuration_log_path()
    with open(fpath) as f:
        data = json.load(f)
    entries = []
    for item in data.get("beam_configuration_entries", []):
        entries.append(BeamConfigurationEntry(
            entry_id=item["entry_id"],
            candidate_id=item["candidate_id"],
            beam_kind=item["beam_kind"],
            status=item["status"],
            configured_by=item["configured_by"],
            configured_at=item["configured_at"],
            track=item["track"],
            azimuth_deg=item.get("azimuth_deg"),
            elevation_deg=item.get("elevation_deg"),
            notes=item.get("notes"),
        ))
    return entries


def beam_configuration_log_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_beam_configuration_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for e in entries:
        by_kind[e.beam_kind] = by_kind.get(e.beam_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
    return {
        "schema_version": BEAM_CONFIGURATION_LOG_SCHEMA_VERSION,
        "disclaimer": BEAM_CONFIGURATION_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "applied_count": by_status.get("applied", 0),
        "configured_count": by_status.get("configured", 0),
        "counts_by_kind": by_kind,
        "counts_by_status": by_status,
    }
