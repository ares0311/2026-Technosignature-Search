"""Operational provenance records for signal classification events."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SIGNAL_CLASSIFICATION_SCHEMA_VERSION = "signal_classification_log_v1"

SIGNAL_CLASSIFICATION_DISCLAIMER = (
    "Signal classification entries are operational provenance records. "
    "A classification does not confirm or rule out technosignature interest, "
    "does not modify candidate scores or pathway routing, "
    "and does not authorize external submission or constitute a detection claim."
)

ALLOWED_CLASSIFICATION_KINDS = frozenset({
    "narrowband", "broadband", "pulsed", "intermittent", "unknown",
})

ALLOWED_CLASSIFICATION_STATUSES = frozenset({
    "classified", "unclassified", "ambiguous", "reclassified",
})


def _default_signal_classification_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "signal_classification_log.json"
    )


@dataclass
class SignalClassificationEntry:
    entry_id: str
    candidate_id: str
    classification_kind: str
    status: str
    classified_by: str
    classified_at: str
    track: str
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "candidate_id": self.candidate_id,
            "classification_kind": self.classification_kind,
            "status": self.status,
            "classified_by": self.classified_by,
            "classified_at": self.classified_at,
            "track": self.track,
            "notes": self.notes,
        }


def load_signal_classification_entries(
    path: Path | None = None,
) -> list[SignalClassificationEntry]:
    fpath = path or _default_signal_classification_path()
    with open(fpath) as f:
        data = json.load(f)
    entries = []
    for item in data.get("signal_classification_entries", []):
        entries.append(SignalClassificationEntry(
            entry_id=item["entry_id"],
            candidate_id=item["candidate_id"],
            classification_kind=item["classification_kind"],
            status=item["status"],
            classified_by=item["classified_by"],
            classified_at=item["classified_at"],
            track=item["track"],
            notes=item.get("notes", ""),
        ))
    return entries


def signal_classification_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_signal_classification_entries(path)
    by_status: dict[str, int] = {}
    by_classification_kind: dict[str, int] = {}
    by_track: dict[str, int] = {}
    for e in entries:
        by_status[e.status] = by_status.get(e.status, 0) + 1
        by_classification_kind[e.classification_kind] = (
            by_classification_kind.get(e.classification_kind, 0) + 1
        )
        by_track[e.track] = by_track.get(e.track, 0) + 1
    return {
        "schema_version": SIGNAL_CLASSIFICATION_SCHEMA_VERSION,
        "disclaimer": SIGNAL_CLASSIFICATION_DISCLAIMER,
        "entry_count": len(entries),
        "classified_count": by_status.get("classified", 0),
        "unclassified_count": by_status.get("unclassified", 0),
        "ambiguous_count": by_status.get("ambiguous", 0),
        "reclassified_count": by_status.get("reclassified", 0),
        "by_status": by_status,
        "by_classification_kind": by_classification_kind,
        "by_track": by_track,
    }
