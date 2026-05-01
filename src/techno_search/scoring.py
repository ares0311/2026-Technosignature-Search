"""Interpretable v0 scoring for synthetic candidates."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from typing import Final

from techno_search.pathway import classify_pathway
from techno_search.schemas import (
    Candidate,
    CandidateScores,
    EvidenceSummary,
    PosteriorClass,
    ScoredCandidate,
    Track,
)

_LOG_PRIORS: Final[dict[PosteriorClass, float]] = {
    PosteriorClass.TECHNOSIGNATURE_INTEREST: -2.30,
    PosteriorClass.NATURAL_SOURCE: -0.65,
    PosteriorClass.HUMAN_INTERFERENCE: -0.65,
    PosteriorClass.INSTRUMENTAL_ARTIFACT: -0.65,
    PosteriorClass.CATALOG_OR_PROCESSING_ERROR: -0.65,
    PosteriorClass.KNOWN_OBJECT: -1.20,
    PosteriorClass.NOISE_OR_LOW_CONFIDENCE: -0.80,
}

DictLike = Mapping[str, object]


def score_candidate(candidate: Candidate) -> ScoredCandidate:
    """Score a synthetic candidate and assign a conservative pathway."""

    raw_scores, evidence = _track_scores(candidate)
    posterior = _softmax(
        {
            posterior_class: _LOG_PRIORS[posterior_class] + raw_scores[posterior_class]
            for posterior_class in PosteriorClass
        }
    )
    scores = _derived_scores(candidate, posterior)
    pathway = classify_pathway(posterior, scores)

    return ScoredCandidate(
        candidate=candidate,
        posterior=posterior,
        scores=scores,
        recommended_pathway=pathway,
        evidence=evidence,
    )


def score_candidates(candidates: Iterable[Candidate]) -> list[ScoredCandidate]:
    """Score candidates in input order."""

    return [score_candidate(candidate) for candidate in candidates]


def _track_scores(candidate: Candidate) -> tuple[dict[PosteriorClass, float], EvidenceSummary]:
    if candidate.track == Track.RADIO:
        return _radio_scores(candidate)
    if candidate.track == Track.INFRARED:
        return _infrared_scores(candidate)
    if candidate.track == Track.ANOMALY:
        return _anomaly_scores(candidate)
    msg = f"Unsupported track: {candidate.track}"
    raise ValueError(msg)


def _radio_scores(candidate: Candidate) -> tuple[dict[PosteriorClass, float], EvidenceSummary]:
    f = candidate.features
    snr = _scaled_positive_float(f, "snr", divisor=50.0)
    bandwidth = _narrowband_score(_float(f, "bandwidth_hz", default=10.0))
    drift = _drift_score(_float(f, "drift_rate_hz_per_sec", default=0.0))
    zero_drift = 1.0 - drift
    on_target = _score(f, "on_target_presence_score")
    off_target = _score(f, "off_target_presence_score")
    absent_off = 1.0 - off_target
    rfi = _score(f, "rfi_band_overlap_score")
    persistence = _score(f, "frequency_persistence_score")
    recurrence = _score(f, "nearby_target_recurrence_score")
    artifact = _score(f, "instrumental_artifact_score")
    injection = _score(f, "injection_recovery_score", default=0.5)
    repeat = _score(f, "repeat_observation_score")
    known = _score(f, "known_object_score")
    metadata = _score(f, "metadata_completeness_score", default=0.5)

    raw_scores = _empty_scores()
    raw_scores[PosteriorClass.TECHNOSIGNATURE_INTEREST] += (
        1.15 * snr
        + 1.35 * bandwidth
        + 1.10 * drift
        + 1.45 * on_target
        + 1.35 * absent_off
        + 1.00 * (1.0 - rfi)
        + 0.85 * (1.0 - persistence)
        + 0.90 * injection
        + 0.55 * repeat
        + 0.50 * metadata
    )
    raw_scores[PosteriorClass.HUMAN_INTERFERENCE] += (
        1.70 * off_target
        + 1.60 * rfi
        + 1.15 * persistence
        + 1.00 * recurrence
        + 0.80 * zero_drift
    )
    raw_scores[PosteriorClass.INSTRUMENTAL_ARTIFACT] += (
        1.60 * artifact + 0.65 * _score(f, "band_edge_score") + 0.75 * (1.0 - metadata)
    )
    raw_scores[PosteriorClass.NOISE_OR_LOW_CONFIDENCE] += (
        1.25 * (1.0 - snr) + 0.90 * (1.0 - metadata) + 0.60 * (1.0 - on_target)
    )
    raw_scores[PosteriorClass.KNOWN_OBJECT] += 8.00 * known
    raw_scores[PosteriorClass.NATURAL_SOURCE] += 0.20
    raw_scores[PosteriorClass.CATALOG_OR_PROCESSING_ERROR] += 0.20 * (1.0 - metadata)

    evidence = _radio_evidence(
        snr=snr,
        bandwidth=bandwidth,
        drift=drift,
        on_target=on_target,
        off_target=off_target,
        rfi=rfi,
        persistence=persistence,
        artifact=artifact,
        injection=injection,
        repeat=repeat,
        metadata=metadata,
    )
    return raw_scores, evidence


def _infrared_scores(candidate: Candidate) -> tuple[dict[PosteriorClass, float], EvidenceSummary]:
    f = candidate.features
    ir_excess = _score(f, "ir_excess_score")
    sed_residual = _score(f, "sed_fit_residual_score")
    stellar = _score(f, "stellar_solution_quality")
    agn = _score(f, "galaxy_agn_indicator_score")
    dust = _score(f, "dust_indicator_score")
    confusion = _score(f, "confusion_score")
    photometry = _score(f, "photometric_quality_score", default=0.5)
    catalog_artifact = _score(f, "catalog_artifact_score")
    known = _score(f, "known_object_score")

    raw_scores = _empty_scores()
    raw_scores[PosteriorClass.TECHNOSIGNATURE_INTEREST] += (
        1.45 * ir_excess
        + 1.15 * sed_residual
        + 1.20 * stellar
        + 1.05 * photometry
        + 1.15 * (1.0 - agn)
        + 1.05 * (1.0 - dust)
        + 1.00 * (1.0 - confusion)
    )
    raw_scores[PosteriorClass.NATURAL_SOURCE] += (
        1.60 * dust
        + 0.90 * _score(f, "young_stellar_object_score")
        + 0.90 * _score(f, "agb_like_color_score")
        + 0.70 * _score(f, "star_forming_region_score")
    )
    raw_scores[PosteriorClass.CATALOG_OR_PROCESSING_ERROR] += (
        1.35 * confusion + 1.20 * (1.0 - photometry) + 1.45 * catalog_artifact
    )
    raw_scores[PosteriorClass.INSTRUMENTAL_ARTIFACT] += 0.85 * catalog_artifact
    raw_scores[PosteriorClass.NOISE_OR_LOW_CONFIDENCE] += (
        0.95 * (1.0 - photometry) + 0.75 * (1.0 - stellar)
    )
    raw_scores[PosteriorClass.KNOWN_OBJECT] += 8.00 * known
    raw_scores[PosteriorClass.HUMAN_INTERFERENCE] += 0.05

    evidence = _infrared_evidence(
        ir_excess=ir_excess,
        sed_residual=sed_residual,
        stellar=stellar,
        agn=agn,
        dust=dust,
        confusion=confusion,
        photometry=photometry,
        catalog_artifact=catalog_artifact,
    )
    return raw_scores, evidence


def _anomaly_scores(candidate: Candidate) -> tuple[dict[PosteriorClass, float], EvidenceSummary]:
    f = candidate.features
    historical = _score(f, "historical_detection_score", default=0.5)
    modern_non_detection = _score(f, "modern_non_detection_score")
    magnitude_change = _scaled_positive_float(f, "magnitude_change", divisor=6.0)
    proper_motion = _score(f, "proper_motion_explanation_score")
    survey_depth = _score(f, "survey_depth_explanation_score")
    artifact = _score(f, "artifact_score")
    moving_object = _score(f, "moving_object_score")
    variability = _score(f, "variability_score")
    mismatch = _score(f, "catalog_mismatch_score")
    known = _score(f, "known_object_score")
    crossmatch_confidence = _score(f, "crossmatch_confidence", default=0.5)

    raw_scores = _empty_scores()
    raw_scores[PosteriorClass.TECHNOSIGNATURE_INTEREST] += (
        1.25 * historical
        + 1.30 * modern_non_detection
        + 0.95 * magnitude_change
        + 1.15 * (1.0 - proper_motion)
        + 1.00 * (1.0 - survey_depth)
        + 1.15 * (1.0 - artifact)
        + 0.90 * (1.0 - moving_object)
        + 0.85 * (1.0 - mismatch)
    )
    raw_scores[PosteriorClass.NATURAL_SOURCE] += (
        1.25 * variability + 1.10 * proper_motion + 1.05 * moving_object
    )
    raw_scores[PosteriorClass.CATALOG_OR_PROCESSING_ERROR] += (
        1.50 * artifact
        + 1.25 * mismatch
        + 1.00 * survey_depth
        + 0.65 * (1.0 - crossmatch_confidence)
    )
    raw_scores[PosteriorClass.INSTRUMENTAL_ARTIFACT] += 1.25 * artifact
    raw_scores[PosteriorClass.NOISE_OR_LOW_CONFIDENCE] += (
        0.95 * (1.0 - historical) + 0.70 * (1.0 - crossmatch_confidence)
    )
    raw_scores[PosteriorClass.KNOWN_OBJECT] += 8.00 * known
    raw_scores[PosteriorClass.HUMAN_INTERFERENCE] += 0.05

    evidence = _anomaly_evidence(
        historical=historical,
        modern_non_detection=modern_non_detection,
        magnitude_change=magnitude_change,
        proper_motion=proper_motion,
        survey_depth=survey_depth,
        artifact=artifact,
        moving_object=moving_object,
        variability=variability,
        mismatch=mismatch,
        crossmatch_confidence=crossmatch_confidence,
    )
    return raw_scores, evidence


def _derived_scores(
    candidate: Candidate, posterior: dict[PosteriorClass, float]
) -> CandidateScores:
    features = candidate.features
    false_positive_probability = _round_probability(
        1.0 - posterior[PosteriorClass.TECHNOSIGNATURE_INTEREST]
    )
    known_or_artifact = max(
        posterior[PosteriorClass.KNOWN_OBJECT],
        posterior[PosteriorClass.INSTRUMENTAL_ARTIFACT],
        posterior[PosteriorClass.CATALOG_OR_PROCESSING_ERROR],
        posterior[PosteriorClass.HUMAN_INTERFERENCE],
    )
    data_quality = _score(features, "data_quality_score", default=0.7)
    provenance = _score(features, "provenance_completeness_score", default=0.6)

    signal_reality = _round_probability(
        0.50 * posterior[PosteriorClass.TECHNOSIGNATURE_INTEREST]
        + 0.35 * (1.0 - posterior[PosteriorClass.NOISE_OR_LOW_CONFIDENCE])
        + 0.15 * data_quality
    )
    novelty = _round_probability(1.0 - known_or_artifact)
    followup = _round_probability(
        0.55 * posterior[PosteriorClass.TECHNOSIGNATURE_INTEREST]
        + 0.25 * signal_reality
        + 0.20 * novelty
    )
    readiness = _round_probability(
        0.40 * provenance + 0.35 * data_quality + 0.25 * signal_reality
    )

    return CandidateScores(
        false_positive_probability=false_positive_probability,
        signal_reality_confidence=signal_reality,
        novelty_score=novelty,
        followup_value=followup,
        review_readiness=readiness,
    )


def _empty_scores() -> dict[PosteriorClass, float]:
    return {posterior_class: 0.0 for posterior_class in PosteriorClass}


def _softmax(log_scores: dict[PosteriorClass, float]) -> dict[PosteriorClass, float]:
    max_score = max(log_scores.values())
    exp_scores = {
        posterior_class: math.exp(log_score - max_score)
        for posterior_class, log_score in log_scores.items()
    }
    total = sum(exp_scores.values())
    return {
        posterior_class: _round_probability(exp_score / total)
        for posterior_class, exp_score in exp_scores.items()
    }


def _score(features: DictLike, name: str, default: float = 0.0) -> float:
    value = features.get(name, default)
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, int | float):
        return _clamp(float(value))
    return default


def _float(features: DictLike, name: str, default: float = 0.0) -> float:
    value = features.get(name, default)
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, int | float):
        return float(value)
    return default


def _scaled_positive_float(features: DictLike, name: str, divisor: float) -> float:
    return _clamp(max(_float(features, name), 0.0) / divisor)


def _narrowband_score(bandwidth_hz: float) -> float:
    if bandwidth_hz <= 0.0:
        return 0.0
    return _clamp(1.0 - ((bandwidth_hz - 1.0) / 9.0))


def _drift_score(drift_rate_hz_per_sec: float) -> float:
    return _clamp(abs(drift_rate_hz_per_sec) / 5.0)


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))


def _round_probability(value: float) -> float:
    return round(_clamp(value), 6)


def _radio_evidence(
    *,
    snr: float,
    bandwidth: float,
    drift: float,
    on_target: float,
    off_target: float,
    rfi: float,
    persistence: float,
    artifact: float,
    injection: float,
    repeat: float,
    metadata: float,
) -> EvidenceSummary:
    positive: list[str] = []
    negative: list[str] = []
    blocking: list[str] = []

    _append_if(positive, snr >= 0.6, "High synthetic SNR supports signal reality.")
    _append_if(positive, bandwidth >= 0.7, "Signal morphology is narrowband.")
    _append_if(positive, drift >= 0.4, "Signal has nonzero Doppler drift.")
    _append_if(positive, on_target >= 0.7, "Signal appears in ON-target scans.")
    _append_if(positive, off_target <= 0.2, "Signal is weak or absent in OFF-target scans.")
    _append_if(positive, injection >= 0.7, "Similar synthetic injections are recoverable.")
    _append_if(positive, repeat >= 0.7, "Repeat observation support is present.")

    _append_if(negative, off_target >= 0.4, "Signal appears in OFF-target scans.")
    _append_if(negative, rfi >= 0.4, "Frequency overlaps known or suspected RFI.")
    _append_if(negative, persistence >= 0.4, "Frequency persists across unrelated contexts.")
    _append_if(negative, artifact >= 0.4, "Instrumental artifact evidence is present.")
    _append_if(
        negative,
        drift < 0.2,
        "Drift is zero or too small to help reject local interference.",
    )
    _append_if(
        negative,
        injection < 0.7,
        "Independent repeat or injection-recovery support is not strong.",
    )
    _append_if(negative, repeat < 0.7, "No strong repeat observation support is present.")

    _append_if(blocking, metadata < 0.5, "Observation metadata is incomplete.")
    _append_if(blocking, off_target > 0.2 and off_target < 0.4, "OFF-target evidence is ambiguous.")

    return EvidenceSummary(tuple(positive), tuple(negative), tuple(blocking))


def _infrared_evidence(
    *,
    ir_excess: float,
    sed_residual: float,
    stellar: float,
    agn: float,
    dust: float,
    confusion: float,
    photometry: float,
    catalog_artifact: float,
) -> EvidenceSummary:
    positive: list[str] = []
    negative: list[str] = []
    blocking: list[str] = []

    _append_if(
        positive,
        ir_excess >= 0.6,
        "Mid-infrared excess is significant in synthetic features.",
    )
    _append_if(
        positive,
        sed_residual >= 0.6,
        "SED residual is not well explained by a normal stellar model.",
    )
    _append_if(positive, stellar >= 0.7, "Gaia-like solution is stellar in character.")
    _append_if(positive, photometry >= 0.7, "Photometric quality is high.")
    _append_if(
        positive,
        confusion <= 0.2,
        "Source appears isolated in synthetic confusion features.",
    )

    _append_if(negative, agn >= 0.4, "Galaxy or AGN indicators are present.")
    _append_if(
        negative,
        dust >= 0.4,
        "Dust or natural astrophysical contaminant evidence is present.",
    )
    _append_if(negative, confusion >= 0.4, "Blending or source-confusion risk is present.")
    _append_if(negative, catalog_artifact >= 0.4, "Catalog artifact indicators are present.")

    _append_if(blocking, photometry < 0.5, "Photometric quality is too weak for external review.")
    _append_if(blocking, stellar < 0.5, "Stellar-source context is not secure.")

    return EvidenceSummary(tuple(positive), tuple(negative), tuple(blocking))


def _anomaly_evidence(
    *,
    historical: float,
    modern_non_detection: float,
    magnitude_change: float,
    proper_motion: float,
    survey_depth: float,
    artifact: float,
    moving_object: float,
    variability: float,
    mismatch: float,
    crossmatch_confidence: float,
) -> EvidenceSummary:
    positive: list[str] = []
    negative: list[str] = []
    blocking: list[str] = []

    _append_if(positive, historical >= 0.7, "Historical detection is strong in synthetic features.")
    _append_if(
        positive,
        modern_non_detection >= 0.7,
        "Modern non-detection or major change is strong.",
    )
    _append_if(positive, magnitude_change >= 0.6, "Photometric change is large.")
    _append_if(positive, proper_motion <= 0.2, "Proper motion does not explain the anomaly.")
    _append_if(positive, survey_depth <= 0.2, "Survey-depth mismatch does not explain the anomaly.")

    _append_if(
        negative,
        proper_motion >= 0.4,
        "Proper motion may explain the source position change.",
    )
    _append_if(
        negative,
        survey_depth >= 0.4,
        "Survey-depth or bandpass mismatch may explain the anomaly.",
    )
    _append_if(
        negative,
        artifact >= 0.4,
        "Plate, image, or processing artifact evidence is present.",
    )
    _append_if(negative, moving_object >= 0.4, "Moving-object explanation is plausible.")
    _append_if(negative, variability >= 0.4, "Natural variability may explain the change.")
    _append_if(negative, mismatch >= 0.4, "Catalog cross-match ambiguity is present.")

    _append_if(blocking, crossmatch_confidence < 0.5, "Cross-match confidence is too low.")
    _append_if(blocking, historical < 0.5, "Historical detection strength is insufficient.")

    return EvidenceSummary(tuple(positive), tuple(negative), tuple(blocking))


def _append_if(items: list[str], condition: bool, message: str) -> None:
    if condition:
        items.append(message)
