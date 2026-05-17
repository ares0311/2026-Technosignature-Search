"""Candidate annotation module — operator annotations and tags on candidates."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CANDIDATE_ANNOTATION_SCHEMA_VERSION = "candidate_annotation_v1"

CANDIDATE_ANNOTATION_DISCLAIMER = (
    "Candidate annotations are operator notes and tags for scheduling provenance "
    "only. Annotations do not modify candidate scores, posteriors, or pathway "
    "routing. A 'warning' annotation reflects an operator's scheduling concern — "
    "it does not constitute a scientific assessment of candidate validity. "
    "Annotation content is not evidence of a technosignature."
)

ALLOWED_ANNOTATION_TYPES = frozenset(
    {"note", "tag", "warning", "highlight", "question", "followup"}
)


def _default_fixture_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "candidate_annotations.json"
    )


@dataclass
class CandidateAnnotation:
    annotation_id: str
    candidate_id: str
    track: str
    annotation_type: str
    content: str
    operator_id: str
    created_utc: str
    is_resolved: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "annotation_id": self.annotation_id,
            "candidate_id": self.candidate_id,
            "track": self.track,
            "annotation_type": self.annotation_type,
            "content": self.content,
            "operator_id": self.operator_id,
            "created_utc": self.created_utc,
            "is_resolved": self.is_resolved,
        }


def load_candidate_annotations(
    fixture_path: Path | None = None,
) -> list[CandidateAnnotation]:
    path = fixture_path or _default_fixture_path()
    with Path(path).open(encoding="utf-8") as fh:
        data = json.load(fh)
    annotations = []
    for item in data.get("annotations", []):
        annotations.append(
            CandidateAnnotation(
                annotation_id=item["annotation_id"],
                candidate_id=item["candidate_id"],
                track=item["track"],
                annotation_type=item["annotation_type"],
                content=item.get("content", ""),
                operator_id=item["operator_id"],
                created_utc=item["created_utc"],
                is_resolved=bool(item.get("is_resolved", False)),
            )
        )
    return annotations


def candidate_annotation_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    annotations = load_candidate_annotations(fixture_path)

    unresolved_count = sum(1 for a in annotations if not a.is_resolved)

    by_track: dict[str, int] = {}
    by_type: dict[str, int] = {}
    operator_ids: set[str] = set()

    for a in annotations:
        by_track[a.track] = by_track.get(a.track, 0) + 1
        by_type[a.annotation_type] = by_type.get(a.annotation_type, 0) + 1
        if a.operator_id:
            operator_ids.add(a.operator_id)

    return {
        "schema_version": CANDIDATE_ANNOTATION_SCHEMA_VERSION,
        "disclaimer": CANDIDATE_ANNOTATION_DISCLAIMER,
        "annotation_count": len(annotations),
        "unresolved_count": unresolved_count,
        "by_track": dict(sorted(by_track.items())),
        "by_type": dict(sorted(by_type.items())),
        "tracks_covered": sorted(by_track.keys()),
        "unique_operators": len(operator_ids),
    }
