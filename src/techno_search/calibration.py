"""Calibration fixture helpers."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from techno_search.schemas import Candidate, Pathway, candidate_from_mapping

FALSE_POSITIVE_ANALYSIS_SCHEMA_VERSION = "synthetic_false_positive_analysis_v1"
FALSE_POSITIVE_ANALYSIS_DISCLAIMER = (
    "Synthetic false-positive class analysis is a development diagnostic only; "
    "it is not calibrated survey contamination analysis."
)
CALIBRATION_TRACK_SCHEMA_VERSION = "synthetic_calibration_by_track_v1"
CALIBRATION_TRACK_DISCLAIMER = (
    "Synthetic calibration-by-track summaries are development diagnostics only; "
    "they are not calibrated per-track survey performance estimates."
)


@dataclass(frozen=True)
class CalibrationFixture:
    """A synthetic calibration fixture with an expected conservative pathway."""

    name: str
    expected_pathway: Pathway
    candidate: Candidate
    false_positive_class: str


@dataclass(frozen=True)
class CalibrationSummary:
    """Counts for calibration fixture coverage."""

    total: int
    by_track: dict[str, int]
    by_false_positive_class: dict[str, int]
    by_expected_pathway: dict[str, int]

    def as_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "by_track": self.by_track,
            "by_false_positive_class": self.by_false_positive_class,
            "by_expected_pathway": self.by_expected_pathway,
        }


def default_calibration_fixture_path() -> Path:
    """Return the repository-local false-positive calibration fixture path."""

    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / (
        "calibration_false_positives.json"
    )


def load_calibration_fixtures(path: Path | None = None) -> tuple[CalibrationFixture, ...]:
    """Load synthetic false-positive calibration fixtures."""

    fixture_path = path or default_calibration_fixture_path()
    with fixture_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    return tuple(_fixture_from_mapping(item) for item in data["fixtures"])


def summarize_calibration_fixtures(
    fixtures: tuple[CalibrationFixture, ...],
) -> CalibrationSummary:
    """Summarize fixture counts by track, false-positive class, and expected pathway."""

    return CalibrationSummary(
        total=len(fixtures),
        by_track=_counter_to_dict(Counter(fixture.candidate.track.value for fixture in fixtures)),
        by_false_positive_class=_counter_to_dict(
            Counter(fixture.false_positive_class for fixture in fixtures)
        ),
        by_expected_pathway=_counter_to_dict(
            Counter(fixture.expected_pathway.value for fixture in fixtures)
        ),
    )


def false_positive_class_summary(path: Path | None = None) -> dict[str, object]:
    """Summarize synthetic false-positive fixture coverage by class and track."""

    fixture_path = path or default_calibration_fixture_path()
    fixtures = load_calibration_fixtures(fixture_path)
    by_track_and_class: dict[str, Counter[str]] = defaultdict(Counter)
    fixture_names_by_class: dict[str, list[str]] = defaultdict(list)
    candidate_ids_by_class: dict[str, list[str]] = defaultdict(list)

    for fixture in fixtures:
        track = fixture.candidate.track.value
        false_positive_class = fixture.false_positive_class
        by_track_and_class[track][false_positive_class] += 1
        fixture_names_by_class[false_positive_class].append(fixture.name)
        candidate_ids_by_class[false_positive_class].append(fixture.candidate.candidate_id)

    summary = summarize_calibration_fixtures(fixtures)
    return {
        "fixture_path": str(fixture_path),
        "schema_version": FALSE_POSITIVE_ANALYSIS_SCHEMA_VERSION,
        "disclaimer": FALSE_POSITIVE_ANALYSIS_DISCLAIMER,
        "case_count": summary.total,
        "class_count": len(summary.by_false_positive_class),
        "track_count": len(summary.by_track),
        "by_track": summary.by_track,
        "by_class": summary.by_false_positive_class,
        "by_expected_pathway": summary.by_expected_pathway,
        "by_track_and_class": {
            track: _counter_to_dict(counter)
            for track, counter in sorted(by_track_and_class.items())
        },
        "fixture_names_by_class": {
            key: sorted(value) for key, value in sorted(fixture_names_by_class.items())
        },
        "candidate_ids_by_class": {
            key: sorted(value) for key, value in sorted(candidate_ids_by_class.items())
        },
    }


def calibration_track_summary(path: Path | None = None) -> dict[str, object]:
    """Summarize synthetic calibration fixture coverage within each search track."""

    fixture_path = path or default_calibration_fixture_path()
    fixtures = load_calibration_fixtures(fixture_path)
    by_track: dict[str, list[CalibrationFixture]] = defaultdict(list)
    for fixture in fixtures:
        by_track[fixture.candidate.track.value].append(fixture)

    track_summaries = {
        track: _calibration_track_detail(track_fixtures)
        for track, track_fixtures in sorted(by_track.items())
    }
    case_counts = [
        detail["case_count"]
        for detail in track_summaries.values()
        if isinstance(detail["case_count"], int)
    ]
    summary = summarize_calibration_fixtures(fixtures)
    return {
        "fixture_path": str(fixture_path),
        "schema_version": CALIBRATION_TRACK_SCHEMA_VERSION,
        "disclaimer": CALIBRATION_TRACK_DISCLAIMER,
        "case_count": summary.total,
        "track_count": len(track_summaries),
        "minimum_track_case_count": min(case_counts) if case_counts else 0,
        "by_track": track_summaries,
    }


def _fixture_from_mapping(data: dict[str, Any]) -> CalibrationFixture:
    candidate = candidate_from_mapping(data["candidate"])
    false_positive_class = str(candidate.provenance.get("false_positive_class", "unknown"))
    return CalibrationFixture(
        name=str(data["name"]),
        expected_pathway=Pathway(str(data["expected_pathway"])),
        candidate=candidate,
        false_positive_class=false_positive_class,
    )


def _calibration_track_detail(fixtures: list[CalibrationFixture]) -> dict[str, object]:
    return {
        "case_count": len(fixtures),
        "class_count": len({fixture.false_positive_class for fixture in fixtures}),
        "by_false_positive_class": _counter_to_dict(
            Counter(fixture.false_positive_class for fixture in fixtures)
        ),
        "by_expected_pathway": _counter_to_dict(
            Counter(fixture.expected_pathway.value for fixture in fixtures)
        ),
        "candidate_ids": sorted(fixture.candidate.candidate_id for fixture in fixtures),
        "fixture_names": sorted(fixture.name for fixture in fixtures),
    }


def _counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items()))
