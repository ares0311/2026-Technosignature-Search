"""Operational provenance records for observation data archival events."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DATA_ARCHIVAL_LOG_SCHEMA_VERSION = "data_archival_log_v1"

DATA_ARCHIVAL_LOG_DISCLAIMER = (
    "Data archival entries are operational provenance records — "
    "an archival record does not modify candidate scores or pathway routing, "
    "does not authorize external submission, "
    "and does not constitute a detection claim."
)

ALLOWED_DATA_ARCHIVAL_KINDS = frozenset({
    "raw_data",
    "processed_data",
    "candidate_packet",
    "pipeline_artifact",
    "calibration_data",
})

ALLOWED_DATA_ARCHIVAL_STATUSES = frozenset({
    "archived",
    "pending",
    "failed",
    "deleted",
})


def _default_data_archival_log_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "data_archival_log.json"
    )


@dataclass
class DataArchivalEntry:
    entry_id: str
    candidate_id: str
    track: str
    archival_kind: str
    status: str
    archived_by: str
    archived_at: str
    artifact_path: str | None = None
    size_bytes: int | None = None
    notes: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "candidate_id": self.candidate_id,
            "track": self.track,
            "archival_kind": self.archival_kind,
            "status": self.status,
            "archived_by": self.archived_by,
            "archived_at": self.archived_at,
            "artifact_path": self.artifact_path,
            "size_bytes": self.size_bytes,
            "notes": self.notes,
        }


def load_data_archival_entries(
    path: Path | None = None,
) -> list[DataArchivalEntry]:
    fpath = path or _default_data_archival_log_path()
    with open(fpath) as f:
        data = json.load(f)
    entries = []
    for item in data.get("entries", []):
        entries.append(DataArchivalEntry(
            entry_id=item["entry_id"],
            candidate_id=item["candidate_id"],
            track=item["track"],
            archival_kind=item["archival_kind"],
            status=item["status"],
            archived_by=item["archived_by"],
            archived_at=item["archived_at"],
            artifact_path=item.get("artifact_path"),
            size_bytes=item.get("size_bytes"),
            notes=item.get("notes"),
        ))
    return entries


def data_archival_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_data_archival_entries(path)
    by_kind: dict[str, int] = {}
    by_track: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for e in entries:
        by_kind[e.archival_kind] = by_kind.get(e.archival_kind, 0) + 1
        by_track[e.track] = by_track.get(e.track, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
    return {
        "schema_version": DATA_ARCHIVAL_LOG_SCHEMA_VERSION,
        "disclaimer": DATA_ARCHIVAL_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "archived_count": by_status.get("archived", 0),
        "pending_count": by_status.get("pending", 0),
        "failed_count": by_status.get("failed", 0),
        "deleted_count": by_status.get("deleted", 0),
        "counts_by_kind": by_kind,
        "counts_by_track": by_track,
    }
