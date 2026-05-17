"""Candidate resolution — tracks final disposition of candidates after review."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CANDIDATE_RESOLUTION_SCHEMA_VERSION = "candidate_resolution_v1"

CANDIDATE_RESOLUTION_DISCLAIMER = (
    "Candidate resolution records are local scheduling closure records only. "
    "Resolution status reflects internal workflow disposition, not external "
    "validation or confirmation of any technosignature. 'resolved_fp' means "
    "the candidate was internally assessed as a false positive — not that "
    "it has been scientifically ruled out by independent observation."
)

ALLOWED_RESOLUTION_STATUSES = frozenset(
    {
        "resolved_fp",
        "unresolved",
        "awaiting_confirmation",
        "deferred",
        "inconclusive",
        "follow_up_scheduled",
    }
)


def _default_resolution_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "candidate_resolution.json"
    )


@dataclass
class CandidateResolutionRecord:
    record_id: str
    candidate_id: str
    track: str
    resolution_status: str
    resolved_by: str
    resolution_utc: str
    days_to_resolution: int
    blocking_reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "candidate_id": self.candidate_id,
            "track": self.track,
            "resolution_status": self.resolution_status,
            "resolved_by": self.resolved_by,
            "resolution_utc": self.resolution_utc,
            "days_to_resolution": self.days_to_resolution,
            "blocking_reason": self.blocking_reason,
        }


def load_resolution_records(
    fixture_path: Path | None = None,
) -> list[CandidateResolutionRecord]:
    path = fixture_path if fixture_path is not None else _default_resolution_path()
    raw = json.loads(path.read_text())
    records = raw.get("records", [])
    result: list[CandidateResolutionRecord] = []
    for r in records:
        result.append(
            CandidateResolutionRecord(
                record_id=str(r["record_id"]),
                candidate_id=str(r["candidate_id"]),
                track=str(r["track"]),
                resolution_status=str(r["resolution_status"]),
                resolved_by=str(r["resolved_by"]),
                resolution_utc=str(r["resolution_utc"]),
                days_to_resolution=int(r["days_to_resolution"]),
                blocking_reason=str(r.get("blocking_reason", "")),
            )
        )
    return result


def candidate_resolution_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    records = load_resolution_records(fixture_path)

    by_track: dict[str, int] = {}
    by_status: dict[str, int] = {}
    unresolved_count = 0
    resolved_fp_count = 0
    total_days = 0
    max_days = 0

    for rec in records:
        by_track[rec.track] = by_track.get(rec.track, 0) + 1
        by_status[rec.resolution_status] = by_status.get(rec.resolution_status, 0) + 1
        if rec.resolution_status == "unresolved":
            unresolved_count += 1
        if rec.resolution_status == "resolved_fp":
            resolved_fp_count += 1
        total_days += rec.days_to_resolution
        if rec.days_to_resolution > max_days:
            max_days = rec.days_to_resolution

    avg_days = round(total_days / len(records), 1) if records else 0.0
    unique_operators = {r.resolved_by for r in records if r.resolved_by}

    return {
        "schema_version": CANDIDATE_RESOLUTION_SCHEMA_VERSION,
        "disclaimer": CANDIDATE_RESOLUTION_DISCLAIMER,
        "record_count": len(records),
        "unique_candidate_count": len({r.candidate_id for r in records}),
        "unresolved_count": unresolved_count,
        "resolved_fp_count": resolved_fp_count,
        "average_days_to_resolution": avg_days,
        "max_days_to_resolution": max_days,
        "by_track": dict(sorted(by_track.items())),
        "by_status": dict(sorted(by_status.items())),
        "tracks_covered": sorted(by_track.keys()),
        "unique_operator_count": len(unique_operators),
    }
