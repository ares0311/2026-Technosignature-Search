"""Candidate score history — tracks score evolution across observation epochs."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CANDIDATE_SCORE_HISTORY_SCHEMA_VERSION = "candidate_score_history_v1"

CANDIDATE_SCORE_HISTORY_DISCLAIMER = (
    "Candidate score history entries are local scheduling and provenance records only. "
    "Score changes across epochs reflect updates to synthetic feature estimates and "
    "local pipeline parameters. They do not constitute detections, discoveries, "
    "external validation, or calibrated survey sensitivity estimates."
)

ALLOWED_SCORE_HISTORY_PATHWAYS = frozenset(
    {
        "candidate_review_packet",
        "human_review_queue",
        "do_not_submit_false_positive",
        "known_object_annotation",
        "github_reproducibility_only",
    }
)


def _default_score_history_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "candidate_score_history.json"
    )


@dataclass
class CandidateScoreHistoryEntry:
    entry_id: str
    candidate_id: str
    track: str
    epoch_number: int
    composite_score: float
    pathway: str
    blocking_count: int
    operator_id: str
    created_utc: str
    score_delta: float = 0.0
    notes: str = ""
    feature_highlights: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "candidate_id": self.candidate_id,
            "track": self.track,
            "epoch_number": self.epoch_number,
            "composite_score": self.composite_score,
            "pathway": self.pathway,
            "blocking_count": self.blocking_count,
            "operator_id": self.operator_id,
            "created_utc": self.created_utc,
            "score_delta": self.score_delta,
            "notes": self.notes,
            "feature_highlights": list(self.feature_highlights),
        }


def load_score_history(
    fixture_path: Path | None = None,
) -> list[CandidateScoreHistoryEntry]:
    path = fixture_path if fixture_path is not None else _default_score_history_path()
    raw = json.loads(path.read_text())
    entries = raw.get("entries", [])
    result: list[CandidateScoreHistoryEntry] = []
    for e in entries:
        result.append(
            CandidateScoreHistoryEntry(
                entry_id=str(e["entry_id"]),
                candidate_id=str(e["candidate_id"]),
                track=str(e["track"]),
                epoch_number=int(e["epoch_number"]),
                composite_score=float(e["composite_score"]),
                pathway=str(e["pathway"]),
                blocking_count=int(e["blocking_count"]),
                operator_id=str(e["operator_id"]),
                created_utc=str(e["created_utc"]),
                score_delta=float(e.get("score_delta", 0.0)),
                notes=str(e.get("notes", "")),
                feature_highlights=list(e.get("feature_highlights", [])),
            )
        )
    return result


def score_history_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    entries = load_score_history(fixture_path)

    by_track: dict[str, int] = {}
    by_pathway: dict[str, int] = {}
    by_candidate: dict[str, list[float]] = {}

    for e in entries:
        by_track[e.track] = by_track.get(e.track, 0) + 1
        by_pathway[e.pathway] = by_pathway.get(e.pathway, 0) + 1
        by_candidate.setdefault(e.candidate_id, []).append(e.composite_score)

    improving: list[str] = []
    declining: list[str] = []
    stable: list[str] = []
    for cid, scores in by_candidate.items():
        if len(scores) < 2:
            stable.append(cid)
        elif scores[-1] > scores[0]:
            improving.append(cid)
        elif scores[-1] < scores[0]:
            declining.append(cid)
        else:
            stable.append(cid)

    max_epoch = max((e.epoch_number for e in entries), default=0)

    return {
        "schema_version": CANDIDATE_SCORE_HISTORY_SCHEMA_VERSION,
        "disclaimer": CANDIDATE_SCORE_HISTORY_DISCLAIMER,
        "entry_count": len(entries),
        "unique_candidate_count": len(by_candidate),
        "max_epoch_number": max_epoch,
        "by_track": dict(sorted(by_track.items())),
        "by_pathway": dict(sorted(by_pathway.items())),
        "tracks_covered": sorted(by_track.keys()),
        "improving_candidates": sorted(improving),
        "declining_candidates": sorted(declining),
        "stable_candidates": sorted(stable),
    }
