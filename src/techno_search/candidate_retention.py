"""Candidate retention — tracks how long candidates remain in the pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CANDIDATE_RETENTION_SCHEMA_VERSION = "candidate_retention_v1"

CANDIDATE_RETENTION_DISCLAIMER = (
    "Candidate retention records are local scheduling and provenance aids only. "
    "Pipeline duration and current status reflect operational workflow state, "
    "not candidate quality or discovery probability. Long retention does not "
    "imply higher interest; short retention does not imply dismissal."
)

ALLOWED_RETENTION_STATUSES = frozenset(
    {
        "active",
        "awaiting_epoch",
        "under_review",
        "follow_up_scheduled",
        "archived",
        "rejected",
        "escalated",
    }
)


def _default_retention_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "candidate_retention.json"
    )


@dataclass
class CandidateRetentionRecord:
    record_id: str
    candidate_id: str
    track: str
    entered_pipeline_utc: str
    current_status: str
    days_in_pipeline: int
    last_activity_utc: str
    retention_reason: str = ""
    blocking_count: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "candidate_id": self.candidate_id,
            "track": self.track,
            "entered_pipeline_utc": self.entered_pipeline_utc,
            "current_status": self.current_status,
            "days_in_pipeline": self.days_in_pipeline,
            "last_activity_utc": self.last_activity_utc,
            "retention_reason": self.retention_reason,
            "blocking_count": self.blocking_count,
        }


def load_retention_records(
    fixture_path: Path | None = None,
) -> list[CandidateRetentionRecord]:
    path = fixture_path if fixture_path is not None else _default_retention_path()
    raw = json.loads(path.read_text())
    records = raw.get("records", [])
    result: list[CandidateRetentionRecord] = []
    for r in records:
        result.append(
            CandidateRetentionRecord(
                record_id=str(r["record_id"]),
                candidate_id=str(r["candidate_id"]),
                track=str(r["track"]),
                entered_pipeline_utc=str(r["entered_pipeline_utc"]),
                current_status=str(r["current_status"]),
                days_in_pipeline=int(r["days_in_pipeline"]),
                last_activity_utc=str(r["last_activity_utc"]),
                retention_reason=str(r.get("retention_reason", "")),
                blocking_count=int(r.get("blocking_count", 0)),
            )
        )
    return result


def candidate_retention_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    records = load_retention_records(fixture_path)

    by_track: dict[str, int] = {}
    by_status: dict[str, int] = {}
    active_count = 0
    archived_count = 0
    total_days = 0
    max_days = 0
    blocked_count = 0

    for rec in records:
        by_track[rec.track] = by_track.get(rec.track, 0) + 1
        by_status[rec.current_status] = by_status.get(rec.current_status, 0) + 1
        _active_statuses = (
            "active", "awaiting_epoch", "under_review", "follow_up_scheduled", "escalated"
        )
        if rec.current_status in _active_statuses:
            active_count += 1
        if rec.current_status in ("archived", "rejected"):
            archived_count += 1
        total_days += rec.days_in_pipeline
        if rec.days_in_pipeline > max_days:
            max_days = rec.days_in_pipeline
        if rec.blocking_count > 0:
            blocked_count += 1

    avg_days = round(total_days / len(records), 1) if records else 0.0

    return {
        "schema_version": CANDIDATE_RETENTION_SCHEMA_VERSION,
        "disclaimer": CANDIDATE_RETENTION_DISCLAIMER,
        "record_count": len(records),
        "unique_candidate_count": len({r.candidate_id for r in records}),
        "active_count": active_count,
        "archived_count": archived_count,
        "blocked_count": blocked_count,
        "average_days_in_pipeline": avg_days,
        "max_days_in_pipeline": max_days,
        "by_track": dict(sorted(by_track.items())),
        "by_status": dict(sorted(by_status.items())),
        "tracks_covered": sorted(by_track.keys()),
    }
