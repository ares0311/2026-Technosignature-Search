"""Calibration fixture helpers."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from techno_search.schemas import Candidate, Pathway, candidate_from_mapping


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


def _fixture_from_mapping(data: dict[str, Any]) -> CalibrationFixture:
    candidate = candidate_from_mapping(data["candidate"])
    false_positive_class = str(candidate.provenance.get("false_positive_class", "unknown"))
    return CalibrationFixture(
        name=str(data["name"]),
        expected_pathway=Pathway(str(data["expected_pathway"])),
        candidate=candidate,
        false_positive_class=false_positive_class,
    )


def _counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items()))
