"""Target priority recalibration summary — scheduling aid for priority ordering comparison."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

TARGET_RECALIBRATION_SCHEMA_VERSION = "target_priority_snapshots_v1"

TARGET_RECALIBRATION_DISCLAIMER = (
    "Target priority recalibration summaries are scheduling aids only. "
    "Priority rank changes do not modify candidate scores or posteriors and "
    "are not detection evidence. A change in priority ordering does not "
    "constitute a discovery claim or authorization for external submission."
)


def _default_snapshots_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "target_priority_snapshots.json"
    )


@dataclass
class TargetPrioritySnapshot:
    snapshot_id: str
    snapshot_utc: str
    ordered_target_ids: list[str] = field(default_factory=list)
    priority_scores: dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "snapshot_utc": self.snapshot_utc,
            "ordered_target_ids": list(self.ordered_target_ids),
            "priority_scores": dict(self.priority_scores),
        }


def load_priority_snapshots(
    fixture_path: Path | None = None,
) -> list[TargetPrioritySnapshot]:
    path = fixture_path or _default_snapshots_path()
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    snapshots = []
    for raw in data.get("snapshots", []):
        snapshots.append(
            TargetPrioritySnapshot(
                snapshot_id=str(raw["snapshot_id"]),
                snapshot_utc=str(raw["snapshot_utc"]),
                ordered_target_ids=list(raw.get("ordered_target_ids", [])),
                priority_scores={
                    str(k): float(v)
                    for k, v in raw.get("priority_scores", {}).items()
                },
            )
        )
    return snapshots


def target_recalibration_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    """Compare the two most recent priority snapshots and report rank changes."""

    snapshots = load_priority_snapshots(fixture_path)
    snapshot_count = len(snapshots)

    if snapshot_count < 2:
        return {
            "schema_version": TARGET_RECALIBRATION_SCHEMA_VERSION,
            "disclaimer": TARGET_RECALIBRATION_DISCLAIMER,
            "snapshot_count": snapshot_count,
            "ok": snapshot_count >= 2,
            "rank_change_count": 0,
            "new_top_target_id": None,
            "previous_top_target_id": None,
            "top_changed": False,
            "mean_absolute_rank_change": 0.0,
        }

    current = snapshots[-1]
    previous = snapshots[-2]

    current_ranks = {tid: i for i, tid in enumerate(current.ordered_target_ids)}
    previous_ranks = {tid: i for i, tid in enumerate(previous.ordered_target_ids)}

    shared_targets = set(current_ranks) & set(previous_ranks)
    rank_changes = [
        abs(current_ranks[tid] - previous_ranks[tid]) for tid in shared_targets
    ]
    rank_change_count = sum(1 for c in rank_changes if c > 0)
    mean_abs_rank_change = (
        round(sum(rank_changes) / len(rank_changes), 4) if rank_changes else 0.0
    )

    new_top = current.ordered_target_ids[0] if current.ordered_target_ids else None
    previous_top = previous.ordered_target_ids[0] if previous.ordered_target_ids else None

    return {
        "schema_version": TARGET_RECALIBRATION_SCHEMA_VERSION,
        "disclaimer": TARGET_RECALIBRATION_DISCLAIMER,
        "snapshot_count": snapshot_count,
        "ok": snapshot_count >= 2,
        "current_snapshot_id": current.snapshot_id,
        "previous_snapshot_id": previous.snapshot_id,
        "shared_target_count": len(shared_targets),
        "rank_change_count": rank_change_count,
        "new_top_target_id": new_top,
        "previous_top_target_id": previous_top,
        "top_changed": new_top != previous_top,
        "mean_absolute_rank_change": mean_abs_rank_change,
    }
