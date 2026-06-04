"""Operational provenance records for data transfer and synchronization events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DATA_TRANSFER_LOG_SCHEMA_VERSION = "data_transfer_log_v1"

DATA_TRANSFER_LOG_DISCLAIMER = (
    "Data transfer log entries are operational provenance records — "
    "a data transfer event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

ALLOWED_DATA_TRANSFER_KINDS = frozenset(
    {
        "bulk_export",
        "emergency_transfer",
        "inbound_transfer",
        "internal_sync",
        "outbound_transfer",
    }
)

ALLOWED_DATA_TRANSFER_STATUSES = frozenset(
    {
        "cancelled",
        "completed",
        "failed",
        "in_progress",
    }
)


def _default_data_transfer_log_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "data_transfer_log.json"
    )


@dataclass(frozen=True)
class DataTransferEntry:
    entry_id: str
    transfer_kind: str
    status: str
    actor_id: str
    source_id: str
    destination_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.transfer_kind not in ALLOWED_DATA_TRANSFER_KINDS:
            raise ValueError(f"Invalid transfer_kind: {self.transfer_kind!r}")
        if self.status not in ALLOWED_DATA_TRANSFER_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_data_transfer_entries(
    path: Path | None = None,
) -> list[DataTransferEntry]:
    fpath = path or _default_data_transfer_log_path()
    raw: dict[str, Any] = json.loads(fpath.read_text(encoding="utf-8"))
    return [
        DataTransferEntry(
            entry_id=e["entry_id"],
            transfer_kind=e["transfer_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            source_id=e["source_id"],
            destination_id=e["destination_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def data_transfer_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_data_transfer_entries(path)
    completed = sum(1 for e in entries if e.status == "completed")
    return {
        "schema_version": DATA_TRANSFER_LOG_SCHEMA_VERSION,
        "disclaimer": DATA_TRANSFER_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "completed_count": completed,
        "by_kind": {
            kind: sum(1 for e in entries if e.transfer_kind == kind)
            for kind in sorted(ALLOWED_DATA_TRANSFER_KINDS)
        },
        "by_status": {
            status: sum(1 for e in entries if e.status == status)
            for status in sorted(ALLOWED_DATA_TRANSFER_STATUSES)
        },
    }
