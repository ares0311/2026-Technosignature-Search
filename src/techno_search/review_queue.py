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
CONSENSUS_LABEL_SCHEMA_VERSION = "human_review_consensus_labels_v1"
CONSENSUS_LABEL_DISCLAIMER = (
    "Human-review consensus labels are triage summaries only; they are not discovery "
    "claims or external validation."
)
CONSENSUS_EXPORT_SCHEMA_VERSION = "human_review_consensus_export_v1"
CONSENSUS_EXPORT_DISCLAIMER = (
    "Consensus exports are conservative review handoff summaries only; they are not "
    "discovery claims, detections, or external validation."
)


class TriageLabel(StrEnum):
    """Allowed labels for conservative human-review queue triage."""

    NEEDS_HUMAN_REVIEW = "needs_human_review"
    LIKELY_FALSE_POSITIVE = "likely_false_positive"
    FOLLOW_UP_TARGET = "follow_up_target"
    KNOWN_OBJECT_ANNOTATION = "known_object_annotation"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class ConsensusLabel(StrEnum):
    """Allowed conservative consensus labels across repeated reviewer decisions."""

    FOLLOW_UP_TARGET = "follow_up_target"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    KNOWN_OBJECT_ANNOTATION = "known_object_annotation"
    LIKELY_FALSE_POSITIVE = "likely_false_positive"
    NO_CONSENSUS = "no_consensus"


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


@dataclass(frozen=True)
class ConsensusDecision:
    """One reviewer decision contributing to a conservative consensus label."""

    reviewer_id: str
    triage_label: TriageLabel
    created_at_utc: str
    rationale: str


@dataclass(frozen=True)
class ConsensusItem:
    """Repeated reviewer decisions and resulting conservative consensus label."""

    candidate_id: str
    track: Track
    consensus_label: ConsensusLabel
    reviewer_decisions: tuple[ConsensusDecision, ...]


@dataclass(frozen=True)
class ConsensusExportItem:
    """One conservative consensus-label export item."""

    candidate_id: str
    track: Track
    consensus_label: ConsensusLabel
    export_path: str
    evidence_summary: str
    negative_evidence_count: int
    blocking_issue_count: int
    reviewer_decision_count: int


def allowed_triage_labels() -> tuple[str, ...]:
    """Return sorted allowed human-review triage label values."""

    return tuple(sorted(label.value for label in TriageLabel))


def allowed_consensus_labels() -> tuple[str, ...]:
    """Return sorted allowed human-review consensus label values."""

    return tuple(sorted(label.value for label in ConsensusLabel))


def default_review_queue_fixture_path() -> Path:
    """Return the repository-local human-review queue fixture path."""

    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / (
        "review_queue.json"
    )


def default_consensus_label_fixture_path() -> Path:
    """Return the repository-local human-review consensus fixture path."""

    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / (
        "consensus_labels.json"
    )


