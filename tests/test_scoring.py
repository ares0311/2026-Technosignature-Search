from techno_search import Candidate, Pathway, Track, score_candidate
from techno_search.pathway import PathwayThresholds
from techno_search.schemas import PosteriorClass


def test_clean_radio_candidate_scores_above_obvious_rfi() -> None:
    clean = Candidate(
        candidate_id="radio-clean",
        track=Track.RADIO,
        source_ids=("synthetic-on-001",),
        features={
            "snr": 42.0,
            "bandwidth_hz": 1.8,
            "drift_rate_hz_per_sec": 2.4,
            "on_target_presence_score": 0.95,
            "off_target_presence_score": 0.02,
            "rfi_band_overlap_score": 0.02,
            "frequency_persistence_score": 0.05,
            "nearby_target_recurrence_score": 0.03,
            "instrumental_artifact_score": 0.02,
            "injection_recovery_score": 0.88,
            "metadata_completeness_score": 0.95,
            "data_quality_score": 0.92,
            "provenance_completeness_score": 0.9,
        },
    )
    rfi = Candidate(
        candidate_id="radio-rfi",
        track=Track.RADIO,
        source_ids=("synthetic-off-001",),
        features={
            "snr": 45.0,
            "bandwidth_hz": 1.4,
            "drift_rate_hz_per_sec": 0.0,
            "on_target_presence_score": 0.85,
            "off_target_presence_score": 0.92,
            "rfi_band_overlap_score": 0.95,
            "frequency_persistence_score": 0.9,
            "nearby_target_recurrence_score": 0.85,
            "instrumental_artifact_score": 0.15,
            "injection_recovery_score": 0.3,
            "metadata_completeness_score": 0.9,
            "data_quality_score": 0.9,
            "provenance_completeness_score": 0.9,
        },
    )

    clean_score = score_candidate(clean)
    rfi_score = score_candidate(rfi)

    assert (
        clean_score.posterior[PosteriorClass.TECHNOSIGNATURE_INTEREST]
        > rfi_score.posterior[PosteriorClass.TECHNOSIGNATURE_INTEREST]
    )
    assert rfi_score.posterior[PosteriorClass.HUMAN_INTERFERENCE] > 0.5
    assert rfi_score.recommended_pathway == Pathway.DO_NOT_SUBMIT_FALSE_POSITIVE
    assert clean_score.evidence.negative_evidence


def test_off_target_presence_blocks_high_snr_radio_promotion() -> None:
    candidate = Candidate(
        candidate_id="radio-real-cadence-rfi",
        track=Track.RADIO,
        features={
            "snr": 148.0,
            "bandwidth_hz": 2.79,
            "drift_rate_hz_per_sec": 5.2,
            "on_target_presence_score": 1.0,
            "off_target_presence_score": 1.0,
            "rfi_band_overlap_score": 0.0,
            "frequency_persistence_score": 0.02,
            "nearby_target_recurrence_score": 0.0,
            "instrumental_artifact_score": 0.0,
            "injection_recovery_score": 0.5,
            "repeat_observation_score": 0.0,
            "metadata_completeness_score": 1.0,
            "data_quality_score": 1.0,
            "provenance_completeness_score": 1.0,
        },
    )

    scored = score_candidate(candidate)

    assert (
        scored.posterior[PosteriorClass.HUMAN_INTERFERENCE]
        > scored.posterior[PosteriorClass.TECHNOSIGNATURE_INTEREST]
    )
    assert scored.scores.false_positive_probability >= 0.8
    assert scored.recommended_pathway == Pathway.DO_NOT_SUBMIT_FALSE_POSITIVE
    assert any("OFF-target presence" in issue for issue in scored.evidence.blocking_issues)


def test_clean_infrared_excess_scores_above_blended_agn_like_source() -> None:
    clean = Candidate(
        candidate_id="ir-clean",
        track=Track.INFRARED,
        features={
            "ir_excess_score": 0.9,
            "sed_fit_residual_score": 0.82,
            "stellar_solution_quality": 0.94,
            "galaxy_agn_indicator_score": 0.05,
            "dust_indicator_score": 0.08,
            "confusion_score": 0.04,
            "photometric_quality_score": 0.92,
            "catalog_artifact_score": 0.02,
            "data_quality_score": 0.9,
            "provenance_completeness_score": 0.86,
        },
    )
    blended_agn = Candidate(
        candidate_id="ir-agn-blend",
        track=Track.INFRARED,
        features={
            "ir_excess_score": 0.88,
            "sed_fit_residual_score": 0.75,
            "stellar_solution_quality": 0.25,
            "galaxy_agn_indicator_score": 0.9,
            "dust_indicator_score": 0.55,
            "confusion_score": 0.86,
            "photometric_quality_score": 0.35,
            "catalog_artifact_score": 0.55,
            "data_quality_score": 0.4,
            "provenance_completeness_score": 0.7,
        },
    )

    clean_score = score_candidate(clean)
    blend_score = score_candidate(blended_agn)

    assert (
        clean_score.posterior[PosteriorClass.TECHNOSIGNATURE_INTEREST]
        > blend_score.posterior[PosteriorClass.TECHNOSIGNATURE_INTEREST]
    )
    assert (
        blend_score.scores.false_positive_probability
        > clean_score.scores.false_positive_probability
    )
    assert "Galaxy or AGN indicators are present." in blend_score.evidence.negative_evidence


