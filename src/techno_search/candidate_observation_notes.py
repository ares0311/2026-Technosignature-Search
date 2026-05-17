"""Candidate observation notes — post-observation operator annotations."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CANDIDATE_OBSERVATION_NOTES_SCHEMA_VERSION = "candidate_observation_notes_v1"

CANDIDATE_OBSERVATION_NOTES_DISCLAIMER = (
    "Candidate observation notes are post-observation operator annotations recorded "
    "for scheduling and provenance purposes only. They do not constitute external "
    "validation, detection claims, or discovery announcements. Notes flagging "
    "quality issues are expected and do not modify candidate posteriors."
)

ALLOWED_OBSERVATION_OUTCOMES = frozenset(
    {
        "clean",
        "rfi_contaminated",
        "low_snr",
        "non_detection",
        "data_quality_issue",
        "needs_reobservation",
        "archived",
    }
)


def _default_observation_notes_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "candidate_observation_notes.json"
    )


@dataclass
class CandidateObservationNote:
    note_id: str
    candidate_id: str
    track: str
    observation_id: str
    operator_id: str
    outcome: str
    note_text: str
    created_utc: str
    quality_flags: list[str] = field(default_factory=list)
    follow_up_recommended: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "note_id": self.note_id,
            "candidate_id": self.candidate_id,
            "track": self.track,
            "observation_id": self.observation_id,
            "operator_id": self.operator_id,
            "outcome": self.outcome,
            "note_text": self.note_text,
            "created_utc": self.created_utc,
            "quality_flags": list(self.quality_flags),
            "follow_up_recommended": self.follow_up_recommended,
        }


def load_observation_notes(
    fixture_path: Path | None = None,
) -> list[CandidateObservationNote]:
    path = fixture_path or _default_observation_notes_path()
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    notes = []
    for raw in data.get("notes", []):
        notes.append(
            CandidateObservationNote(
                note_id=str(raw["note_id"]),
                candidate_id=str(raw["candidate_id"]),
                track=str(raw["track"]),
                observation_id=str(raw["observation_id"]),
                operator_id=str(raw["operator_id"]),
                outcome=str(raw["outcome"]),
                note_text=str(raw.get("note_text", "")),
                created_utc=str(raw["created_utc"]),
                quality_flags=list(raw.get("quality_flags", [])),
                follow_up_recommended=bool(raw.get("follow_up_recommended", False)),
            )
        )
    return notes


def observation_notes_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    """Return a summary of candidate observation notes."""

    notes = load_observation_notes(fixture_path)

    by_track: dict[str, int] = {}
    by_outcome: dict[str, int] = {}
    follow_up_count = 0
    quality_flag_total = 0

    for note in notes:
        by_track[note.track] = by_track.get(note.track, 0) + 1
        by_outcome[note.outcome] = by_outcome.get(note.outcome, 0) + 1
        if note.follow_up_recommended:
            follow_up_count += 1
        quality_flag_total += len(note.quality_flags)

    unique_candidates = len({n.candidate_id for n in notes})
    unique_operators = len({n.operator_id for n in notes})

    return {
        "schema_version": CANDIDATE_OBSERVATION_NOTES_SCHEMA_VERSION,
        "disclaimer": CANDIDATE_OBSERVATION_NOTES_DISCLAIMER,
        "note_count": len(notes),
        "unique_candidate_count": unique_candidates,
        "unique_operator_count": unique_operators,
        "follow_up_recommended_count": follow_up_count,
        "quality_flag_total": quality_flag_total,
        "by_track": dict(sorted(by_track.items())),
        "by_outcome": dict(sorted(by_outcome.items())),
        "tracks_covered": sorted(by_track.keys()),
        "outcomes_covered": sorted(by_outcome.keys()),
    }
