"""Session log module — per-observation session records."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SESSION_LOG_SCHEMA_VERSION = "session_log_v1"

SESSION_LOG_DISCLAIMER = (
    "Session log entries are local scheduling and provenance records only. "
    "Session outcomes reflect operational execution status — a 'completed' "
    "session means all planned observations were executed, not that any "
    "candidate signal was confirmed or that science conclusions are final. "
    "Duration and outcome fields are workflow metadata, not scientific assessments."
)

ALLOWED_SESSION_OUTCOMES = frozenset(
    {"completed", "partial", "aborted", "rescheduled", "failed"}
)


def _default_fixture_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "session_log.json"
    )


@dataclass
class SessionLogEntry:
    session_id: str
    campaign_id: str
    track: str
    operator_id: str
    session_utc: str
    duration_minutes: int
    outcome: str
    notes: str
    candidates_observed: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "campaign_id": self.campaign_id,
            "track": self.track,
            "operator_id": self.operator_id,
            "session_utc": self.session_utc,
            "duration_minutes": self.duration_minutes,
            "outcome": self.outcome,
            "notes": self.notes,
            "candidates_observed": self.candidates_observed,
        }


def load_session_log_entries(fixture_path: Path | None = None) -> list[SessionLogEntry]:
    path = fixture_path or _default_fixture_path()
    with Path(path).open(encoding="utf-8") as fh:
        data = json.load(fh)
    entries = []
    for item in data.get("sessions", []):
        entries.append(
            SessionLogEntry(
                session_id=item["session_id"],
                campaign_id=item["campaign_id"],
                track=item["track"],
                operator_id=item["operator_id"],
                session_utc=item["session_utc"],
                duration_minutes=int(item.get("duration_minutes", 0)),
                outcome=item["outcome"],
                notes=item.get("notes", ""),
                candidates_observed=list(item.get("candidates_observed", [])),
            )
        )
    return entries


def session_log_summary(fixture_path: Path | None = None) -> dict[str, Any]:
    entries = load_session_log_entries(fixture_path)

    completed_count = sum(1 for e in entries if e.outcome == "completed")
    aborted_count = sum(1 for e in entries if e.outcome == "aborted")
    total_duration = sum(e.duration_minutes for e in entries)
    average_duration = round(total_duration / len(entries), 1) if entries else 0.0

    by_track: dict[str, int] = {}
    by_outcome: dict[str, int] = {}
    operator_ids: set[str] = set()
    all_candidates: set[str] = set()

    for e in entries:
        by_track[e.track] = by_track.get(e.track, 0) + 1
        by_outcome[e.outcome] = by_outcome.get(e.outcome, 0) + 1
        if e.operator_id:
            operator_ids.add(e.operator_id)
        all_candidates.update(e.candidates_observed)

    return {
        "schema_version": SESSION_LOG_SCHEMA_VERSION,
        "disclaimer": SESSION_LOG_DISCLAIMER,
        "session_count": len(entries),
        "completed_count": completed_count,
        "aborted_count": aborted_count,
        "total_duration_minutes": total_duration,
        "average_duration_minutes": average_duration,
        "unique_candidates_observed": len(all_candidates),
        "by_track": dict(sorted(by_track.items())),
        "by_outcome": dict(sorted(by_outcome.items())),
        "tracks_covered": sorted(by_track.keys()),
        "unique_operators": len(operator_ids),
    }
