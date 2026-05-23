"""Operator provenance records for candidate annotation events."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CANDIDATE_ANNOTATION_LOG_SCHEMA_VERSION = "candidate_annotation_log_v1"

CANDIDATE_ANNOTATION_LOG_DISCLAIMER = (
    "Candidate annotation entries are operator provenance records. "
    "Annotations do not modify candidate posteriors, scores, or pathway routing, "
    "and do not authorize external submission or constitute a detection claim."
)

ALLOWED_ANNOTATION_LOG_KINDS = frozenset({
    "manual_tag", "automated_flag", "cross_reference", "operator_note",
    "classification_hint",
})

ALLOWED_ANNOTATION_LOG_STATUSES = frozenset({
    "active", "superseded", "withdrawn",
})


def _default_candidate_annotation_log_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "candidate_annotation_log.json"
    )


@dataclass
class CandidateAnnotationLogEntry:
    entry_id: str
    candidate_id: str
    annotation_kind: str
    status: str
    annotated_by: str
    annotated_at: str
    track: str
    annotation_text: str
    supersedes_entry_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "candidate_id": self.candidate_id,
            "annotation_kind": self.annotation_kind,
            "status": self.status,
            "annotated_by": self.annotated_by,
            "annotated_at": self.annotated_at,
            "track": self.track,
            "annotation_text": self.annotation_text,
            "supersedes_entry_id": self.supersedes_entry_id,
        }


def load_candidate_annotation_log_entries(
    path: Path | None = None,
) -> list[CandidateAnnotationLogEntry]:
    fpath = path or _default_candidate_annotation_log_path()
    with open(fpath) as f:
        data = json.load(f)
    entries = []
    for item in data.get("candidate_annotation_log_entries", []):
        entries.append(CandidateAnnotationLogEntry(
            entry_id=item["entry_id"],
            candidate_id=item["candidate_id"],
            annotation_kind=item["annotation_kind"],
            status=item["status"],
            annotated_by=item["annotated_by"],
            annotated_at=item["annotated_at"],
            track=item["track"],
            annotation_text=item["annotation_text"],
            supersedes_entry_id=item.get("supersedes_entry_id"),
        ))
    return entries


def candidate_annotation_log_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_candidate_annotation_log_entries(path)
    by_status: dict[str, int] = {}
    by_annotation_kind: dict[str, int] = {}
    by_track: dict[str, int] = {}
    for e in entries:
        by_status[e.status] = by_status.get(e.status, 0) + 1
        by_annotation_kind[e.annotation_kind] = (
            by_annotation_kind.get(e.annotation_kind, 0) + 1
        )
        by_track[e.track] = by_track.get(e.track, 0) + 1
    return {
        "schema_version": CANDIDATE_ANNOTATION_LOG_SCHEMA_VERSION,
        "disclaimer": CANDIDATE_ANNOTATION_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "active_count": by_status.get("active", 0),
        "superseded_count": by_status.get("superseded", 0),
        "withdrawn_count": by_status.get("withdrawn", 0),
        "by_status": by_status,
        "by_annotation_kind": by_annotation_kind,
        "by_track": by_track,
    }
