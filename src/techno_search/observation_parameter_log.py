"""Operational processing provenance records for observation configuration parameters."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

OBSERVATION_PARAMETER_LOG_SCHEMA_VERSION = "observation_parameter_log_v1"

OBSERVATION_PARAMETER_LOG_DISCLAIMER = (
    "Observation parameter entries are operational processing provenance records — "
    "a parameter record does not modify candidate scores or pathway routing "
    "and does not authorize external submission or constitute a detection claim."
)

ALLOWED_PARAMETER_KINDS = frozenset({
    "integration_time", "bandwidth", "center_frequency",
    "resolution", "sensitivity_target",
})

ALLOWED_PARAMETER_STATUSES = frozenset({
    "applied", "overridden", "flagged", "failed",
})


def _default_observation_parameter_log_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "observation_parameter_log.json"
    )


@dataclass
class ObservationParameterEntry:
    entry_id: str
    run_id: str
    parameter_kind: str
    status: str
    set_by: str
    set_at: str
    value: float | None = None
    unit: str | None = None
    notes: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "run_id": self.run_id,
            "parameter_kind": self.parameter_kind,
            "status": self.status,
            "set_by": self.set_by,
            "set_at": self.set_at,
            "value": self.value,
            "unit": self.unit,
            "notes": self.notes,
        }


def load_observation_parameter_entries(
    path: Path | None = None,
) -> list[ObservationParameterEntry]:
    fpath = path or _default_observation_parameter_log_path()
    with open(fpath) as f:
        data = json.load(f)
    entries = []
    for item in data.get("observation_parameter_entries", []):
        entries.append(ObservationParameterEntry(
            entry_id=item["entry_id"],
            run_id=item["run_id"],
            parameter_kind=item["parameter_kind"],
            status=item["status"],
            set_by=item["set_by"],
            set_at=item["set_at"],
            value=item.get("value"),
            unit=item.get("unit"),
            notes=item.get("notes"),
        ))
    return entries


def observation_parameter_log_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_observation_parameter_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for e in entries:
        by_kind[e.parameter_kind] = by_kind.get(e.parameter_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
    return {
        "schema_version": OBSERVATION_PARAMETER_LOG_SCHEMA_VERSION,
        "disclaimer": OBSERVATION_PARAMETER_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "applied_count": by_status.get("applied", 0),
        "flagged_count": by_status.get("flagged", 0),
        "counts_by_kind": by_kind,
        "counts_by_status": by_status,
    }
