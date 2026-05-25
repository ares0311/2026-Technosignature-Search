"""Labeled candidate dataset for scoring model evaluation and future training."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LABELED_DATASET_SCHEMA_VERSION = "labeled_candidates_v1"
LABELED_DATASET_DISCLAIMER = (
    "Labeled candidate dataset entries are synthetic ground-truth annotations "
    "for local model evaluation only. Labels are not detection claims, do not "
    "authorize external submission, and do not constitute peer-reviewed evidence."
)

ALLOWED_LABELS = frozenset({
    "false_positive",
    "known_object",
    "follow_up",
    "insufficient_evidence",
})


@dataclass
class LabeledCandidate:
    entry_id: str
    candidate_id: str
    track: str
    label: str
    label_confidence: float
    labeled_by: str
    labeled_at: str
    false_positive_class: str | None
    candidate: dict[str, Any]
    notes: str

    def __post_init__(self) -> None:
        if self.label not in ALLOWED_LABELS:
            msg = f"Invalid label '{self.label}'. Expected: {sorted(ALLOWED_LABELS)}"
            raise ValueError(msg)
        if not 0.0 <= self.label_confidence <= 1.0:
            msg = "label_confidence must be between 0.0 and 1.0"
            raise ValueError(msg)


def load_labeled_candidates(path: Path) -> list[LabeledCandidate]:
    data = json.loads(path.read_text())
    entries = data.get("entries", [])
    result = []
    for e in entries:
        result.append(LabeledCandidate(
            entry_id=e["entry_id"],
            candidate_id=e["candidate_id"],
            track=e["track"],
            label=e["label"],
            label_confidence=float(e["label_confidence"]),
            labeled_by=e["labeled_by"],
            labeled_at=e["labeled_at"],
            false_positive_class=e.get("false_positive_class"),
            candidate=e.get("candidate", {}),
            notes=e.get("notes", ""),
        ))
    return result


def labeled_dataset_summary(path: Path | None = None) -> dict[str, Any]:
    if path is None:
        path = (
            Path(__file__).parent.parent.parent / "tests" / "fixtures" / "labeled_candidates.json"
        )
    entries = load_labeled_candidates(path)
    counts_by_label: dict[str, int] = {}
    counts_by_track: dict[str, int] = {}
    fp_classes: dict[str, int] = {}
    for e in entries:
        counts_by_label[e.label] = counts_by_label.get(e.label, 0) + 1
        counts_by_track[e.track] = counts_by_track.get(e.track, 0) + 1
        if e.false_positive_class:
            fp_classes[e.false_positive_class] = fp_classes.get(e.false_positive_class, 0) + 1
    return {
        "schema_version": LABELED_DATASET_SCHEMA_VERSION,
        "disclaimer": LABELED_DATASET_DISCLAIMER,
        "entry_count": len(entries),
        "false_positive_count": counts_by_label.get("false_positive", 0),
        "known_object_count": counts_by_label.get("known_object", 0),
        "follow_up_count": counts_by_label.get("follow_up", 0),
        "insufficient_evidence_count": counts_by_label.get("insufficient_evidence", 0),
        "counts_by_label": counts_by_label,
        "counts_by_track": counts_by_track,
        "false_positive_classes": fp_classes,
    }
