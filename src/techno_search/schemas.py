"""Typed public schemas for synthetic candidate scoring."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Track(StrEnum):
    """Supported search tracks."""

    RADIO = "radio"
    INFRARED = "infrared"
    ANOMALY = "anomaly"
    TRANSIT_PHOTOMETRY = "transit_photometry"
    SPECTROSCOPY = "spectroscopy"


class Pathway(StrEnum):
    """Conservative candidate routing labels."""

    KNOWN_OBJECT_ANNOTATION = "known_object_annotation"
    DO_NOT_SUBMIT_FALSE_POSITIVE = "do_not_submit_false_positive"
    GITHUB_REPRODUCIBILITY_ONLY = "github_reproducibility_only"
    HUMAN_REVIEW_QUEUE = "human_review_queue"
    CANDIDATE_REVIEW_PACKET = "candidate_review_packet"
    EXTERNAL_FOLLOWUP_CANDIDATE = "external_followup_candidate"


class PosteriorClass(StrEnum):
    """Shared posterior-style hypothesis classes."""

    TECHNOSIGNATURE_INTEREST = "technosignature_interest"
    NATURAL_SOURCE = "natural_source"
    HUMAN_INTERFERENCE = "human_interference"
    INSTRUMENTAL_ARTIFACT = "instrumental_artifact"
    CATALOG_OR_PROCESSING_ERROR = "catalog_or_processing_error"
    KNOWN_OBJECT = "known_object"
    NOISE_OR_LOW_CONFIDENCE = "noise_or_low_confidence"


FeatureValue = bool | int | float | str | None
FeatureMap = Mapping[str, FeatureValue]
ProvenanceMap = Mapping[str, FeatureValue]


@dataclass(frozen=True)
class Candidate:
    """A normalized candidate feature packet.

    Features are intentionally flexible in v0 so each search track can mature without
    forcing an overfit schema. Numeric scores are interpreted as normalized 0..1 values
    unless a field name documents a physical unit, such as ``snr`` or ``bandwidth_hz``.
    """

    candidate_id: str
    track: Track
    features: FeatureMap
    source_ids: tuple[str, ...] = ()
    provenance: ProvenanceMap = field(default_factory=dict)


def candidate_from_mapping(data: Mapping[str, Any]) -> Candidate:
    """Convert a JSON-like mapping into a normalized candidate."""

    return Candidate(
        candidate_id=str(data["candidate_id"]),
        track=Track(str(data["track"])),
        features=_feature_mapping(data.get("features", {})),
        source_ids=tuple(str(item) for item in data.get("source_ids", ())),
        provenance=_feature_mapping(data.get("provenance", {})),
    )


@dataclass(frozen=True)
class EvidenceSummary:
    """Human-readable evidence lists for a candidate."""

    positive_evidence: tuple[str, ...] = ()
    negative_evidence: tuple[str, ...] = ()
    blocking_issues: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, list[str]]:
        return {
            "positive_evidence": list(self.positive_evidence),
            "negative_evidence": list(self.negative_evidence),
            "blocking_issues": list(self.blocking_issues),
        }


@dataclass(frozen=True)
class CandidateScores:
    """Derived scores used by pathway classification."""

    false_positive_probability: float
    signal_reality_confidence: float
    novelty_score: float
    followup_value: float
    review_readiness: float

    def as_dict(self) -> dict[str, float]:
        return {
            "false_positive_probability": self.false_positive_probability,
            "signal_reality_confidence": self.signal_reality_confidence,
            "novelty_score": self.novelty_score,
            "followup_value": self.followup_value,
            "review_readiness": self.review_readiness,
        }


@dataclass(frozen=True)
class ScoredCandidate:
    """Complete v0 scoring output."""

    candidate: Candidate
    posterior: dict[PosteriorClass, float]
    scores: CandidateScores
    recommended_pathway: Pathway
    evidence: EvidenceSummary
    calibration_status: str = "uncalibrated"
    calibration_dataset_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate.candidate_id,
            "track": self.candidate.track.value,
            "source_ids": list(self.candidate.source_ids),
            "features": dict(self.candidate.features),
            "posterior": {key.value: value for key, value in self.posterior.items()},
            "scores": self.scores.as_dict(),
            "score_calibration": {
                "schema_version": "score_calibration_v1",
                "status": self.calibration_status,
                "calibration_dataset_id": self.calibration_dataset_id,
                "probability_interpretation_allowed": self.calibration_status
                == "calibrated",
                "limitation": (
                    "Normalized heuristic routing weights are not calibrated "
                    "probabilities and must not be interpreted as false-positive, "
                    "signal-reality, or technosignature probabilities."
                    if self.calibration_status != "calibrated"
                    else ""
                ),
            },
            "recommended_pathway": self.recommended_pathway.value,
            **self.evidence.as_dict(),
            "provenance": dict(self.candidate.provenance),
        }


def _feature_mapping(data: Mapping[str, Any]) -> dict[str, FeatureValue]:
    return {str(key): _feature_value(value) for key, value in data.items()}


def _feature_value(value: Any) -> FeatureValue:
    if value is None or isinstance(value, bool | int | float | str):
        return value
    msg = f"Unsupported candidate JSON value: {value!r}"
    raise TypeError(msg)
