"""Candidate flags — quality flags and operational alerts raised against candidates."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CANDIDATE_FLAGS_SCHEMA_VERSION = "candidate_flags_v1"

CANDIDATE_FLAGS_DISCLAIMER = (
    "Candidate flag records are local scheduling and quality-control aids only. "
    "They surface data-quality issues, RFI indicators, and operational blockers "
    "for operator review. They do not constitute evidence of a technosignature, "
    "detection, or discovery, and do not modify candidate pathway routing."
)

ALLOWED_FLAG_SEVERITIES = frozenset({"critical", "high", "medium", "low", "info"})

ALLOWED_FLAG_TYPES = frozenset(
    {
        "rfi_suspected",
        "data_quality_low",
        "needs_reobservation",
        "catalog_mismatch",
        "photometry_artifact",
        "satellite_interference",
        "pipeline_error",
        "operator_note",
        "scheduling_conflict",
        "provenance_incomplete",
    }
)

ALLOWED_FLAG_STATUSES = frozenset({"open", "acknowledged", "resolved", "dismissed"})


def _default_flags_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "candidate_flags.json"
    )


@dataclass
class CandidateFlag:
    flag_id: str
    candidate_id: str
    track: str
    flag_type: str
    severity: str
    raised_by: str
    raised_utc: str
    status: str
    resolution_notes: str = ""
    related_observation_id: str = ""
    tags: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "flag_id": self.flag_id,
            "candidate_id": self.candidate_id,
            "track": self.track,
            "flag_type": self.flag_type,
            "severity": self.severity,
            "raised_by": self.raised_by,
            "raised_utc": self.raised_utc,
            "status": self.status,
            "resolution_notes": self.resolution_notes,
            "related_observation_id": self.related_observation_id,
            "tags": list(self.tags),
        }


def load_candidate_flags(fixture_path: Path | None = None) -> list[CandidateFlag]:
    path = fixture_path if fixture_path is not None else _default_flags_path()
    raw = json.loads(path.read_text())
    flags = raw.get("flags", [])
    result: list[CandidateFlag] = []
    for f in flags:
        result.append(
            CandidateFlag(
                flag_id=str(f["flag_id"]),
                candidate_id=str(f["candidate_id"]),
                track=str(f["track"]),
                flag_type=str(f["flag_type"]),
                severity=str(f["severity"]),
                raised_by=str(f["raised_by"]),
                raised_utc=str(f["raised_utc"]),
                status=str(f["status"]),
                resolution_notes=str(f.get("resolution_notes", "")),
                related_observation_id=str(f.get("related_observation_id", "")),
                tags=list(f.get("tags", [])),
            )
        )
    return result


def candidate_flags_summary(fixture_path: Path | None = None) -> dict[str, Any]:
    flags = load_candidate_flags(fixture_path)

    by_track: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    by_type: dict[str, int] = {}
    by_status: dict[str, int] = {}

    open_count = 0
    critical_count = 0

    for fl in flags:
        by_track[fl.track] = by_track.get(fl.track, 0) + 1
        by_severity[fl.severity] = by_severity.get(fl.severity, 0) + 1
        by_type[fl.flag_type] = by_type.get(fl.flag_type, 0) + 1
        by_status[fl.status] = by_status.get(fl.status, 0) + 1
        if fl.status == "open":
            open_count += 1
        if fl.severity == "critical":
            critical_count += 1

    return {
        "schema_version": CANDIDATE_FLAGS_SCHEMA_VERSION,
        "disclaimer": CANDIDATE_FLAGS_DISCLAIMER,
        "flag_count": len(flags),
        "unique_candidate_count": len({f.candidate_id for f in flags}),
        "open_count": open_count,
        "critical_count": critical_count,
        "by_track": dict(sorted(by_track.items())),
        "by_severity": dict(sorted(by_severity.items())),
        "by_type": dict(sorted(by_type.items())),
        "by_status": dict(sorted(by_status.items())),
        "tracks_covered": sorted(by_track.keys()),
    }
