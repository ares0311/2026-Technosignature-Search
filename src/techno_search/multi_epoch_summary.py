"""Multi-epoch observation summary — scheduling aid for multi-epoch target tracking."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

MULTI_EPOCH_SCHEMA_VERSION = "multi_epoch_observations_v1"

MULTI_EPOCH_DISCLAIMER = (
    "Multi-epoch summaries are scheduling provenance records only. "
    "Inconsistent detections across epochs are expected and do not constitute "
    "confirmation. Consistent detection across epochs does not imply a "
    "technosignature without independent external validation."
)


def _default_multi_epoch_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "multi_epoch_observations.json"
    )


@dataclass
class MultiEpochRecord:
    target_id: str
    track: str
    epoch_count: int
    first_epoch_utc: str
    latest_epoch_utc: str
    status_per_epoch: list[str] = field(default_factory=list)
    consistent_detection: bool = False
    operator_notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id,
            "track": self.track,
            "epoch_count": self.epoch_count,
            "first_epoch_utc": self.first_epoch_utc,
            "latest_epoch_utc": self.latest_epoch_utc,
            "status_per_epoch": list(self.status_per_epoch),
            "consistent_detection": self.consistent_detection,
            "operator_notes": self.operator_notes,
        }


def load_multi_epoch_records(
    fixture_path: Path | None = None,
) -> list[MultiEpochRecord]:
    path = fixture_path or _default_multi_epoch_path()
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    records = []
    for raw in data.get("records", []):
        records.append(
            MultiEpochRecord(
                target_id=str(raw["target_id"]),
                track=str(raw["track"]),
                epoch_count=int(raw["epoch_count"]),
                first_epoch_utc=str(raw["first_epoch_utc"]),
                latest_epoch_utc=str(raw["latest_epoch_utc"]),
                status_per_epoch=list(raw.get("status_per_epoch", [])),
                consistent_detection=bool(raw.get("consistent_detection", False)),
                operator_notes=str(raw.get("operator_notes", "")),
            )
        )
    return records


def multi_epoch_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    """Return a summary of multi-epoch observation records."""

    records = load_multi_epoch_records(fixture_path)

    by_track: dict[str, int] = {}
    consistent_count = 0
    inconsistent_count = 0
    multi_epoch_count = 0
    total_epochs = 0

    for rec in records:
        by_track[rec.track] = by_track.get(rec.track, 0) + 1
        total_epochs += rec.epoch_count
        if rec.epoch_count > 1:
            multi_epoch_count += 1
        if rec.consistent_detection:
            consistent_count += 1
        else:
            inconsistent_count += 1

    target_count = len(records)
    mean_epoch_count = round(total_epochs / target_count, 4) if target_count > 0 else 0.0

    return {
        "schema_version": MULTI_EPOCH_SCHEMA_VERSION,
        "disclaimer": MULTI_EPOCH_DISCLAIMER,
        "target_count": target_count,
        "multi_epoch_target_count": multi_epoch_count,
        "consistent_detection_count": consistent_count,
        "inconsistent_detection_count": inconsistent_count,
        "mean_epoch_count": mean_epoch_count,
        "by_track": dict(sorted(by_track.items())),
        "tracks_covered": sorted(by_track.keys()),
    }
