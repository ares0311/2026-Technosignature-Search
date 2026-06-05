"""Operational provenance records for personnel training and certification events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TRAINING_LOG_SCHEMA_VERSION = "training_log_v1"

ALLOWED_TRAINING_KINDS = frozenset(
    {
        "certification",
        "compliance_training",
        "onboarding",
        "skills_development",
        "vendor_training",
    }
)

ALLOWED_TRAINING_STATUSES = frozenset(
    {
        "completed",
        "expired",
        "in_progress",
        "scheduled",
    }
)

_DISCLAIMER = (
    "Training log entries are operational provenance records only. "
    "A training event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a "
    "detection claim."
)


def _default_fixture_path() -> Path:
    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "training_log.json"


@dataclass(frozen=True)
class TrainingEntry:
    entry_id: str
    training_kind: str
    status: str
    personnel_id: str
    training_topic: str
    notes: str = ""

    def __post_init__(self) -> None:
        if self.training_kind not in ALLOWED_TRAINING_KINDS:
            raise ValueError(f"invalid training_kind: {self.training_kind!r}")
        if self.status not in ALLOWED_TRAINING_STATUSES:
            raise ValueError(f"invalid status: {self.status!r}")


def load_training_entries(path: Path | None = None) -> list[TrainingEntry]:
    fixture_path = path if path is not None else _default_fixture_path()
    raw = json.loads(fixture_path.read_text(encoding="utf-8"))
    return [
        TrainingEntry(
            entry_id=str(entry["entry_id"]),
            training_kind=str(entry["training_kind"]),
            status=str(entry["status"]),
            personnel_id=str(entry["personnel_id"]),
            training_topic=str(entry["training_topic"]),
            notes=str(entry.get("notes", "")),
        )
        for entry in raw["entries"]
    ]


def training_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_training_entries(path)
    completed_count = sum(1 for e in entries if e.status == "completed")
    return {
        "schema_version": TRAINING_LOG_SCHEMA_VERSION,
        "disclaimer": _DISCLAIMER,
        "entry_count": len(entries),
        "completed_count": completed_count,
        "kind_counts": {
            kind: sum(1 for e in entries if e.training_kind == kind)
            for kind in sorted(ALLOWED_TRAINING_KINDS)
        },
        "status_counts": {
            status: sum(1 for e in entries if e.status == status)
            for status in sorted(ALLOWED_TRAINING_STATUSES)
        },
    }
