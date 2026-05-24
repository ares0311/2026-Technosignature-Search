"""Operational processing provenance records for polarization measurements."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

POLARIZATION_LOG_SCHEMA_VERSION = "polarization_log_v1"

POLARIZATION_LOG_DISCLAIMER = (
    "Polarization entries are operational processing provenance records — "
    "a polarization measurement does not modify candidate scores or pathway routing "
    "and does not authorize external submission or constitute a detection claim."
)

ALLOWED_POLARIZATION_KINDS = frozenset({
    "stokes_i", "stokes_q", "stokes_u", "stokes_v", "circular_polarization",
})

ALLOWED_POLARIZATION_STATUSES = frozenset({
    "measured", "calibrated", "flagged", "failed",
})


def _default_polarization_log_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "polarization_log.json"
    )


@dataclass
class PolarizationEntry:
    entry_id: str
    run_id: str
    polarization_kind: str
    status: str
    measured_by: str
    measured_at: str
    fractional_polarization: float | None = None
    position_angle_deg: float | None = None
    notes: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "run_id": self.run_id,
            "polarization_kind": self.polarization_kind,
            "status": self.status,
            "measured_by": self.measured_by,
            "measured_at": self.measured_at,
            "fractional_polarization": self.fractional_polarization,
            "position_angle_deg": self.position_angle_deg,
            "notes": self.notes,
        }


def load_polarization_entries(
    path: Path | None = None,
) -> list[PolarizationEntry]:
    fpath = path or _default_polarization_log_path()
    with open(fpath) as f:
        data = json.load(f)
    entries = []
    for item in data.get("polarization_entries", []):
        entries.append(PolarizationEntry(
            entry_id=item["entry_id"],
            run_id=item["run_id"],
            polarization_kind=item["polarization_kind"],
            status=item["status"],
            measured_by=item["measured_by"],
            measured_at=item["measured_at"],
            fractional_polarization=item.get("fractional_polarization"),
            position_angle_deg=item.get("position_angle_deg"),
            notes=item.get("notes"),
        ))
    return entries


def polarization_log_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_polarization_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for e in entries:
        by_kind[e.polarization_kind] = by_kind.get(e.polarization_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
    return {
        "schema_version": POLARIZATION_LOG_SCHEMA_VERSION,
        "disclaimer": POLARIZATION_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "measured_count": by_status.get("measured", 0),
        "flagged_count": by_status.get("flagged", 0),
        "counts_by_kind": by_kind,
        "counts_by_status": by_status,
    }
