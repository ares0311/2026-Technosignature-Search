"""Candidate triage note schema and summary helper."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CANDIDATE_TRIAGE_SCHEMA_VERSION = "candidate_triage_v1"

CANDIDATE_TRIAGE_DISCLAIMER = (
    "Candidate triage notes are operator scheduling aids and provenance records only. "
    "They do not modify candidate scores, posteriors, or pathway routing. "
    "Triage notes are not detection claims, discovery announcements, or "
    "authorizations for external submission."
)

ALLOWED_TRIAGE_LABELS = frozenset(
    {
        "needs_human_review",
        "likely_false_positive",
        "follow_up_target",
        "known_object_annotation",
        "insufficient_evidence",
        "defer",
    }
)


def _default_triage_fixture_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "candidate_triage_notes.json"
    )


@dataclass
class CandidateTriageNote:
    note_id: str
    candidate_id: str
    track: str
    triage_label: str
    operator_id: str
    note_text: str
    created_utc: str
    blocking_reasons: list[str] = field(default_factory=list)
    follow_up_required: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "note_id": self.note_id,
            "candidate_id": self.candidate_id,
            "track": self.track,
            "triage_label": self.triage_label,
            "operator_id": self.operator_id,
            "note_text": self.note_text,
            "created_utc": self.created_utc,
            "blocking_reasons": list(self.blocking_reasons),
            "follow_up_required": self.follow_up_required,
        }


def load_triage_notes(
    fixture_path: Path | None = None,
) -> list[CandidateTriageNote]:
    path = fixture_path or _default_triage_fixture_path()
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    notes = []
    for raw in data.get("notes", []):
        notes.append(
            CandidateTriageNote(
                note_id=str(raw["note_id"]),
                candidate_id=str(raw["candidate_id"]),
                track=str(raw["track"]),
                triage_label=str(raw["triage_label"]),
                operator_id=str(raw["operator_id"]),
                note_text=str(raw["note_text"]),
                created_utc=str(raw["created_utc"]),
                blocking_reasons=list(raw.get("blocking_reasons", [])),
                follow_up_required=bool(raw.get("follow_up_required", False)),
            )
        )
    return notes


def triage_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    """Return a summary of candidate triage notes."""

    notes = load_triage_notes(fixture_path)

    by_label: dict[str, int] = {}
    by_track: dict[str, int] = {}
    follow_up_count = 0
    blocking_reason_total = 0

    for note in notes:
        by_label[note.triage_label] = by_label.get(note.triage_label, 0) + 1
        by_track[note.track] = by_track.get(note.track, 0) + 1
        if note.follow_up_required:
            follow_up_count += 1
        blocking_reason_total += len(note.blocking_reasons)

    unique_candidates = len({n.candidate_id for n in notes})
    unique_operators = len({n.operator_id for n in notes})

    return {
        "schema_version": CANDIDATE_TRIAGE_SCHEMA_VERSION,
        "disclaimer": CANDIDATE_TRIAGE_DISCLAIMER,
        "note_count": len(notes),
        "unique_candidate_count": unique_candidates,
        "unique_operator_count": unique_operators,
        "follow_up_required_count": follow_up_count,
        "blocking_reason_total": blocking_reason_total,
        "by_label": dict(sorted(by_label.items())),
        "by_track": dict(sorted(by_track.items())),
        "labels_covered": sorted(by_label.keys()),
        "tracks_covered": sorted(by_track.keys()),
    }
