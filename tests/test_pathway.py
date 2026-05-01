from techno_search.pathway import classify_pathway
from techno_search.schemas import CandidateScores, Pathway, PosteriorClass


def _posterior(**overrides: float) -> dict[PosteriorClass, float]:
    base = {
        PosteriorClass.TECHNOSIGNATURE_INTEREST: 0.1,
        PosteriorClass.NATURAL_SOURCE: 0.2,
        PosteriorClass.HUMAN_INTERFERENCE: 0.2,
        PosteriorClass.INSTRUMENTAL_ARTIFACT: 0.2,
        PosteriorClass.CATALOG_OR_PROCESSING_ERROR: 0.1,
        PosteriorClass.KNOWN_OBJECT: 0.0,
        PosteriorClass.NOISE_OR_LOW_CONFIDENCE: 0.2,
    }
    for key, value in overrides.items():
        base[PosteriorClass(key)] = value
    return base


def _scores(
    false_positive_probability: float = 0.5,
    signal_reality_confidence: float = 0.7,
    review_readiness: float = 0.7,
) -> CandidateScores:
    return CandidateScores(
        false_positive_probability=false_positive_probability,
        signal_reality_confidence=signal_reality_confidence,
        novelty_score=0.7,
        followup_value=0.7,
        review_readiness=review_readiness,
    )


def test_known_object_takes_precedence() -> None:
    pathway = classify_pathway(
        _posterior(known_object=0.85, technosignature_interest=0.05),
        _scores(false_positive_probability=0.95),
    )

    assert pathway == Pathway.KNOWN_OBJECT_ANNOTATION


def test_high_false_positive_probability_is_suppressed() -> None:
    pathway = classify_pathway(
        _posterior(technosignature_interest=0.15),
        _scores(false_positive_probability=0.85),
    )

    assert pathway == Pathway.DO_NOT_SUBMIT_FALSE_POSITIVE


def test_low_signal_reality_stays_reproducibility_only() -> None:
    pathway = classify_pathway(
        _posterior(technosignature_interest=0.35),
        _scores(false_positive_probability=0.65, signal_reality_confidence=0.25),
    )

    assert pathway == Pathway.GITHUB_REPRODUCIBILITY_ONLY


def test_strong_candidate_gets_review_packet() -> None:
    pathway = classify_pathway(
        _posterior(technosignature_interest=0.65),
        _scores(
            false_positive_probability=0.35,
            signal_reality_confidence=0.75,
            review_readiness=0.78,
        ),
    )

    assert pathway == Pathway.CANDIDATE_REVIEW_PACKET
