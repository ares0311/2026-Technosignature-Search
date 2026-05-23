"""Operational provenance records for candidate status transitions."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CANDIDATE_STATUS_LOG_SCHEMA_VERSION = "candidate_status_log_v1"

CANDIDATE_STATUS_LOG_DISCLAIMER = (
    "Candidate status entries are operational provenance records. "
    "A status transition does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

ALLOWED_STATUS_TRANSITION_KINDS = frozenset({
    "initial", "promotion", "demotion", "hold", "archive",
})

ALLOWED_CANDIDATE_STATUSES = frozenset({
    "new", "active", "under_review", "on_hold", "archived",
})


def _default_candidate_status_log_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "candidate_status_log.json"
    )


@dataclass
class CandidateStatusEntry:
    entry_id: str
    candidate_id: str
    transition_kind: str
    current_status: str
    transitioned_by: str
    transitioned_at: str
    track: str
    previous_status: str | None = None
    reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "candidate_id": self.candidate_id,
            "transition_kind": self.transition_kind,
            "current_status": self.current_status,
            "transitioned_by": self.transitioned_by,
            "transitioned_at": self.transitioned_at,
            "track": self.track,
            "previous_status": self.previous_status,
            "reason": self.reason,
        }


def load_candidate_status_entries(
    path: Path | None = None,
) -> list[CandidateStatusEntry]:
    fpath = path or _default_candidate_status_log_path()
    with open(fpath) as f:
        data = json.load(f)
    entries = []
    for item in data.get("candidate_status_entries", []):
        entries.append(CandidateStatusEntry(
            entry_id=item["entry_id"],
            candidate_id=item["candidate_id"],
            transition_kind=item["transition_kind"],
            current_status=item["current_status"],
            transitioned_by=item["transitioned_by"],
            transitioned_at=item["transitioned_at"],
            track=item["track"],
            previous_status=item.get("previous_status"),
            reason=item.get("reason"),
        ))
    return entries


def candidate_status_log_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_candidate_status_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    unique_candidates: set[str] = set()
    for e in entries:
        by_kind[e.transition_kind] = by_kind.get(e.transition_kind, 0) + 1
        by_status[e.current_status] = by_status.get(e.current_status, 0) + 1
        unique_candidates.add(e.candidate_id)
    return {
        "schema_version": CANDIDATE_STATUS_LOG_SCHEMA_VERSION,
        "disclaimer": CANDIDATE_STATUS_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "active_count": by_status.get("active", 0),
        "archived_count": by_status.get("archived", 0),
        "counts_by_kind": by_kind,
        "counts_by_status": by_status,
        "unique_candidate_count": len(unique_candidates),
    }
