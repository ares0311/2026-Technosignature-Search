"""Synthetic calibration metric fixture summaries."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from techno_search.schemas import Track

RELIABILITY_SCHEMA_VERSION = "synthetic_reliability_curves_v1"
RELIABILITY_DISCLAIMER = (
    "Synthetic reliability fixtures are development diagnostics only; they are not "
    "calibrated survey performance estimates."
)


@dataclass(frozen=True)
class ReliabilityBin:
    """One synthetic reliability curve bin."""

    bin_id: str
    track: Track
    score_min: float
    score_max: float
    predicted_probability: float
    observed_fraction: float
    sample_count: int

    @property
    def absolute_error(self) -> float:
        """Return the absolute calibration error for this synthetic bin."""

        return abs(self.predicted_probability - self.observed_fraction)


def default_reliability_fixture_path() -> Path:
    """Return the repository-local synthetic reliability fixture path."""

    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / (
        "reliability_curves.json"
    )


def load_reliability_bins(path: Path | str | None = None) -> tuple[ReliabilityBin, ...]:
    """Load and validate synthetic reliability curve bins."""

    fixture_path = default_reliability_fixture_path() if path is None else Path(path)
    with fixture_path.open(encoding="utf-8") as handle:
        fixture = json.load(handle)
    if not isinstance(fixture, dict):
        msg = f"Reliability fixture is not an object: {fixture_path}"
        raise ValueError(msg)
    if fixture.get("schema_version") != RELIABILITY_SCHEMA_VERSION:
        msg = f"Unsupported reliability fixture schema: {fixture_path}"
        raise ValueError(msg)
    bins = fixture.get("bins")
    if not isinstance(bins, list):
        msg = f"Reliability fixture missing bins: {fixture_path}"
        raise ValueError(msg)
    return tuple(_reliability_bin_from_mapping(item) for item in bins)


def reliability_summary(path: Path | str | None = None) -> dict[str, object]:
    """Summarize synthetic reliability curve fixture coverage."""

    fixture_path = default_reliability_fixture_path() if path is None else Path(path)
    bins = load_reliability_bins(fixture_path)
    total_samples = sum(item.sample_count for item in bins)
    weighted_error = sum(item.absolute_error * item.sample_count for item in bins)
    return {
        "fixture_path": str(fixture_path),
        "schema_version": RELIABILITY_SCHEMA_VERSION,
        "disclaimer": RELIABILITY_DISCLAIMER,
        "bin_count": len(bins),
        "total_sample_count": total_samples,
        "by_track": _counter_to_dict(Counter(item.track.value for item in bins)),
        "score_bins": sorted({f"{item.score_min:.1f}-{item.score_max:.1f}" for item in bins}),
        "mean_absolute_calibration_error": _safe_ratio(weighted_error, total_samples),
        "max_absolute_calibration_error": round(
            max((item.absolute_error for item in bins), default=0.0),
            6,
        ),
        "bin_ids": sorted(item.bin_id for item in bins),
    }


def _reliability_bin_from_mapping(data: object) -> ReliabilityBin:
    if not isinstance(data, dict):
        msg = "Reliability bin must be an object"
        raise ValueError(msg)
    return ReliabilityBin(
        bin_id=str(data["bin_id"]),
        track=Track(str(data["track"])),
        score_min=float(data["score_min"]),
        score_max=float(data["score_max"]),
        predicted_probability=float(data["predicted_probability"]),
        observed_fraction=float(data["observed_fraction"]),
        sample_count=int(data["sample_count"]),
    )


def _safe_ratio(numerator: float, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 6)


def _counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items()))
