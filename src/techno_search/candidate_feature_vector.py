"""Candidate feature vector extraction for ML preprocessing."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CANDIDATE_FEATURE_VECTOR_SCHEMA_VERSION = "candidate_feature_vector_v1"
CANDIDATE_FEATURE_VECTOR_DISCLAIMER = (
    "Feature vectors are ML preprocessing artifacts for scheduling and model development "
    "only. They are not technosignature detections, discoveries, or external validation."
)
ALLOWED_NORMALIZATION_KINDS = frozenset({"none", "min_max", "z_score"})


def _default_feature_vector_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests" / "fixtures" / "candidate_feature_vectors.json"
    )


@dataclass
class CandidateFeatureVector:
    vector_id: str
    candidate_id: str
    track: str
    extractor_version: str
    feature_names: list[str]
    feature_values: list[float]
    normalization_kind: str
    extraction_utc: str
    is_normalized: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "vector_id": self.vector_id,
            "candidate_id": self.candidate_id,
            "track": self.track,
            "extractor_version": self.extractor_version,
            "feature_names": self.feature_names,
            "feature_values": self.feature_values,
            "normalization_kind": self.normalization_kind,
            "extraction_utc": self.extraction_utc,
            "is_normalized": self.is_normalized,
        }


def load_feature_vectors(
    fixture_path: Path | None = None,
) -> list[CandidateFeatureVector]:
    path = fixture_path or _default_feature_vector_path()
    with Path(path).open(encoding="utf-8") as fh:
        data = json.load(fh)
    entries = data.get("candidate_feature_vectors", [])
    return [
        CandidateFeatureVector(
            vector_id=e["vector_id"],
            candidate_id=e["candidate_id"],
            track=e["track"],
            extractor_version=e["extractor_version"],
            feature_names=e["feature_names"],
            feature_values=[float(v) for v in e["feature_values"]],
            normalization_kind=e["normalization_kind"],
            extraction_utc=e["extraction_utc"],
            is_normalized=bool(e["is_normalized"]),
        )
        for e in entries
    ]


def feature_vector_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    vectors = load_feature_vectors(fixture_path)
    by_track: dict[str, int] = {}
    by_normalization: dict[str, int] = {}
    extractor_versions: set[str] = set()
    feature_counts: list[int] = []

    for v in vectors:
        by_track[v.track] = by_track.get(v.track, 0) + 1
        by_normalization[v.normalization_kind] = (
            by_normalization.get(v.normalization_kind, 0) + 1
        )
        extractor_versions.add(v.extractor_version)
        feature_counts.append(len(v.feature_names))

    avg_feature_count = (
        round(sum(feature_counts) / len(feature_counts), 2) if feature_counts else 0.0
    )

    return {
        "schema_version": CANDIDATE_FEATURE_VECTOR_SCHEMA_VERSION,
        "disclaimer": CANDIDATE_FEATURE_VECTOR_DISCLAIMER,
        "vector_count": len(vectors),
        "by_track": by_track,
        "by_normalization_kind": by_normalization,
        "tracks_covered": sorted(by_track),
        "unique_extractor_versions": sorted(extractor_versions),
        "avg_feature_count": avg_feature_count,
    }
