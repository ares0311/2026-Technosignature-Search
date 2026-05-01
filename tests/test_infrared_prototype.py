import pytest

from techno_search import score_candidate
from techno_search.infrared import build_infrared_candidate
from techno_search.schemas import PosteriorClass, Track


def test_build_infrared_candidate_normalizes_catalog_features() -> None:
    candidate = build_infrared_candidate(
        "ir-prototype",
        {
            "gaia_source_id": "Gaia DR3 1",
            "ra": 10.0,
            "dec": -2.0,
            "parallax": 3.0,
            "proper_motion": 25.0,
            "g_mag": 12.0,
            "bp_rp": 1.1,
            "w1": 10.0,
            "w2": 9.8,
            "w3": 7.2,
            "w4": 6.9,
            "photometric_quality_score": 0.9,
        },
        provenance={"source_dataset": "synthetic-infrared"},
    )

    assert candidate.track == Track.INFRARED
    assert candidate.features["gaia_source_id"] == "Gaia DR3 1"
    assert candidate.features["ir_excess_score"] > 0.8
    assert candidate.features["stellar_solution_quality"] > 0.5
    assert candidate.provenance["source_dataset"] == "synthetic-infrared"


def test_clean_infrared_candidate_scores_above_agn_confused_source() -> None:
    clean = build_infrared_candidate(
        "ir-clean-prototype",
        {
            "gaia_source_id": "Gaia DR3 clean",
            "parallax": 4.5,
            "proper_motion": 30.0,
            "w1": 10.0,
            "w2": 9.7,
            "w3": 7.0,
            "w4": 6.8,
            "photometric_quality_score": 0.92,
            "confusion_score": 0.02,
            "galaxy_agn_indicator_score": 0.02,
            "dust_indicator_score": 0.04,
        },
        provenance={"source_dataset": "synthetic-infrared"},
    )
    agn = build_infrared_candidate(
        "ir-agn-prototype",
        {
            "gaia_source_id": "Gaia DR3 agn",
            "parallax": 0.1,
            "proper_motion": 0.2,
            "w1": 10.0,
            "w2": 9.8,
            "w3": 7.0,
            "w4": 6.5,
            "photometric_quality_score": 0.45,
            "confusion_score": 0.85,
            "galaxy_agn_indicator_score": 0.92,
            "dust_indicator_score": 0.55,
        },
        provenance={"source_dataset": "synthetic-infrared"},
    )

    clean_score = score_candidate(clean)
    agn_score = score_candidate(agn)

    assert (
        clean_score.posterior[PosteriorClass.TECHNOSIGNATURE_INTEREST]
        > agn_score.posterior[PosteriorClass.TECHNOSIGNATURE_INTEREST]
    )
    assert "Galaxy or AGN indicators are present." in agn_score.evidence.negative_evidence


def test_infrared_candidate_requires_mid_ir_fields() -> None:
    with pytest.raises(ValueError, match="w1"):
        build_infrared_candidate("missing-w1", {"w2": 9.0, "w3": 7.0})
