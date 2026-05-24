"""Operational provenance records for external source catalog query events."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SOURCE_CATALOG_LOG_SCHEMA_VERSION = "source_catalog_log_v1"

SOURCE_CATALOG_LOG_DISCLAIMER = (
    "Source catalog entries are operational provenance records — a catalog match "
    "does not confirm or rule out technosignature interest, does not modify candidate "
    "scores or pathway routing, and does not authorize external submission or "
    "constitute a detection claim."
)

ALLOWED_CATALOG_KINDS = frozenset({
    "stellar", "radio_source", "infrared", "known_rfi", "known_object",
})

ALLOWED_CATALOG_STATUSES = frozenset({
    "queried", "matched", "no_match", "error",
})


def _default_source_catalog_log_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "source_catalog_log.json"
    )


@dataclass
class SourceCatalogEntry:
    entry_id: str
    candidate_id: str
    catalog_kind: str
    status: str
    catalog_name: str
    queried_by: str
    queried_at: str
    track: str
    match_count: int | None = None
    notes: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "candidate_id": self.candidate_id,
            "catalog_kind": self.catalog_kind,
            "status": self.status,
            "catalog_name": self.catalog_name,
            "queried_by": self.queried_by,
            "queried_at": self.queried_at,
            "track": self.track,
            "match_count": self.match_count,
            "notes": self.notes,
        }


def load_source_catalog_entries(
    path: Path | None = None,
) -> list[SourceCatalogEntry]:
    fpath = path or _default_source_catalog_log_path()
    with open(fpath) as f:
        data = json.load(f)
    entries = []
    for item in data.get("source_catalog_entries", []):
        entries.append(SourceCatalogEntry(
            entry_id=item["entry_id"],
            candidate_id=item["candidate_id"],
            catalog_kind=item["catalog_kind"],
            status=item["status"],
            catalog_name=item["catalog_name"],
            queried_by=item["queried_by"],
            queried_at=item["queried_at"],
            track=item["track"],
            match_count=item.get("match_count"),
            notes=item.get("notes"),
        ))
    return entries


def source_catalog_log_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_source_catalog_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for e in entries:
        by_kind[e.catalog_kind] = by_kind.get(e.catalog_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
    return {
        "schema_version": SOURCE_CATALOG_LOG_SCHEMA_VERSION,
        "disclaimer": SOURCE_CATALOG_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "matched_count": by_status.get("matched", 0),
        "no_match_count": by_status.get("no_match", 0),
        "counts_by_kind": by_kind,
        "counts_by_status": by_status,
    }
