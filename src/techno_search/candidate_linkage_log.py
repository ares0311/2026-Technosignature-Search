"""Operational records linking related candidates together."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CANDIDATE_LINKAGE_SCHEMA_VERSION = "candidate_linkage_log_v1"

CANDIDATE_LINKAGE_DISCLAIMER = (
    "Candidate linkage entries are operational provenance records. "
    "A confirmed linkage does not modify candidate scores or pathway routing, "
    "does not constitute a detection claim, "
    "and does not authorize external submission."
)

ALLOWED_LINKAGE_KINDS = frozenset({
    "same_source", "temporal_followup", "spatial_neighbor",
    "frequency_related", "cross_track",
})

ALLOWED_LINKAGE_STATUSES = frozenset({
    "proposed", "confirmed", "rejected", "under_review",
})


def _default_linkage_path() -> Path:
    return (
        Path(__file__).parent.parent.parent / "tests" / "fixtures" / "candidate_linkage_log.json"
    )


@dataclass
class CandidateLinkageEntry:
    linkage_id: str
    candidate_id_a: str
    candidate_id_b: str
    linkage_kind: str
    status: str
    linked_by: str
    linked_utc: str
    separation_arcsec: float | None = None
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "linkage_id": self.linkage_id,
            "candidate_id_a": self.candidate_id_a,
            "candidate_id_b": self.candidate_id_b,
            "linkage_kind": self.linkage_kind,
            "status": self.status,
            "linked_by": self.linked_by,
            "linked_utc": self.linked_utc,
            "separation_arcsec": self.separation_arcsec,
            "notes": self.notes,
        }


def load_linkage_entries(path: Path | None = None) -> list[CandidateLinkageEntry]:
    fpath = path or _default_linkage_path()
    with open(fpath) as f:
        data = json.load(f)
    entries = []
    for item in data.get("candidate_linkage_entries", []):
        entries.append(CandidateLinkageEntry(
            linkage_id=item["linkage_id"],
            candidate_id_a=item["candidate_id_a"],
            candidate_id_b=item["candidate_id_b"],
            linkage_kind=item["linkage_kind"],
            status=item["status"],
            linked_by=item["linked_by"],
            linked_utc=item["linked_utc"],
            separation_arcsec=item.get("separation_arcsec"),
            notes=item.get("notes", ""),
        ))
    return entries


def candidate_linkage_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_linkage_entries(path)
    by_status: dict[str, int] = {}
    by_linkage_kind: dict[str, int] = {}
    for e in entries:
        by_status[e.status] = by_status.get(e.status, 0) + 1
        by_linkage_kind[e.linkage_kind] = by_linkage_kind.get(e.linkage_kind, 0) + 1
    return {
        "schema_version": CANDIDATE_LINKAGE_SCHEMA_VERSION,
        "disclaimer": CANDIDATE_LINKAGE_DISCLAIMER,
        "entry_count": len(entries),
        "confirmed_count": by_status.get("confirmed", 0),
        "proposed_count": by_status.get("proposed", 0),
        "rejected_count": by_status.get("rejected", 0),
        "under_review_count": by_status.get("under_review", 0),
        "by_status": by_status,
        "by_linkage_kind": by_linkage_kind,
    }