def default_consensus_export_fixture_path() -> Path:
    """Return the repository-local human-review consensus export fixture path."""

    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / (
        "consensus_exports.json"
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


def load_consensus_items(path: Path | None = None) -> tuple[ConsensusItem, ...]:
    """Load and validate synthetic human-review consensus label fixture items."""

    fixture_path = path or default_consensus_label_fixture_path()
    with fixture_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    schema_version = str(data.get("schema_version", ""))
    if schema_version != CONSENSUS_LABEL_SCHEMA_VERSION:
        msg = (
            f"Unsupported consensus label schema version {schema_version!r}; "
            f"expected {CONSENSUS_LABEL_SCHEMA_VERSION!r}"
        )
        raise ValueError(msg)

    fixture_labels = tuple(str(label) for label in data.get("allowed_consensus_labels", ()))
    if tuple(sorted(fixture_labels)) != allowed_consensus_labels():
        msg = "Consensus fixture allowed labels do not match project labels"
        raise ValueError(msg)

    return tuple(_consensus_item_from_mapping(item) for item in data["items"])


def load_consensus_export_items(path: Path | None = None) -> tuple[ConsensusExportItem, ...]:
    """Load synthetic human-review consensus export fixture items."""

    fixture_path = path or default_consensus_export_fixture_path()
    with fixture_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    schema_version = str(data.get("schema_version", ""))
    if schema_version != CONSENSUS_EXPORT_SCHEMA_VERSION:
        msg = (
            f"Unsupported consensus export schema version {schema_version!r}; "
            f"expected {CONSENSUS_EXPORT_SCHEMA_VERSION!r}"
        )
        raise ValueError(msg)

    disclaimer = str(data.get("disclaimer", ""))
    if "not discovery claims" not in disclaimer:
        msg = "Consensus export fixture must preserve conservative disclaimer language"
        raise ValueError(msg)

    return tuple(_consensus_export_item_from_mapping(item) for item in data["exports"])


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


def consensus_summary(path: Path | None = None) -> dict[str, object]:
    """Summarize synthetic human-review consensus label fixture coverage."""

    fixture_path = path or default_consensus_label_fixture_path()
    items = load_consensus_items(fixture_path)
    decisions = [decision for item in items for decision in item.reviewer_decisions]

    return {
        "fixture_path": str(fixture_path),
        "schema_version": CONSENSUS_LABEL_SCHEMA_VERSION,
        "disclaimer": CONSENSUS_LABEL_DISCLAIMER,
        "item_count": len(items),
        "decision_count": len(decisions),
        "unique_reviewer_count": len({decision.reviewer_id for decision in decisions}),
        "allowed_consensus_labels": list(allowed_consensus_labels()),
        "by_track": _counter_to_dict(Counter(item.track.value for item in items)),
        "by_consensus_label": _counter_to_dict(
            Counter(item.consensus_label.value for item in items)
        ),
        "by_decision_label": _counter_to_dict(
            Counter(decision.triage_label.value for decision in decisions)
        ),
        "by_reviewer_decision_count": _counter_to_dict(
            Counter(str(len(item.reviewer_decisions)) for item in items)
        ),
        "candidate_ids": sorted(item.candidate_id for item in items),
    }


def consensus_export_summary(path: Path | None = None) -> dict[str, object]:
    """Summarize synthetic human-review consensus export fixture coverage."""

    fixture_path = path or default_consensus_export_fixture_path()
    items = load_consensus_export_items(fixture_path)
    return {
        "fixture_path": str(fixture_path),
        "schema_version": CONSENSUS_EXPORT_SCHEMA_VERSION,
        "disclaimer": CONSENSUS_EXPORT_DISCLAIMER,
        "export_count": len(items),
        "reviewer_decision_total": sum(item.reviewer_decision_count for item in items),
        "negative_evidence_total": sum(item.negative_evidence_count for item in items),
        "blocking_issue_total": sum(item.blocking_issue_count for item in items),
        "by_track": _counter_to_dict(Counter(item.track.value for item in items)),
        "by_consensus_label": _counter_to_dict(
            Counter(item.consensus_label.value for item in items)
        ),
        "candidate_ids": sorted(item.candidate_id for item in items),
        "export_paths": sorted(item.export_path for item in items),
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


def _consensus_item_from_mapping(data: dict[str, Any]) -> ConsensusItem:
    decisions = tuple(
        _consensus_decision_from_mapping(decision)
        for decision in data.get("reviewer_decisions", ())
    )
    if not decisions:
        msg = f"Consensus item {data.get('candidate_id')!r} must include decisions"
        raise ValueError(msg)
    return ConsensusItem(
        candidate_id=str(data["candidate_id"]),
        track=Track(str(data["track"])),
        consensus_label=ConsensusLabel(str(data["consensus_label"])),
        reviewer_decisions=decisions,
    )


def _consensus_decision_from_mapping(data: dict[str, Any]) -> ConsensusDecision:
    return ConsensusDecision(
        reviewer_id=str(data["reviewer_id"]),
        triage_label=TriageLabel(str(data["triage_label"])),
        created_at_utc=str(data["created_at_utc"]),
        rationale=str(data["rationale"]),
    )


def _consensus_export_item_from_mapping(data: dict[str, Any]) -> ConsensusExportItem:
    return ConsensusExportItem(
        candidate_id=str(data["candidate_id"]),
        track=Track(str(data["track"])),
        consensus_label=ConsensusLabel(str(data["consensus_label"])),
        export_path=str(data["export_path"]),
        evidence_summary=str(data["evidence_summary"]),
        negative_evidence_count=int(data["negative_evidence_count"]),
        blocking_issue_count=int(data["blocking_issue_count"]),
        reviewer_decision_count=int(data["reviewer_decision_count"]),
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
