"""Operational processing provenance records for pipeline noise and sensitivity measurements."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

NOISE_MEASUREMENT_LOG_SCHEMA_VERSION = "noise_measurement_log_v1"

NOISE_MEASUREMENT_LOG_DISCLAIMER = (
    "Noise measurement entries are operational processing provenance records — "
    "a noise measurement does not modify candidate scores or pathway routing "
    "and does not authorize external submission or constitute a detection claim."
)

ALLOWED_MEASUREMENT_KINDS = frozenset({
    "system_temperature", "noise_floor", "rms_baseline",
    "sensitivity_estimate", "interference_level",
})

ALLOWED_MEASUREMENT_STATUSES = frozenset({
    "recorded", "flagged", "superseded", "failed",
})


def _default_noise_measurement_log_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "noise_measurement_log.json"
    )


@dataclass
class NoiseMeasurementEntry:
    entry_id: str
    run_id: str
    measurement_kind: str
    status: str
    measured_by: str
    measured_at: str
    value: float | None = None
    unit: str | None = None
    notes: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "run_id": self.run_id,
            "measurement_kind": self.measurement_kind,
            "status": self.status,
            "measured_by": self.measured_by,
            "measured_at": self.measured_at,
            "value": self.value,
            "unit": self.unit,
            "notes": self.notes,
        }


def load_noise_measurement_entries(
    path: Path | None = None,
) -> list[NoiseMeasurementEntry]:
    fpath = path or _default_noise_measurement_log_path()
    with open(fpath) as f:
        data = json.load(f)
    entries = []
    for item in data.get("noise_measurement_entries", []):
        entries.append(NoiseMeasurementEntry(
            entry_id=item["entry_id"],
            run_id=item["run_id"],
            measurement_kind=item["measurement_kind"],
            status=item["status"],
            measured_by=item["measured_by"],
            measured_at=item["measured_at"],
            value=item.get("value"),
            unit=item.get("unit"),
            notes=item.get("notes"),
        ))
    return entries


def noise_measurement_log_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_noise_measurement_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for e in entries:
        by_kind[e.measurement_kind] = by_kind.get(e.measurement_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
    return {
        "schema_version": NOISE_MEASUREMENT_LOG_SCHEMA_VERSION,
        "disclaimer": NOISE_MEASUREMENT_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "recorded_count": by_status.get("recorded", 0),
        "flagged_count": by_status.get("flagged", 0),
        "counts_by_kind": by_kind,
        "counts_by_status": by_status,
    }
