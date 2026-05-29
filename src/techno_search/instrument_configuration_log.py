"""Operational provenance records for instrument hardware configuration changes."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

INSTRUMENT_CONFIGURATION_LOG_SCHEMA_VERSION = "instrument_configuration_log_v1"

INSTRUMENT_CONFIGURATION_LOG_DISCLAIMER = (
    "Instrument configuration entries are operational provenance records — "
    "a configuration change does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

ALLOWED_CONFIGURATION_KINDS = frozenset(
    {
        "frontend_swap",
        "backend_change",
        "receiver_install",
        "filter_change",
        "attenuator_set",
    }
)

ALLOWED_CONFIGURATION_STATUSES = frozenset(
    {
        "applied",
        "pending",
        "reverted",
        "failed",
    }
)


@dataclass
class InstrumentConfigurationEntry:
    entry_id: str
    configuration_kind: str
    status: str
    configured_by: str
    configured_at: str
    instrument_id: str
    track: str
    previous_value: str | None
    new_value: str | None
    notes: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "configuration_kind": self.configuration_kind,
            "status": self.status,
            "configured_by": self.configured_by,
            "configured_at": self.configured_at,
            "instrument_id": self.instrument_id,
            "track": self.track,
            "previous_value": self.previous_value,
            "new_value": self.new_value,
            "notes": self.notes,
        }


def load_instrument_configuration_entries(
    path: Path | None = None,
) -> list[InstrumentConfigurationEntry]:
    if path is None:
        path = (
            Path(__file__).parent.parent.parent
            / "tests"
            / "fixtures"
            / "instrument_configuration_log.json"
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        InstrumentConfigurationEntry(
            entry_id=e["entry_id"],
            configuration_kind=e["configuration_kind"],
            status=e["status"],
            configured_by=e["configured_by"],
            configured_at=e["configured_at"],
            instrument_id=e["instrument_id"],
            track=e["track"],
            previous_value=e.get("previous_value"),
            new_value=e.get("new_value"),
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def instrument_configuration_summary(
    path: Path | None = None,
) -> dict[str, Any]:
    entries = load_instrument_configuration_entries(path)
    counts_by_status: dict[str, int] = {}
    for e in entries:
        counts_by_status[e.status] = counts_by_status.get(e.status, 0) + 1
    counts_by_kind: dict[str, int] = {}
    for e in entries:
        counts_by_kind[e.configuration_kind] = (
            counts_by_kind.get(e.configuration_kind, 0) + 1
        )
    return {
        "schema_version": INSTRUMENT_CONFIGURATION_LOG_SCHEMA_VERSION,
        "disclaimer": INSTRUMENT_CONFIGURATION_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "applied_count": counts_by_status.get("applied", 0),
        "pending_count": counts_by_status.get("pending", 0),
        "reverted_count": counts_by_status.get("reverted", 0),
        "failed_count": counts_by_status.get("failed", 0),
        "counts_by_status": counts_by_status,
        "counts_by_kind": counts_by_kind,
    }
