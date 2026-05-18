"""ML model performance history — local scheduling records only, not survey metrics."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

MODEL_PERFORMANCE_HISTORY_SCHEMA_VERSION = "model_performance_history_v1"

MODEL_PERFORMANCE_HISTORY_DISCLAIMER = (
    "Model performance snapshots are local scheduling records for model development only. "
    "They are not calibrated survey efficiency estimates, detections, discoveries, "
    "or external validation."
)

ALLOWED_TRENDS = frozenset({"improving", "declining", "stable"})


def _default_history_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "model_performance_history.json"
    )


@dataclass
class ModelPerformanceSnapshot:
    snapshot_id: str
    model_id: str
    track: str
    epoch: int
    accuracy: float
    loss: float
    trend: str
    snapshot_utc: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "model_id": self.model_id,
            "track": self.track,
            "epoch": self.epoch,
            "accuracy": self.accuracy,
            "loss": self.loss,
            "trend": self.trend,
            "snapshot_utc": self.snapshot_utc,
        }


def load_model_performance_snapshots(
    fixture_path: Path | None = None,
) -> list[ModelPerformanceSnapshot]:
    import json

    path = fixture_path or _default_history_path()
    with path.open(encoding="utf-8") as fh:
        raw = json.load(fh)

    snapshots = []
    for item in raw.get("snapshots", []):
        snapshots.append(
            ModelPerformanceSnapshot(
                snapshot_id=item["snapshot_id"],
                model_id=item["model_id"],
                track=item["track"],
                epoch=int(item["epoch"]),
                accuracy=float(item["accuracy"]),
                loss=float(item["loss"]),
                trend=item["trend"],
                snapshot_utc=item["snapshot_utc"],
            )
        )
    return snapshots


def model_performance_history_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    snapshots = load_model_performance_snapshots(fixture_path)

    by_model: dict[str, int] = {}
    by_track: dict[str, int] = {}
    by_trend: dict[str, int] = {}

    latest_by_model: dict[str, ModelPerformanceSnapshot] = {}

    for s in snapshots:
        by_model[s.model_id] = by_model.get(s.model_id, 0) + 1
        by_track[s.track] = by_track.get(s.track, 0) + 1
        by_trend[s.trend] = by_trend.get(s.trend, 0) + 1
        if (
            s.model_id not in latest_by_model
            or s.epoch > latest_by_model[s.model_id].epoch
        ):
            latest_by_model[s.model_id] = s

    most_recent = {
        mid: s.as_dict() for mid, s in latest_by_model.items()
    }

    return {
        "disclaimer": MODEL_PERFORMANCE_HISTORY_DISCLAIMER,
        "schema_version": MODEL_PERFORMANCE_HISTORY_SCHEMA_VERSION,
        "snapshot_count": len(snapshots),
        "unique_model_count": len(by_model),
        "by_model": by_model,
        "by_track": by_track,
        "by_trend": by_trend,
        "most_recent_snapshot_by_model": most_recent,
    }
