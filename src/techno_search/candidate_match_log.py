from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CANDIDATE_MATCH_SCHEMA_VERSION = "candidate_match_log_v1"

CANDIDATE_MATCH_DISCLAIMER = (
    "Candidate match log entries are operational provenance records only. "
    "A match log entry records the result of a cross-catalog matching operation "
    "performed for a candidate against an external or internal catalog source. "
    "A catalog match does not confirm or rule out candidate technosignature interest, "
    "does not modify candidate scores or pathway routing, does not authorize external "
    "submission, and does not constitute a detection claim."
)

ALLOWED_MATCH_SOURCES = frozenset({
    "simbad", "gaia", "vizier", "irsa", "internal_catalog",
})

ALLOWED_MATCH_STATUSES = frozenset({
    "matched", "no_match", "ambiguous", "pending",
})


def _default_candidate_match_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests" / "fixtures" / "candidate_match_log.json"
    )


@dataclass
class CandidateMatchEntry:
    match_id: str
    candidate_id: str
    match_source: str
    status: str
    matched_by: str
    matched_utc: str
    angular_separation_arcsec: float | None = None
    matched_object_id: str | None = None
    matched_object_type: str | None = None
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "match_id": self.match_id,
            "candidate_id": self.candidate_id,
            "match_source": self.match_source,
            "status": self.status,
            "matched_by": self.matched_by,
            "matched_utc": self.matched_utc,
            "angular_separation_arcsec": self.angular_separation_arcsec,
            "matched_object_id": self.matched_object_id,
            "matched_object_type": self.matched_object_type,
            "notes": self.notes,
        }


def load_match_entries(fixture_path: Path | None = None) -> list[CandidateMatchEntry]:
    path = fixture_path or _default_candidate_match_path()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = []
    for raw in data.get("candidate_match_entries", []):
        entries.append(CandidateMatchEntry(
            match_id=raw["match_id"],
            candidate_id=raw["candidate_id"],
            match_source=raw["match_source"],
            status=raw["status"],
            matched_by=raw["matched_by"],
            matched_utc=raw["matched_utc"],
            angular_separation_arcsec=raw.get("angular_separation_arcsec"),
            matched_object_id=raw.get("matched_object_id"),
            matched_object_type=raw.get("matched_object_type"),
            notes=raw.get("notes", ""),
        ))
    return entries


def candidate_match_summary(fixture_path: Path | None = None) -> dict[str, Any]:
    entries = load_match_entries(fixture_path)
    by_status: dict[str, int] = {}
    by_source: dict[str, int] = {}
    for e in entries:
        by_status[e.status] = by_status.get(e.status, 0) + 1
        by_source[e.match_source] = by_source.get(e.match_source, 0) + 1
    return {
        "schema_version": CANDIDATE_MATCH_SCHEMA_VERSION,
        "disclaimer": CANDIDATE_MATCH_DISCLAIMER,
        "entry_count": len(entries),
        "matched_count": by_status.get("matched", 0),
        "no_match_count": by_status.get("no_match", 0),
        "ambiguous_count": by_status.get("ambiguous", 0),
        "pending_count": by_status.get("pending", 0),
        "by_status": by_status,
        "by_source": by_source,
    }
