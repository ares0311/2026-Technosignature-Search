"""Candidate lifecycle tracking — scheduling and provenance aid."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CANDIDATE_LIFECYCLE_SCHEMA_VERSION = "candidate_lifecycle_v1"

CANDIDATE_LIFECYCLE_DISCLAIMER = (
    "Candidate lifecycle entries are local scheduling and provenance records only. "
    "They are not detection claims, discovery announcements, or external submissions. "
    "All candidates remain unconfirmed and require external, independent validation "
    "before any claim can be made."
)

ALLOWED_LIFECYCLE_STAGES = frozenset(
    {
        "initial_detection",
        "scored",
        "baseline_classified",
        "human_reviewed",
        "pathway_decided",
        "follow_up_scheduled",
        "archived",
    }
)


def _default_lifecycle_fixture_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "candidate_lifecycle_entries.json"
    )


@dataclass
class CandidateLifecycleEntry:
    candidate_id: str
    track: str
    stage: str
    stage_entered_utc: str
    pathway: str
    operator_notes: str = ""
    blocking_reasons: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "track": self.track,
            "stage": self.stage,
            "stage_entered_utc": self.stage_entered_utc,
            "pathway": self.pathway,
            "operator_notes": self.operator_notes,
            "blocking_reasons": list(self.blocking_reasons),
        }


def load_lifecycle_entries(
    fixture_path: Path | None = None,
) -> list[CandidateLifecycleEntry]:
    path = fixture_path or _default_lifecycle_fixture_path()
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    entries = []
    for raw in data.get("entries", []):
        entries.append(
            CandidateLifecycleEntry(
                candidate_id=str(raw["candidate_id"]),
                track=str(raw["track"]),
                stage=str(raw["stage"]),
                stage_entered_utc=str(raw["stage_entered_utc"]),
                pathway=str(raw["pathway"]),
                operator_notes=str(raw.get("operator_notes", "")),
                blocking_reasons=list(raw.get("blocking_reasons", [])),
            )
        )
    return entries


def candidate_lifecycle_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    entries = load_lifecycle_entries(fixture_path)

    by_stage: dict[str, int] = {}
    by_track: dict[str, int] = {}
    by_pathway: dict[str, int] = {}
    for entry in entries:
        by_stage[entry.stage] = by_stage.get(entry.stage, 0) + 1
        by_track[entry.track] = by_track.get(entry.track, 0) + 1
        by_pathway[entry.pathway] = by_pathway.get(entry.pathway, 0) + 1

    stages_covered = sorted(by_stage.keys())
    tracks_covered = sorted(by_track.keys())

    return {
        "schema_version": CANDIDATE_LIFECYCLE_SCHEMA_VERSION,
        "disclaimer": CANDIDATE_LIFECYCLE_DISCLAIMER,
        "entry_count": len(entries),
        "by_stage": dict(sorted(by_stage.items())),
        "by_track": dict(sorted(by_track.items())),
        "by_pathway": dict(sorted(by_pathway.items())),
        "stages_covered": stages_covered,
        "tracks_covered": tracks_covered,
        "operator_note_count": sum(1 for e in entries if e.operator_notes),
    }
