"""Feature normalization bounds for ML preprocessing."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FEATURE_NORMALIZATION_SCHEMA_VERSION = "feature_normalization_v1"
FEATURE_NORMALIZATION_DISCLAIMER = (
    "Normalization bounds are ML preprocessing metadata only. "
    "They are not technosignature detections, discoveries, or external validation."
)


def _default_normalization_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests" / "fixtures" / "feature_normalization.json"
    )


@dataclass
class FeatureNormalizationBounds:
    bounds_id: str
    track: str
    extractor_version: str
    feature_names: list[str]
    min_values: list[float]
    max_values: list[float]
    mean_values: list[float]
    std_values: list[float]
    normalization_kind: str
    computed_utc: str
    sample_count: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "bounds_id": self.bounds_id,
            "track": self.track,
            "extractor_version": self.extractor_version,
            "feature_names": self.feature_names,
            "min_values": self.min_values,
            "max_values": self.max_values,
            "mean_values": self.mean_values,
            "std_values": self.std_values,
            "normalization_kind": self.normalization_kind,
            "computed_utc": self.computed_utc,
            "sample_count": self.sample_count,
        }


def load_normalization_bounds(
    fixture_path: Path | None = None,
) -> list[FeatureNormalizationBounds]:
    path = fixture_path or _default_normalization_path()
    with Path(path).open(encoding="utf-8") as fh:
        data = json.load(fh)
    entries = data.get("feature_normalization_bounds", [])
    return [
        FeatureNormalizationBounds(
            bounds_id=e["bounds_id"],
            track=e["track"],
            extractor_version=e["extractor_version"],
            feature_names=e["feature_names"],
            min_values=[float(v) for v in e["min_values"]],
            max_values=[float(v) for v in e["max_values"]],
            mean_values=[float(v) for v in e["mean_values"]],
            std_values=[float(v) for v in e["std_values"]],
            normalization_kind=e["normalization_kind"],
            computed_utc=e["computed_utc"],
            sample_count=int(e["sample_count"]),
        )
        for e in entries
    ]


def feature_normalization_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    bounds = load_normalization_bounds(fixture_path)
    by_track: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    extractor_versions: set[str] = set()
    track_versions: dict[str, set[str]] = {}

    for b in bounds:
        by_track[b.track] = by_track.get(b.track, 0) + 1
        by_kind[b.normalization_kind] = by_kind.get(b.normalization_kind, 0) + 1
        extractor_versions.add(b.extractor_version)
        track_versions.setdefault(b.track, set()).add(b.extractor_version)

    drift_detected = any(len(v) > 1 for v in track_versions.values())

    return {
        "schema_version": FEATURE_NORMALIZATION_SCHEMA_VERSION,
        "disclaimer": FEATURE_NORMALIZATION_DISCLAIMER,
        "bounds_count": len(bounds),
        "by_track": by_track,
        "by_normalization_kind": by_kind,
        "tracks_covered": sorted(by_track),
        "unique_extractor_versions": sorted(extractor_versions),
        "drift_detected": drift_detected,
    }
