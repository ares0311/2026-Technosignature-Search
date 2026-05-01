"""Synthetic archival/catalog anomaly prototype."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from techno_search.config import TrackConfig, load_track_config
from techno_search.schemas import Candidate, FeatureValue, Track


@dataclass(frozen=True)
class ArchivalAnomaly:
    """Normalized synthetic historical-modern source comparison."""

    historical_source_id: str
    modern_source_id: str | None
    ra: float
    dec: float
    historical_epoch: float
    modern_epoch: float
    historical_magnitude: float
    modern_magnitude: float | None
    modern_limit_magnitude: float | None
    crossmatch_distance_arcsec: float
    crossmatch_confidence: float
    proper_motion_explanation_score: float
    survey_depth_explanation_score: float
    artifact_score: float
    moving_object_score: float
    variability_score: float
    catalog_mismatch_score: float


def build_anomaly_candidate(
    candidate_id: str,
    row: Mapping[str, FeatureValue],
    *,
    source_ids: Sequence[str] = (),
    provenance: Mapping[str, FeatureValue] | None = None,
    track_config: TrackConfig | None = None,
) -> Candidate:
    """Build a shared candidate from a synthetic archival anomaly row."""

    defaults = _feature_defaults(track_config)
    anomaly = _parse_anomaly(row, defaults)
    magnitude_change = _magnitude_change(anomaly)
    modern_non_detection = _modern_non_detection_score(anomaly)
    historical_detection = _score_or(
        row, "historical_detection_score", defaults["historical_detection_score"]
    )

    features: dict[str, FeatureValue] = {
        "historical_source_id": anomaly.historical_source_id,
        "modern_source_id": anomaly.modern_source_id,
        "ra": anomaly.ra,
        "dec": anomaly.dec,
        "historical_epoch": anomaly.historical_epoch,
        "modern_epoch": anomaly.modern_epoch,
        "historical_magnitude": anomaly.historical_magnitude,
        "modern_magnitude": anomaly.modern_magnitude,
        "modern_limit_magnitude": anomaly.modern_limit_magnitude,
        "crossmatch_distance_arcsec": anomaly.crossmatch_distance_arcsec,
        "crossmatch_confidence": anomaly.crossmatch_confidence,
        "historical_detection_score": historical_detection,
        "modern_non_detection_score": modern_non_detection,
        "magnitude_change": magnitude_change,
        "proper_motion_explanation_score": anomaly.proper_motion_explanation_score,
        "survey_depth_explanation_score": anomaly.survey_depth_explanation_score,
        "artifact_score": anomaly.artifact_score,
        "moving_object_score": anomaly.moving_object_score,
        "variability_score": anomaly.variability_score,
        "catalog_mismatch_score": anomaly.catalog_mismatch_score,
        "data_quality_score": _data_quality_score(anomaly, historical_detection),
        "provenance_completeness_score": (
            1.0 if provenance else defaults.get("provenance_completeness_score", 0.4)
        ),
    }

    default_sources = tuple(
        source_id
        for source_id in (anomaly.historical_source_id, anomaly.modern_source_id)
        if source_id
    )

    return Candidate(
        candidate_id=candidate_id,
        track=Track.ANOMALY,
        features=features,
        source_ids=tuple(source_ids or default_sources),
        provenance=provenance or {},
    )


def _parse_anomaly(
    row: Mapping[str, FeatureValue],
    defaults: Mapping[str, float],
) -> ArchivalAnomaly:
    return ArchivalAnomaly(
        historical_source_id=str(row.get("historical_source_id", "unknown")),
        modern_source_id=_optional_str(row.get("modern_source_id")),
        ra=_float(row.get("ra", 0.0)),
        dec=_float(row.get("dec", 0.0)),
        historical_epoch=_required_float(row, "historical_epoch"),
        modern_epoch=_required_float(row, "modern_epoch"),
        historical_magnitude=_required_float(row, "historical_magnitude"),
        modern_magnitude=_optional_float(row.get("modern_magnitude")),
        modern_limit_magnitude=_optional_float(row.get("modern_limit_magnitude")),
        crossmatch_distance_arcsec=_float(row.get("crossmatch_distance_arcsec", 0.0)),
        crossmatch_confidence=_score_or(
            row,
            "crossmatch_confidence",
            defaults["crossmatch_confidence"],
        ),
        proper_motion_explanation_score=_score_or(
            row,
            "proper_motion_explanation_score",
            defaults["proper_motion_explanation_score"],
        ),
        survey_depth_explanation_score=_score_or(
            row,
            "survey_depth_explanation_score",
            defaults["survey_depth_explanation_score"],
        ),
        artifact_score=_score_or(row, "artifact_score", defaults["artifact_score"]),
        moving_object_score=_score_or(
            row, "moving_object_score", defaults["moving_object_score"]
        ),
        variability_score=_score_or(row, "variability_score", defaults["variability_score"]),
        catalog_mismatch_score=_score_or(
            row, "catalog_mismatch_score", defaults["catalog_mismatch_score"]
        ),
    )


def _magnitude_change(anomaly: ArchivalAnomaly) -> float:
    if anomaly.modern_magnitude is not None:
        return max(0.0, anomaly.modern_magnitude - anomaly.historical_magnitude)
    if anomaly.modern_limit_magnitude is not None:
        return max(0.0, anomaly.modern_limit_magnitude - anomaly.historical_magnitude)
    return 0.0


def _modern_non_detection_score(anomaly: ArchivalAnomaly) -> float:
    if anomaly.modern_magnitude is None and anomaly.modern_limit_magnitude is not None:
        return _clamp(_magnitude_change(anomaly) / 5.0)
    if anomaly.modern_magnitude is None:
        return 0.5
    return 0.0


def _data_quality_score(anomaly: ArchivalAnomaly, historical_detection: float) -> float:
    contaminant_penalty = max(
        anomaly.artifact_score,
        anomaly.catalog_mismatch_score,
        anomaly.survey_depth_explanation_score,
    )
    return _clamp(
        0.45 * historical_detection
        + 0.35 * anomaly.crossmatch_confidence
        + 0.20 * (1.0 - contaminant_penalty)
    )


def _score_or(row: Mapping[str, FeatureValue], key: str, default: float) -> float:
    if key not in row:
        return _clamp(default)
    return _clamp(_float(row[key]))


def _required_float(row: Mapping[str, FeatureValue], key: str) -> float:
    if key not in row:
        msg = f"Missing required archival anomaly field: {key}"
        raise ValueError(msg)
    return _float(row[key])


def _optional_float(value: FeatureValue) -> float | None:
    if value is None:
        return None
    return _float(value)


def _optional_str(value: FeatureValue) -> str | None:
    if value is None:
        return None
    return str(value)


def _float(value: FeatureValue) -> float:
    if isinstance(value, bool) or value is None:
        msg = f"Expected numeric value, got {value!r}"
        raise TypeError(msg)
    if isinstance(value, int | float):
        return float(value)
    return float(value)


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))


def _feature_defaults(track_config: TrackConfig | None) -> dict[str, float]:
    config = track_config or load_track_config(Track.ANOMALY)
    defaults = dict(config.feature_defaults)
    defaults.setdefault("historical_detection_score", 0.8)
    defaults.setdefault("crossmatch_confidence", 0.5)
    defaults.setdefault("proper_motion_explanation_score", 0.0)
    defaults.setdefault("survey_depth_explanation_score", 0.0)
    defaults.setdefault("artifact_score", 0.0)
    defaults.setdefault("moving_object_score", 0.0)
    defaults.setdefault("variability_score", 0.0)
    defaults.setdefault("catalog_mismatch_score", 0.0)
    defaults.setdefault("provenance_completeness_score", 0.4)
    return defaults
