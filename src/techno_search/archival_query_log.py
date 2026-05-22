"""Operational records for archival/catalog query events submitted by the pipeline."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ARCHIVAL_QUERY_SCHEMA_VERSION = "archival_query_log_v1"

ARCHIVAL_QUERY_DISCLAIMER = (
    "Archival query entries are operational provenance records. "
    "A completed query does not confirm or rule out candidate technosignature interest, "
    "does not modify candidate scores or pathway routing, "
    "and does not authorize external submission or constitute a detection claim."
)

ALLOWED_QUERY_KINDS = frozenset({
    "cone_search", "identifier_lookup", "time_series", "spectral_query", "image_retrieval",
})

ALLOWED_QUERY_STATUSES = frozenset({
    "submitted", "completed", "failed", "cached",
})


def _default_archival_query_path() -> Path:
    return Path(__file__).parent.parent.parent / "tests" / "fixtures" / "archival_query_log.json"


@dataclass
class ArchivalQueryEntry:
    query_id: str
    candidate_id: str
    query_kind: str
    status: str
    queried_by: str
    queried_utc: str
    archive_source: str | None = None
    row_count: int | None = None
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "candidate_id": self.candidate_id,
            "query_kind": self.query_kind,
            "status": self.status,
            "queried_by": self.queried_by,
            "queried_utc": self.queried_utc,
            "archive_source": self.archive_source,
            "row_count": self.row_count,
            "notes": self.notes,
        }


def load_archival_query_entries(path: Path | None = None) -> list[ArchivalQueryEntry]:
    fpath = path or _default_archival_query_path()
    with open(fpath) as f:
        data = json.load(f)
    entries = []
    for item in data.get("archival_query_entries", []):
        entries.append(ArchivalQueryEntry(
            query_id=item["query_id"],
            candidate_id=item["candidate_id"],
            query_kind=item["query_kind"],
            status=item["status"],
            queried_by=item["queried_by"],
            queried_utc=item["queried_utc"],
            archive_source=item.get("archive_source"),
            row_count=item.get("row_count"),
            notes=item.get("notes", ""),
        ))
    return entries


def archival_query_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_archival_query_entries(path)
    by_status: dict[str, int] = {}
    by_query_kind: dict[str, int] = {}
    for e in entries:
        by_status[e.status] = by_status.get(e.status, 0) + 1
        by_query_kind[e.query_kind] = by_query_kind.get(e.query_kind, 0) + 1
    return {
        "schema_version": ARCHIVAL_QUERY_SCHEMA_VERSION,
        "disclaimer": ARCHIVAL_QUERY_DISCLAIMER,
        "entry_count": len(entries),
        "completed_count": by_status.get("completed", 0),
        "failed_count": by_status.get("failed", 0),
        "cached_count": by_status.get("cached", 0),
        "submitted_count": by_status.get("submitted", 0),
        "by_status": by_status,
        "by_query_kind": by_query_kind,
    }
