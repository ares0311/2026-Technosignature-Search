import pytest

from techno_search import score_candidate
from techno_search.anomalies import build_anomaly_candidate
from techno_search.config import TrackConfig
from techno_search.schemas import PosteriorClass, Track


def test_build_anomaly_candidate_normalizes_crossmatch_features() -> None:
    candidate = build_anomaly_candidate(
        "anomaly-prototype",
        {
            "historical_source_id": "plate-001",
            "modern_source_id": None,
            "ra": 10.0,
            "dec": -2.0,
            "historical_epoch": 1950.0,
            "modern_epoch": 2020.0,
            "historical_magnitude": 14.0,
            "modern_limit_magnitude": 20.0,
            "crossmatch_distance_arcsec": 0.4,
            "crossmatch_confidence": 0.86,
            "proper_motion_explanation_score": 0.05,
            "survey_depth_explanation_score": 0.05,
            "artifact_score": 0.04,
        },
        provenance={"source_dataset": "synthetic-anomaly"},
    )

    assert candidate.track == Track.ANOMALY
    assert candidate.features["magnitude_change"] == 6.0
    assert candidate.features["modern_non_detection_score"] == 1.0
    assert candidate.features["crossmatch_confidence"] == 0.86
    assert candidate.provenance["source_dataset"] == "synthetic-anomaly"


def test_anomaly_candidate_uses_track_config_feature_defaults() -> None:
    track_config = TrackConfig(
        track=Track.ANOMALY,
        config_version="test_anomaly",
        thresholds={},
        feature_defaults={
            "historical_detection_score": 0.66,
            "crossmatch_confidence": 0.77,
            "proper_motion_explanation_score": 0.11,
            "survey_depth_explanation_score": 0.12,
            "artifact_score": 0.13,
            "moving_object_score": 0.14,
            "variability_score": 0.15,
            "catalog_mismatch_score": 0.16,
            "provenance_completeness_score": 0.76,
        },
        assumptions=(),
        raw={},
    )

    candidate = build_anomaly_candidate(
        "anomaly-config-defaults",
        {
            "historical_source_id": "plate-config",
            "historical_epoch": 1950.0,
            "modern_epoch": 2020.0,
            "historical_magnitude": 14.0,
            "modern_limit_magnitude": 20.0,
        },
        track_config=track_config,
    )

    assert candidate.features["historical_detection_score"] == 0.66
    assert candidate.features["crossmatch_confidence"] == 0.77
    assert candidate.features["proper_motion_explanation_score"] == 0.11
    assert candidate.features["survey_depth_explanation_score"] == 0.12
    assert candidate.features["artifact_score"] == 0.13
    assert candidate.features["moving_object_score"] == 0.14
    assert candidate.features["variability_score"] == 0.15
    assert candidate.features["catalog_mismatch_score"] == 0.16
    assert candidate.features["provenance_completeness_score"] == 0.76


def test_clean_anomaly_candidate_scores_above_artifact_false_positive() -> None:
    clean = build_anomaly_candidate(
        "anomaly-clean-prototype",
        {
            "historical_source_id": "plate-clean",
            "historical_epoch": 1950.0,
            "modern_epoch": 2020.0,
            "historical_magnitude": 14.0,
            "modern_limit_magnitude": 20.0,
            "crossmatch_confidence": 0.9,
            "proper_motion_explanation_score": 0.03,
            "survey_depth_explanation_score": 0.03,
            "artifact_score": 0.02,
            "moving_object_score": 0.02,
            "variability_score": 0.1,
            "catalog_mismatch_score": 0.05,
        },
        provenance={"source_dataset": "synthetic-anomaly"},
    )
    artifact = build_anomaly_candidate(
        "anomaly-artifact-prototype",
        {
            "historical_source_id": "plate-artifact",
            "modern_source_id": "modern-counterpart",
            "historical_epoch": 1950.0,
            "modern_epoch": 2020.0,
            "historical_magnitude": 14.0,
            "modern_magnitude": 18.0,
            "crossmatch_confidence": 0.35,
            "proper_motion_explanation_score": 0.65,
            "survey_depth_explanation_score": 0.75,
            "artifact_score": 0.92,
            "moving_object_score": 0.45,
            "variability_score": 0.65,
            "catalog_mismatch_score": 0.8,
        },
        provenance={"source_dataset": "synthetic-anomaly"},
    )

    clean_score = score_candidate(clean)
    artifact_score = score_candidate(artifact)

    assert (
        clean_score.posterior[PosteriorClass.TECHNOSIGNATURE_INTEREST]
        > artifact_score.posterior[PosteriorClass.TECHNOSIGNATURE_INTEREST]
    )
    assert artifact_score.posterior[PosteriorClass.CATALOG_OR_PROCESSING_ERROR] > 0.35
    assert "Plate, image, or processing artifact evidence is present." in (
        artifact_score.evidence.negative_evidence
    )


def test_anomaly_candidate_requires_epochs() -> None:
    with pytest.raises(ValueError, match="historical_epoch"):
        build_anomaly_candidate(
            "missing-epoch",
            {
                "modern_epoch": 2020.0,
                "historical_magnitude": 14.0,
            },
        )
