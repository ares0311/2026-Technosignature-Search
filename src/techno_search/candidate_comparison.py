from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CANDIDATE_COMPARISON_SCHEMA_VERSION = "candidate_comparison_v1"

CANDIDATE_COMPARISON_DISCLAIMER = (
    "Candidate comparison records are local scheduling aids only. "
    "Ranked status reflects relative scoring order among the compared candidates "
    "and does not modify scores, posteriors, or pathway routing. "
    "This record does not authorize external submission or constitute a detection claim."
)

ALLOWED_COMPARISON_STATUSES = frozenset(
    {"ranked", "tied", "inconclusive", "insufficient_data"}
)


def _default_comparison_fixture_path() -> Path:
    return Path(__file__).parent.parent.parent / "tests" / "fixtures" / "candidate_comparisons.json"


@dataclass
class CandidateComparisonRecord:
    comparison_id: str
    candidate_ids: list[str]
    comparison_status: str
    scores: dict[str, float]
    pathways: dict[str, str]
    top_candidate_id: str
    comparison_utc: str
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "comparison_id": self.comparison_id,
            "candidate_ids": self.candidate_ids,
            "comparison_status": self.comparison_status,
            "scores": self.scores,
            "pathways": self.pathways,
            "top_candidate_id": self.top_candidate_id,
            "comparison_utc": self.comparison_utc,
            "notes": self.notes,
        }


def load_comparison_records(
    fixture_path: Path | str | None = None,
) -> list[CandidateComparisonRecord]:
    path = Path(fixture_path) if fixture_path is not None else _default_comparison_fixture_path()
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    records = []
    for entry in data.get("candidate_comparisons", []):
        records.append(
            CandidateComparisonRecord(
                comparison_id=entry["comparison_id"],
                candidate_ids=list(entry["candidate_ids"]),
                comparison_status=entry["comparison_status"],
                scores=dict(entry.get("scores", {})),
                pathways=dict(entry.get("pathways", {})),
                top_candidate_id=entry.get("top_candidate_id", ""),
                comparison_utc=entry["comparison_utc"],
                notes=entry.get("notes", ""),
            )
        )
    return records


def candidate_comparison_summary(
    fixture_path: Path | str | None = None,
) -> dict[str, Any]:
    records = load_comparison_records(fixture_path)
    by_status: dict[str, int] = {}
    for rec in records:
        by_status[rec.comparison_status] = by_status.get(rec.comparison_status, 0) + 1
    ranked = [r for r in records if r.comparison_status == "ranked"]
    top_candidates = sorted({r.top_candidate_id for r in ranked if r.top_candidate_id})
    return {
        "disclaimer": CANDIDATE_COMPARISON_DISCLAIMER,
        "schema_version": CANDIDATE_COMPARISON_SCHEMA_VERSION,
        "record_count": len(records),
        "ranked_count": by_status.get("ranked", 0),
        "tied_count": by_status.get("tied", 0),
        "inconclusive_count": by_status.get("inconclusive", 0),
        "insufficient_data_count": by_status.get("insufficient_data", 0),
        "by_status": by_status,
        "top_candidate_ids": top_candidates,
    }
