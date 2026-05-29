"""Operational provenance records for data transfer events."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DATA_TRANSFER_LOG_SCHEMA_VERSION = "data_transfer_log_v1"

DATA_TRANSFER_LOG_DISCLAIMER = (
    "Data transfer entries are operational provenance records — "
    "a transfer record does not modify candidate scores or pathway routing, "
    "does not authorize external submission, "
    "and does not constitute a detection claim."
)

ALLOWED_DATA_TRANSFER_KINDS = frozenset({
    "archive_transfer",
    "inter_site_transfer",
    "local_copy",
    "cloud_upload",
    "network_delivery",
})

ALLOWED_DATA_TRANSFER_STATUSES = frozenset({
    "pending",
    "completed",
    "failed",
    "verified",
})


def _default_data_transfer_log_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "data_transfer_log.json"
    )


@dataclass
class DataTransferEntry:
    entry_id: str
    candidate_id: str
    track: str
    transfer_kind: str
    status: str
    initiated_by: str
    initiated_at: str
    source_path: str | None = None
    destination_path: str | None = None
    bytes_transferred: int | None = None
    notes: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "candidate_id": self.candidate_id,
            "track": self.track,
            "transfer_kind": self.transfer_kind,
            "status": self.status,
            "initiated_by": self.initiated_by,
            "initiated_at": self.initiated_at,
            "source_path": self.source_path,
            "destination_path": self.destination_path,
            "bytes_transferred": self.bytes_transferred,
            "notes": self.notes,
        }


def load_data_transfer_entries(
    path: Path | None = None,
) -> list[DataTransferEntry]:
    fpath = path or _default_data_transfer_log_path()
    with open(fpath) as f:
        data = json.load(f)
    entries = []
    for item in data.get("entries", []):
        entries.append(DataTransferEntry(
            entry_id=item["entry_id"],
            candidate_id=item["candidate_id"],
            track=item["track"],
            transfer_kind=item["transfer_kind"],
            status=item["status"],
            initiated_by=item["initiated_by"],
            initiated_at=item["initiated_at"],
            source_path=item.get("source_path"),
            destination_path=item.get("destination_path"),
            bytes_transferred=item.get("bytes_transferred"),
            notes=item.get("notes"),
        ))
    return entries


def data_transfer_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_data_transfer_entries(path)
    by_kind: dict[str, int] = {}
    by_track: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for e in entries:
        by_kind[e.transfer_kind] = by_kind.get(e.transfer_kind, 0) + 1
        by_track[e.track] = by_track.get(e.track, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
    return {
        "schema_version": DATA_TRANSFER_LOG_SCHEMA_VERSION,
        "disclaimer": DATA_TRANSFER_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "completed_count": by_status.get("completed", 0),
        "pending_count": by_status.get("pending", 0),
        "failed_count": by_status.get("failed", 0),
        "verified_count": by_status.get("verified", 0),
        "counts_by_kind": by_kind,
        "counts_by_track": by_track,
    }
