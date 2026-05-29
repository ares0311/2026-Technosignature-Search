"""Operational scheduling provenance records for receiver health checks."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

RECEIVER_HEALTH_LOG_SCHEMA_VERSION = "receiver_health_log_v1"

RECEIVER_HEALTH_LOG_DISCLAIMER = (
    "Receiver health entries are operational scheduling provenance records — "
    "a health check does not modify candidate scores or pathway routing, "
    "does not authorize external submission, "
    "and does not constitute a detection claim."
)

ALLOWED_RECEIVER_HEALTH_KINDS = frozenset({
    "gain_stability",
    "noise_temperature",
    "bandpass_flatness",
    "pointing_accuracy",
    "focus_setting",
})

ALLOWED_RECEIVER_HEALTH_STATUSES = frozenset({
    "nominal",
    "degraded",
    "critical",
    "maintenance_required",
})


def _default_receiver_health_log_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "receiver_health_log.json"
    )


@dataclass
class ReceiverHealthEntry:
    entry_id: str
    run_id: str
    health_kind: str
    status: str
    checked_by: str
    checked_at: str
    metric_value: float | None = None
    threshold_value: float | None = None
    notes: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "run_id": self.run_id,
            "health_kind": self.health_kind,
            "status": self.status,
            "checked_by": self.checked_by,
            "checked_at": self.checked_at,
            "metric_value": self.metric_value,
            "threshold_value": self.threshold_value,
            "notes": self.notes,
        }


def load_receiver_health_entries(
    path: Path | None = None,
) -> list[ReceiverHealthEntry]:
    fpath = path or _default_receiver_health_log_path()
    with open(fpath) as f:
        data = json.load(f)
    entries = []
    for item in data.get("entries", []):
        entries.append(ReceiverHealthEntry(
            entry_id=item["entry_id"],
            run_id=item["run_id"],
            health_kind=item["health_kind"],
            status=item["status"],
            checked_by=item["checked_by"],
            checked_at=item["checked_at"],
            metric_value=item.get("metric_value"),
            threshold_value=item.get("threshold_value"),
            notes=item.get("notes"),
        ))
    return entries


def receiver_health_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_receiver_health_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for e in entries:
        by_kind[e.health_kind] = by_kind.get(e.health_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
    return {
        "schema_version": RECEIVER_HEALTH_LOG_SCHEMA_VERSION,
        "disclaimer": RECEIVER_HEALTH_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "nominal_count": by_status.get("nominal", 0),
        "degraded_count": by_status.get("degraded", 0),
        "critical_count": by_status.get("critical", 0),
        "maintenance_required_count": by_status.get("maintenance_required", 0),
        "counts_by_kind": by_kind,
    }
