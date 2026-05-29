"""Operational processing provenance records for interference environment assessments."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

INTERFERENCE_ENVIRONMENT_LOG_SCHEMA_VERSION = "interference_environment_log_v1"

INTERFERENCE_ENVIRONMENT_LOG_DISCLAIMER = (
    "Interference environment entries are operational processing provenance records — "
    "an assessment does not modify candidate scores or pathway routing, "
    "does not authorize external submission, "
    "and does not constitute a detection claim."
)

ALLOWED_INTERFERENCE_KINDS = frozenset({
    "local_rfi_survey",
    "satellite_interference",
    "ionospheric_event",
    "anthropogenic_source",
    "unknown_transient",
})

ALLOWED_INTERFERENCE_STATUSES = frozenset({
    "assessed",
    "flagged",
    "cleared",
    "inconclusive",
})


def _default_interference_environment_log_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "interference_environment_log.json"
    )


@dataclass
class InterferenceEnvironmentEntry:
    entry_id: str
    run_id: str
    interference_kind: str
    status: str
    assessed_by: str
    assessed_at: str
    frequency_mhz: float | None = None
    severity: str | None = None
    notes: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "run_id": self.run_id,
            "interference_kind": self.interference_kind,
            "status": self.status,
            "assessed_by": self.assessed_by,
            "assessed_at": self.assessed_at,
            "frequency_mhz": self.frequency_mhz,
            "severity": self.severity,
            "notes": self.notes,
        }


def load_interference_environment_entries(
    path: Path | None = None,
) -> list[InterferenceEnvironmentEntry]:
    fpath = path or _default_interference_environment_log_path()
    with open(fpath) as f:
        data = json.load(f)
    entries = []
    for item in data.get("entries", []):
        entries.append(InterferenceEnvironmentEntry(
            entry_id=item["entry_id"],
            run_id=item["run_id"],
            interference_kind=item["interference_kind"],
            status=item["status"],
            assessed_by=item["assessed_by"],
            assessed_at=item["assessed_at"],
            frequency_mhz=item.get("frequency_mhz"),
            severity=item.get("severity"),
            notes=item.get("notes"),
        ))
    return entries


def interference_environment_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_interference_environment_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for e in entries:
        by_kind[e.interference_kind] = by_kind.get(e.interference_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
    return {
        "schema_version": INTERFERENCE_ENVIRONMENT_LOG_SCHEMA_VERSION,
        "disclaimer": INTERFERENCE_ENVIRONMENT_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "assessed_count": by_status.get("assessed", 0),
        "flagged_count": by_status.get("flagged", 0),
        "cleared_count": by_status.get("cleared", 0),
        "inconclusive_count": by_status.get("inconclusive", 0),
        "counts_by_kind": by_kind,
    }
