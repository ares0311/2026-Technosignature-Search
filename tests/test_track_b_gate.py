from techno_search.schemas import Candidate, Track
from techno_search.track_b_gate import track_b_unknown_candidate_gate


def _radio_candidate(**feature_overrides) -> Candidate:
    features = {
        "rfi_band_overlap_score": 0.0,
        "instrumental_artifact_score": 0.0,
        "abacab_cadence_score": 1.0,
        "semisupervised_anomaly_score": 0.9,
        **feature_overrides,
    }
    return Candidate(
        candidate_id="radio-test-1",
        track=Track.RADIO,
        features=features,
        source_ids=("dat-file-1",),
        provenance={"source_dataset": "gbt-test"},
    )


def _no_known_match_crossmatch() -> dict:
    return {"classification": "no_known_match"}


def test_gate_blocks_on_uncalibrated_anomaly_threshold() -> None:
    """Even a candidate that passes every other check cannot be eligible,
    because condition 8 (high anomaly score) has no calibrated threshold."""
    candidate = _radio_candidate()

    result = track_b_unknown_candidate_gate(
        candidate,
        crossmatch_result=_no_known_match_crossmatch(),
        satellite_result={"classification": "no_known_match"},
    )

    assert result["eligible_for_unknown_candidate"] is False
    assert result["unresolved_count"] >= 1
    anomaly_condition = next(
        c for c in result["conditions"] if c["condition_id"] == "has_high_anomaly_score"
    )
    assert anomaly_condition["satisfied"] is None
    assert anomaly_condition["evidence"]["semisupervised_anomaly_score"] == 0.9


def test_gate_fails_when_crossmatch_finds_known_pulsar() -> None:
    candidate = _radio_candidate()

    result = track_b_unknown_candidate_gate(
        candidate,
        crossmatch_result={"classification": "known_pulsar"},
        satellite_result={"classification": "no_known_match"},
    )

    assert result["eligible_for_unknown_candidate"] is False
    pulsar_condition = next(
        c for c in result["conditions"] if c["condition_id"] == "not_confidently_pulsar"
    )
    assert pulsar_condition["satisfied"] is False


def test_gate_fails_when_satellite_transmitter_matches() -> None:
    candidate = _radio_candidate()

    result = track_b_unknown_candidate_gate(
        candidate,
        crossmatch_result=_no_known_match_crossmatch(),
        satellite_result={"classification": "satellite_transmitter"},
    )

    satellite_condition = next(
        c for c in result["conditions"] if c["condition_id"] == "not_known_satellite_transmitter"
    )
    assert satellite_condition["satisfied"] is False
    assert result["eligible_for_unknown_candidate"] is False


def test_gate_fails_when_rfi_overlap_high() -> None:
    candidate = _radio_candidate(rfi_band_overlap_score=1.0)

    result = track_b_unknown_candidate_gate(
        candidate,
        crossmatch_result=_no_known_match_crossmatch(),
        satellite_result={"classification": "no_known_match"},
    )

    rfi_condition = next(
        c for c in result["conditions"] if c["condition_id"] == "not_known_rfi_region"
    )
    assert rfi_condition["satisfied"] is False


def test_gate_fails_when_instrumental_artifact_high() -> None:
    candidate = _radio_candidate(instrumental_artifact_score=0.9)

    result = track_b_unknown_candidate_gate(
        candidate,
        crossmatch_result=_no_known_match_crossmatch(),
        satellite_result={"classification": "no_known_match"},
    )

    artifact_condition = next(
        c for c in result["conditions"] if c["condition_id"] == "not_instrument_artifact"
    )
    assert artifact_condition["satisfied"] is False


def test_gate_unresolved_when_cadence_neutral() -> None:
    candidate = _radio_candidate(abacab_cadence_score=0.5)

    result = track_b_unknown_candidate_gate(
        candidate,
        crossmatch_result=_no_known_match_crossmatch(),
        satellite_result={"classification": "no_known_match"},
    )

    cadence_condition = next(
        c for c in result["conditions"] if c["condition_id"] == "passes_cadence_checks"
    )
    assert cadence_condition["satisfied"] is None


def test_gate_fails_when_cadence_fails() -> None:
    candidate = _radio_candidate(abacab_cadence_score=0.0)

    result = track_b_unknown_candidate_gate(
        candidate,
        crossmatch_result=_no_known_match_crossmatch(),
        satellite_result={"classification": "no_known_match"},
    )

    cadence_condition = next(
        c for c in result["conditions"] if c["condition_id"] == "passes_cadence_checks"
    )
    assert cadence_condition["satisfied"] is False


def test_gate_unresolved_when_catalog_low_confidence() -> None:
    candidate = _radio_candidate()

    result = track_b_unknown_candidate_gate(
        candidate,
        crossmatch_result={"classification": "low_confidence"},
        satellite_result={"classification": "no_known_match"},
    )

    pulsar_condition = next(
        c for c in result["conditions"] if c["condition_id"] == "not_confidently_pulsar"
    )
    assert pulsar_condition["satisfied"] is None
    assert result["eligible_for_unknown_candidate"] is False


def test_gate_fails_provenance_when_no_source_ids() -> None:
    candidate = Candidate(
        candidate_id="radio-no-provenance",
        track=Track.RADIO,
        features={},
        source_ids=(),
        provenance={},
    )

    result = track_b_unknown_candidate_gate(
        candidate,
        crossmatch_result=_no_known_match_crossmatch(),
        satellite_result={"classification": "no_known_match"},
    )

    provenance_condition = next(
        c for c in result["conditions"] if c["condition_id"] == "has_preserved_provenance"
    )
    assert provenance_condition["satisfied"] is False


def test_gate_disclaimer_present() -> None:
    candidate = _radio_candidate()
    result = track_b_unknown_candidate_gate(
        candidate,
        crossmatch_result=_no_known_match_crossmatch(),
    )
    assert "local triage queue state only" in result["disclaimer"]


def test_gate_satellite_result_optional() -> None:
    candidate = _radio_candidate()
    result = track_b_unknown_candidate_gate(
        candidate,
        crossmatch_result=_no_known_match_crossmatch(),
    )
    satellite_condition = next(
        c for c in result["conditions"] if c["condition_id"] == "not_known_satellite_transmitter"
    )
    assert satellite_condition["satisfied"] is None
