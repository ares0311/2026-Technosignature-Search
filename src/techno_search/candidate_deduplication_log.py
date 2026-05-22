from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CANDIDATE_DEDUPLICATION_SCHEMA_VERSION = "candidate_deduplication_log_v1"

CANDIDATE_DEDUPLICATION_DISCLAIMER = (
    "Candidate deduplication log entries are operational provenance records only. "
    "A deduplication entry records that a candidate was compared against previously "
    "seen candidates, known objects, prior-epoch observations, or catalog sources "
    "for scheduling triage. Deduplication does not remove candidates from the record, "
    "does not modify scores or pathway routing, does not constitute a detection claim, "
    "and does not authorize external submission."
)

ALLOWED_DEDUPLICATION_STATUSES = frozenset({
    "pending",
    "confirmed_duplicate",
    "confirmed_distinct",
    "inconclusive",
})

ALLOWED_MATCH_KINDS = frozenset({
    "cross_candidate",
    "known_object",
    "prior_epoch",
    "catalog_match",
})


def _default_deduplication_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "candidate_deduplication_log.json"
    )


@dataclass
class CandidateDeduplicationEntry:
    dedup_id: str
    candidate_id: str
    match_kind: str
    status: str
    compared_to_id: str
    compared_by: str
    compared_utc: str
    match_score: float | None = None
    resolved_utc: str | None = None
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "dedup_id": self.dedup_id,
            "candidate_id": self.candidate_id,
            "match_kind": self.match_kind,
            "status": self.status,
            "compared_to_id": self.compared_to_id,
            "compared_by": self.compared_by,
            "compared_utc": self.compared_utc,
            "match_score": self.match_score,
            "resolved_utc": self.resolved_utc,
            "notes": self.notes,
        }


def load_deduplication_entries(
    fixture_path: Path | None = None,
) -> list[CandidateDeduplicationEntry]:
    path = fixture_path or _default_deduplication_path()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = []
    for raw in data.get("candidate_deduplication_entries", []):
        entries.append(
            CandidateDeduplicationEntry(
                dedup_id=raw["dedup_id"],
                candidate_id=raw["candidate_id"],
                match_kind=raw["match_kind"],
                status=raw["status"],
                compared_to_id=raw["compared_to_id"],
                compared_by=raw["compared_by"],
                compared_utc=raw["compared_utc"],
                match_score=raw.get("match_score"),
                resolved_utc=raw.get("resolved_utc"),
                notes=raw.get("notes", ""),
            )
        )
    return entries


def candidate_deduplication_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    entries = load_deduplication_entries(fixture_path)
    by_status: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    for e in entries:
        by_status[e.status] = by_status.get(e.status, 0) + 1
        by_kind[e.match_kind] = by_kind.get(e.match_kind, 0) + 1
    pending_count = by_status.get("pending", 0)
    confirmed_duplicate_count = by_status.get("confirmed_duplicate", 0)
    confirmed_distinct_count = by_status.get("confirmed_distinct", 0)
    return {
        "schema_version": CANDIDATE_DEDUPLICATION_SCHEMA_VERSION,
        "disclaimer": CANDIDATE_DEDUPLICATION_DISCLAIMER,
        "entry_count": len(entries),
        "pending_count": pending_count,
        "confirmed_duplicate_count": confirmed_duplicate_count,
        "confirmed_distinct_count": confirmed_distinct_count,
        "by_status": by_status,
        "by_kind": by_kind,
    }
