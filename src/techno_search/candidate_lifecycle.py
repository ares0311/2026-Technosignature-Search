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


STAGE_ORDER = [
    "initial_detection",
    "scored",
    "baseline_classified",
    "human_reviewed",
    "pathway_decided",
    "follow_up_scheduled",
    "archived",
]

_STAGE_INDEX = {stage: idx for idx, stage in enumerate(STAGE_ORDER)}


def lifecycle_transition_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    """Validate lifecycle stage transitions follow the allowed ordering.

    Groups entries by candidate_id and checks that stage_entered_utc ordering
    is consistent with the expected stage progression. Reports any regressions
    (stage index moving backward) as invalid transitions.
    """

    entries = load_lifecycle_entries(fixture_path)

    by_candidate: dict[str, list[CandidateLifecycleEntry]] = {}
    for entry in entries:
        by_candidate.setdefault(entry.candidate_id, []).append(entry)

    invalid_transitions: list[dict[str, Any]] = []
    candidates_with_multiple_entries = 0

    for cid, cand_entries in by_candidate.items():
        if len(cand_entries) < 2:
            continue
        candidates_with_multiple_entries += 1
        sorted_entries = sorted(cand_entries, key=lambda e: e.stage_entered_utc)
        for i in range(1, len(sorted_entries)):
            prev = sorted_entries[i - 1]
            curr = sorted_entries[i]
            prev_idx = _STAGE_INDEX.get(prev.stage, -1)
            curr_idx = _STAGE_INDEX.get(curr.stage, -1)
            if curr_idx < prev_idx:
                invalid_transitions.append(
                    {
                        "candidate_id": cid,
                        "from_stage": prev.stage,
                        "to_stage": curr.stage,
                        "from_utc": prev.stage_entered_utc,
                        "to_utc": curr.stage_entered_utc,
                    }
                )

    candidates_with_invalid_transitions = len(
        {t["candidate_id"] for t in invalid_transitions}
    )

    return {
        "schema_version": CANDIDATE_LIFECYCLE_SCHEMA_VERSION,
        "disclaimer": CANDIDATE_LIFECYCLE_DISCLAIMER,
        "total_entry_count": len(entries),
        "unique_candidate_count": len(by_candidate),
        "candidates_with_multiple_entries": candidates_with_multiple_entries,
        "invalid_transition_count": len(invalid_transitions),
        "candidates_with_invalid_transitions": candidates_with_invalid_transitions,
        "invalid_transitions": invalid_transitions,
        "all_transitions_valid": len(invalid_transitions) == 0,
    }