def test_clean_archival_anomaly_scores_above_known_artifact() -> None:
    clean = Candidate(
        candidate_id="anomaly-clean",
        track=Track.ANOMALY,
        features={
            "historical_detection_score": 0.9,
            "modern_non_detection_score": 0.86,
            "magnitude_change": 4.8,
            "proper_motion_explanation_score": 0.05,
            "survey_depth_explanation_score": 0.04,
            "artifact_score": 0.03,
            "moving_object_score": 0.06,
            "variability_score": 0.12,
            "catalog_mismatch_score": 0.08,
            "crossmatch_confidence": 0.88,
            "data_quality_score": 0.88,
            "provenance_completeness_score": 0.84,
        },
    )
    artifact = Candidate(
        candidate_id="anomaly-artifact",
        track=Track.ANOMALY,
        features={
            "historical_detection_score": 0.55,
            "modern_non_detection_score": 0.7,
            "magnitude_change": 4.0,
            "proper_motion_explanation_score": 0.7,
            "survey_depth_explanation_score": 0.65,
            "artifact_score": 0.92,
            "moving_object_score": 0.2,
            "variability_score": 0.55,
            "catalog_mismatch_score": 0.75,
            "crossmatch_confidence": 0.35,
            "data_quality_score": 0.45,
            "provenance_completeness_score": 0.55,
        },
    )

    clean_score = score_candidate(clean)
    artifact_score = score_candidate(artifact)

    assert (
        clean_score.posterior[PosteriorClass.TECHNOSIGNATURE_INTEREST]
        > artifact_score.posterior[PosteriorClass.TECHNOSIGNATURE_INTEREST]
    )
    assert artifact_score.posterior[PosteriorClass.CATALOG_OR_PROCESSING_ERROR] > 0.35
    assert artifact_score.recommended_pathway == Pathway.DO_NOT_SUBMIT_FALSE_POSITIVE
    assert artifact_score.evidence.blocking_issues


def test_known_object_routes_to_annotation() -> None:
    candidate = Candidate(
        candidate_id="known-object",
        track=Track.INFRARED,
        features={
            "known_object_score": 1.0,
            "ir_excess_score": 0.8,
            "sed_fit_residual_score": 0.7,
            "stellar_solution_quality": 0.8,
            "photometric_quality_score": 0.8,
            "galaxy_agn_indicator_score": 0.1,
            "dust_indicator_score": 0.1,
            "confusion_score": 0.1,
        },
    )

    scored = score_candidate(candidate)

    assert scored.recommended_pathway == Pathway.KNOWN_OBJECT_ANNOTATION


def test_known_object_feature_takes_precedence_for_high_snr_radio() -> None:
    candidate = Candidate(
        candidate_id="Voyager1.single_coarse.fine_res",
        track=Track.RADIO,
        features={
            "snr": 245.0,
            "bandwidth_hz": 2.79,
            "drift_rate_hz_per_sec": -0.38,
            "on_target_presence_score": 1.0,
            "off_target_presence_score": 0.0,
            "rfi_band_overlap_score": 0.0,
            "frequency_persistence_score": 0.0,
            "nearby_target_recurrence_score": 0.0,
            "instrumental_artifact_score": 0.0,
            "injection_recovery_score": 0.5,
            "repeat_observation_score": 0.0,
            "metadata_completeness_score": 1.0,
            "data_quality_score": 1.0,
            "provenance_completeness_score": 1.0,
            "known_object_score": 1.0,
        },
    )

    scored = score_candidate(candidate)

    assert scored.recommended_pathway == Pathway.KNOWN_OBJECT_ANNOTATION


def test_score_candidate_uses_supplied_pathway_thresholds() -> None:
    candidate = Candidate(
        candidate_id="threshold-check",
        track=Track.INFRARED,
        features={
            "ir_excess_score": 0.82,
            "sed_fit_residual_score": 0.76,
            "stellar_solution_quality": 0.88,
            "galaxy_agn_indicator_score": 0.05,
            "dust_indicator_score": 0.07,
            "confusion_score": 0.05,
            "photometric_quality_score": 0.9,
            "catalog_artifact_score": 0.02,
            "data_quality_score": 0.9,
            "provenance_completeness_score": 0.88,
        },
    )

    scored = score_candidate(
        candidate,
        thresholds=PathwayThresholds(false_positive_probability=0.0),
    )

    assert scored.recommended_pathway == Pathway.DO_NOT_SUBMIT_FALSE_POSITIVE
