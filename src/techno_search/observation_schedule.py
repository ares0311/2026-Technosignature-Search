"""Observation schedule — scheduling aid for planned, completed, and cancelled windows."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

OBSERVATION_SCHEDULE_SCHEMA_VERSION = "observation_schedule_v1"

OBSERVATION_SCHEDULE_DISCLAIMER = (
    "Observation schedule entries are local scheduling aids only. "
    "Scheduled or completed windows do not constitute detection claims, "
    "confirmed technosignature observations, or authorizations for external submission."
)

ALLOWED_OBSERVATION_STATUSES = frozenset({"planned", "completed", "cancelled"})


def _default_schedule_fixture_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "observation_schedule.json"
    )


@dataclass
class ObservationWindow:
    window_id: str
    target_id: str
    track: str
    scheduled_utc: str
    duration_minutes: float
    priority_score: float
    status: str
    operator_notes: str = ""
    blocking_reasons: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "window_id": self.window_id,
            "target_id": self.target_id,
            "track": self.track,
            "scheduled_utc": self.scheduled_utc,
            "duration_minutes": self.duration_minutes,
            "priority_score": self.priority_score,
            "status": self.status,
            "operator_notes": self.operator_notes,
            "blocking_reasons": list(self.blocking_reasons),
        }


def load_observation_windows(
    fixture_path: Path | None = None,
) -> list[ObservationWindow]:
    path = fixture_path or _default_schedule_fixture_path()
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    windows = []
    for raw in data.get("windows", []):
        windows.append(
            ObservationWindow(
                window_id=str(raw["window_id"]),
                target_id=str(raw["target_id"]),
                track=str(raw["track"]),
                scheduled_utc=str(raw["scheduled_utc"]),
                duration_minutes=float(raw["duration_minutes"]),
                priority_score=float(raw["priority_score"]),
                status=str(raw["status"]),
                operator_notes=str(raw.get("operator_notes", "")),
                blocking_reasons=list(raw.get("blocking_reasons", [])),
            )
        )
    return windows


def observation_schedule_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    windows = load_observation_windows(fixture_path)

    by_status: dict[str, int] = {}
    by_track: dict[str, int] = {}
    total_minutes = 0.0
    for w in windows:
        by_status[w.status] = by_status.get(w.status, 0) + 1
        by_track[w.track] = by_track.get(w.track, 0) + 1
        total_minutes += w.duration_minutes

    planned_count = by_status.get("planned", 0)
    completed_count = by_status.get("completed", 0)
    cancelled_count = by_status.get("cancelled", 0)

    priority_sorted = sorted(windows, key=lambda w: w.priority_score, reverse=True)
    top_target_ids = [w.target_id for w in priority_sorted[:5]]

    return {
        "schema_version": OBSERVATION_SCHEDULE_SCHEMA_VERSION,
        "disclaimer": OBSERVATION_SCHEDULE_DISCLAIMER,
        "window_count": len(windows),
        "planned_count": planned_count,
        "completed_count": completed_count,
        "cancelled_count": cancelled_count,
        "by_track": dict(sorted(by_track.items())),
        "total_scheduled_minutes": total_minutes,
        "top_priority_target_ids": top_target_ids,
        "operator_note_count": sum(1 for w in windows if w.operator_notes),
    }
