"""Conservative pathway classification."""

from __future__ import annotations

from dataclasses import dataclass

from techno_search.schemas import CandidateScores, Pathway, PosteriorClass


@dataclass(frozen=True)
class PathwayThresholds:
    """Initial pathway thresholds from the scoring model specification."""

    known_object_probability: float = 0.80
    false_positive_probability: float = 0.80
    minimum_signal_reality_for_review: float = 0.40
    candidate_interest_probability: float = 0.60
    candidate_max_false_positive_probability: float = 0.40
    candidate_signal_reality: float = 0.70
    candidate_review_readiness: float = 0.70


DEFAULT_PATHWAY_THRESHOLDS = PathwayThresholds()


def classify_pathway(
    posterior: dict[PosteriorClass, float],
    scores: CandidateScores,
    thresholds: PathwayThresholds = DEFAULT_PATHWAY_THRESHOLDS,
) -> Pathway:
    """Route a candidate to a conservative next step."""

    if posterior[PosteriorClass.KNOWN_OBJECT] >= thresholds.known_object_probability:
        return Pathway.KNOWN_OBJECT_ANNOTATION

    if scores.false_positive_probability >= thresholds.false_positive_probability:
        return Pathway.DO_NOT_SUBMIT_FALSE_POSITIVE

    if scores.signal_reality_confidence < thresholds.minimum_signal_reality_for_review:
        return Pathway.GITHUB_REPRODUCIBILITY_ONLY

    if (
        posterior[PosteriorClass.TECHNOSIGNATURE_INTEREST]
        >= thresholds.candidate_interest_probability
        and scores.false_positive_probability <= thresholds.candidate_max_false_positive_probability
        and scores.signal_reality_confidence >= thresholds.candidate_signal_reality
        and scores.review_readiness >= thresholds.candidate_review_readiness
    ):
        return Pathway.CANDIDATE_REVIEW_PACKET

    return Pathway.HUMAN_REVIEW_QUEUE
