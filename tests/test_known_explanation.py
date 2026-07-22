from __future__ import annotations

from techno_search.known_explanation import resolve_radio_known_explanations
from techno_search.schemas import Candidate, Track


def _complete_candidate(**features: object) -> Candidate:
    return Candidate(
        candidate_id="radio-resolution-test",
        track=Track.RADIO,
        features={
            "ra_deg": 83.0,
            "dec_deg": 22.0,
            "frequency_hz": 1_420_000_000.0,
            "observation_time_utc": "2026-01-01T00:00:00Z",
            "observer_lat_deg": 38.43312111111111,
            "observer_lon_deg": -79.839835,
            "observer_elevation_m": 807.43,
            "rfi_band_overlap_score": 0.0,
            "instrumental_artifact_score": 0.0,
            "abacab_cadence_score": 1.0,
            "snr": 20.0,
            **features,
        },
        source_ids=("real-observation.dat",),
        provenance={
            "source_dataset": "real-test-observation",
            "processing_snr_threshold": 10.0,
        },
    )


def _no_match_crossmatch(*args: object, **kwargs: object) -> dict[str, object]:
    return {"classification": "no_known_match", "catalogs_missing": []}


def _no_match_satellite(**kwargs: object) -> dict[str, object]:
    return {"classification": "no_known_match", "catalogs_missing": []}


def test_complete_no_match_is_unknown_without_anomaly_score() -> None:
    result = resolve_radio_known_explanations(
        _complete_candidate(),
        crossmatch_runner=_no_match_crossmatch,
        satellite_runner=_no_match_satellite,
    )

    assert result["classification_state"] == "unknown"
    assert result["eligible_for_unknown_candidate"] is True
    assert result["adversarial_review_required"] is True
    assert result["ranking_evidence"]["semisupervised_anomaly_score"] is None


def test_catalog_match_is_known_even_when_anomaly_score_is_high() -> None:
    def known_pulsar(*args: object, **kwargs: object) -> dict[str, object]:
        return {"classification": "known_pulsar", "catalogs_missing": []}

    result = resolve_radio_known_explanations(
        _complete_candidate(semisupervised_anomaly_score=1.0),
        crossmatch_runner=known_pulsar,
        satellite_runner=_no_match_satellite,
    )

    assert result["classification_state"] == "known"
    assert result["eligible_for_unknown_candidate"] is False
    assert result["known_explanations"][0]["condition_id"] == "not_confidently_pulsar"


def test_missing_required_satellite_inputs_is_unresolved() -> None:
    candidate = _complete_candidate()
    candidate = Candidate(
        candidate_id=candidate.candidate_id,
        track=candidate.track,
        features={
            key: value
            for key, value in candidate.features.items()
            if key != "observer_elevation_m"
        },
        source_ids=candidate.source_ids,
        provenance=candidate.provenance,
    )

    result = resolve_radio_known_explanations(
        candidate,
        crossmatch_runner=_no_match_crossmatch,
        satellite_runner=_no_match_satellite,
    )

    assert result["classification_state"] == "unresolved"
    assert result["satellite_match"]["status"] == "missing_inputs"
    assert result["satellite_match"]["missing_candidate_fields"] == [
        "observer_elevation_m"
    ]


def test_rfi_match_is_known_even_when_catalogs_are_unavailable() -> None:
    def missing_catalogs(*args: object, **kwargs: object) -> dict[str, object]:
        return {"classification": "low_confidence", "catalogs_missing": ["atnf"]}

    result = resolve_radio_known_explanations(
        _complete_candidate(rfi_band_overlap_score=1.0),
        crossmatch_runner=missing_catalogs,
        satellite_runner=_no_match_satellite,
    )

    assert result["classification_state"] == "known"
    assert any(
        explanation["condition_id"] == "not_known_rfi_region"
        for explanation in result["known_explanations"]
    )
