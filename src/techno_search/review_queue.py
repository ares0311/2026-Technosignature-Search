"""Human-review queue fixture helpers."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from techno_search.schemas import Pathway, Track

REVIEW_QUEUE_SCHEMA_VERSION = "human_review_queue_v1"
REVIEW_QUEUE_DISCLAIMER = (
    "Human-review queue packets are triage aids only; they are not discovery claims."
)


class TriageLabel(StrEnum):
    """Allowed labels for conservative human-review queue triage."""

    NEEDS_HUMAN_REVIEW = "needs_human_review"
    LIKELY_FALSE_POSITIVE = "likely_false_positive"
    FOLLOW_UP_TARGET = "follow_up_target"
    KNOWN_OBJECT_ANNOTATION = "known_object_annotation"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


@dataclass(frozen=True)
class ReviewerNote:
    """A reviewer note attached to a human-review queue item."""

    reviewer_id: str
    created_at_utc: str
    note: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReviewQueueItem:
    """A conservative candidate triage item for human review."""

    candidate_id: str
    track: Track
    recommended_pathway: Pathway
    triage_label: TriageLabel
    source_packet_path: str
    review_packet_path: str
    negative_evidence_count: int
    blocking_issue_count: int
    reviewer_notes: tuple[ReviewerNote, ...] = ()


def allowed_triage_labels() -> tuple[str, ...]:
    """Return sorted allowed human-review triage label values."""

    return tuple(sorted(label.value for label in TriageLabel))


def default_review_queue_fixture_path() -> Path:
    """Return the repository-local human-review queue fixture path."""

    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / (
        "review_queue.json"
    )


def load_review_queue_items(path: Path | None = None) -> tuple[ReviewQueueItem, ...]:
    """Load and validate synthetic human-review queue fixture items."""

    fixture_path = path or default_review_queue_fixture_path()
    with fixture_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    schema_version = str(data.get("schema_version", ""))
    if schema_version != REVIEW_QUEUE_SCHEMA_VERSION:
        msg = (
            f"Unsupported review queue schema version {schema_version!r}; "
            f"expected {REVIEW_QUEUE_SCHEMA_VERSION!r}"
        )
        raise ValueError(msg)

    fixture_labels = tuple(str(label) for label in data.get("allowed_triage_labels", ()))
    if tuple(sorted(fixture_labels)) != allowed_triage_labels():
        msg = "Review queue fixture allowed triage labels do not match project labels"
        raise ValueError(msg)

    return tuple(_review_queue_item_from_mapping(item) for item in data["items"])


def review_queue_summary(path: Path | None = None) -> dict[str, object]:
    """Summarize synthetic human-review queue fixture coverage."""

    fixture_path = path or default_review_queue_fixture_path()
    items = load_review_queue_items(fixture_path)
    notes = [note for item in items for note in item.reviewer_notes]
    items_missing_notes = sorted(
        item.candidate_id for item in items if not item.reviewer_notes
    )

    return {
        "fixture_path": str(fixture_path),
        "schema_version": REVIEW_QUEUE_SCHEMA_VERSION,
        "disclaimer": REVIEW_QUEUE_DISCLAIMER,
        "item_count": len(items),
        "note_count": len(notes),
        "allowed_triage_labels": list(allowed_triage_labels()),
        "by_track": _counter_to_dict(Counter(item.track.value for item in items)),
        "by_triage_label": _counter_to_dict(
            Counter(item.triage_label.value for item in items)
        ),
        "by_recommended_pathway": _counter_to_dict(
            Counter(item.recommended_pathway.value for item in items)
        ),
        "items_missing_notes": items_missing_notes,
        "candidate_ids": sorted(item.candidate_id for item in items),
        "blocking_issue_total": sum(item.blocking_issue_count for item in items),
        "negative_evidence_total": sum(item.negative_evidence_count for item in items),
    }


def _review_queue_item_from_mapping(data: dict[str, Any]) -> ReviewQueueItem:
    return ReviewQueueItem(
        candidate_id=str(data["candidate_id"]),
        track=Track(str(data["track"])),
        recommended_pathway=Pathway(str(data["recommended_pathway"])),
        triage_label=TriageLabel(str(data["triage_label"])),
        source_packet_path=str(data["source_packet_path"]),
        review_packet_path=str(data["review_packet_path"]),
        negative_evidence_count=int(data.get("negative_evidence_count", 0)),
        blocking_issue_count=int(data.get("blocking_issue_count", 0)),
        reviewer_notes=tuple(
            _reviewer_note_from_mapping(note)
            for note in data.get("reviewer_notes", ())
        ),
    )


def _reviewer_note_from_mapping(data: dict[str, Any]) -> ReviewerNote:
    return ReviewerNote(
        reviewer_id=str(data["reviewer_id"]),
        created_at_utc=str(data["created_at_utc"]),
        note=str(data["note"]),
        tags=tuple(str(tag) for tag in data.get("tags", ())),
    )


def _counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items()))
