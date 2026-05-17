"""Data quality log — per-observation data quality assessments."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DATA_QUALITY_LOG_SCHEMA_VERSION = "data_quality_log_v1"

DATA_QUALITY_LOG_DISCLAIMER = (
    "Data quality log entries are local scheduling and provenance records only. "
    "Quality grades reflect observational conditions at the time of acquisition, "
    "not candidate scientific merit. Poor data quality does not rule out a real "
    "signal; excellent quality does not confirm one. These records are scheduling "
    "aids for re-observation planning only."
)

ALLOWED_QUALITY_GRADES = frozenset({"excellent", "good", "marginal", "poor", "unusable"})

ALLOWED_QUALITY_ISSUE_TYPES = frozenset(
    {"rfi", "weather", "equipment", "calibration_failure", "data_loss", "none"}
)


def _default_quality_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "data_quality_log.json"
    )


@dataclass
class DataQualityEntry:
    entry_id: str
    observation_id: str
    track: str
    quality_grade: str
    issue_types: list[str]
    rfi_level: str
    weather_flag: bool
    equipment_flag: bool
    operator_id: str
    assessed_utc: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "observation_id": self.observation_id,
            "track": self.track,
            "quality_grade": self.quality_grade,
            "issue_types": self.issue_types,
            "rfi_level": self.rfi_level,
            "weather_flag": self.weather_flag,
            "equipment_flag": self.equipment_flag,
            "operator_id": self.operator_id,
            "assessed_utc": self.assessed_utc,
        }


def load_data_quality_entries(
    fixture_path: Path | None = None,
) -> list[DataQualityEntry]:
    path = fixture_path if fixture_path is not None else _default_quality_path()
    raw = json.loads(path.read_text())
    entries = raw.get("entries", [])
    result: list[DataQualityEntry] = []
    for e in entries:
        result.append(
            DataQualityEntry(
                entry_id=str(e["entry_id"]),
                observation_id=str(e["observation_id"]),
                track=str(e["track"]),
                quality_grade=str(e["quality_grade"]),
                issue_types=list(e.get("issue_types", [])),
                rfi_level=str(e.get("rfi_level", "none")),
                weather_flag=bool(e.get("weather_flag", False)),
                equipment_flag=bool(e.get("equipment_flag", False)),
                operator_id=str(e["operator_id"]),
                assessed_utc=str(e["assessed_utc"]),
            )
        )
    return result


def data_quality_log_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    entries = load_data_quality_entries(fixture_path)

    by_track: dict[str, int] = {}
    by_grade: dict[str, int] = {}
    poor_count = 0
    weather_affected_count = 0
    equipment_affected_count = 0
    rfi_affected_count = 0

    for e in entries:
        by_track[e.track] = by_track.get(e.track, 0) + 1
        by_grade[e.quality_grade] = by_grade.get(e.quality_grade, 0) + 1
        if e.quality_grade in ("poor", "unusable"):
            poor_count += 1
        if e.weather_flag:
            weather_affected_count += 1
        if e.equipment_flag:
            equipment_affected_count += 1
        if "rfi" in e.issue_types:
            rfi_affected_count += 1

    usable_count = sum(
        1 for e in entries if e.quality_grade not in ("poor", "unusable")
    )

    return {
        "schema_version": DATA_QUALITY_LOG_SCHEMA_VERSION,
        "disclaimer": DATA_QUALITY_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "usable_count": usable_count,
        "poor_count": poor_count,
        "weather_affected_count": weather_affected_count,
        "equipment_affected_count": equipment_affected_count,
        "rfi_affected_count": rfi_affected_count,
        "by_track": dict(sorted(by_track.items())),
        "by_grade": dict(sorted(by_grade.items())),
        "tracks_covered": sorted(by_track.keys()),
    }
