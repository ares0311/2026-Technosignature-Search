from techno_search.schemas import Candidate, Track
from techno_search.track_b_gate import (
    track_b_candidate_packet_readiness,
    track_b_unknown_candidate_gate,
)


def _radio_candidate(**feature_overrides) -> Candidate:
    features = {
        "rfi_band_overlap_score": 0.0,
        "instrumental_artifact_score": 0.0,
        "abacab_cadence_score": 1.0,
        "semisupervised_anomaly_score": 0.9,
        "snr": 20.0,
        **feature_overrides,
    }
    return Candidate(
        candidate_id="radio-test-1",
        track=Track.RADIO,
        features=features,
        source_ids=("dat-file-1",),
        provenance={"source_dataset": "gbt-test", "processing_snr_threshold": 10.0},
    )


def _no_known_match_crossmatch() -> dict:
    return {"classification": "no_known_match"}


def test_gate_unknown_does_not_depend_on_anomaly_calibration() -> None:
    """Unknownness is exhausted known-class checking, not an anomaly threshold."""
    candidate = _radio_candidate()

    result = track_b_unknown_candidate_gate(
        candidate,
        crossmatch_result=_no_known_match_crossmatch(),
        satellite_result={"classification": "no_known_match"},
    )

    assert result["eligible_for_unknown_candidate"] is True
    assert result["classification_state"] == "unknown"
    assert result["unresolved_count"] == 0
    assert all(
        condition["condition_id"] != "has_high_anomaly_score"
        for condition in result["conditions"]
    )
    assert result["ranking_evidence"]["semisupervised_anomaly_score"] == 0.9
    assert result["ranking_evidence"]["affects_classification_state"] is False


def test_gate_missing_provenance_is_unresolved_not_unknown() -> None:
    candidate = _radio_candidate()
    candidate = Candidate(
        candidate_id=candidate.candidate_id,
        track=candidate.track,
        features=candidate.features,
        source_ids=(),
        provenance={},
    )

    result = track_b_unknown_candidate_gate(
        candidate,
        crossmatch_result=_no_known_match_crossmatch(),
        satellite_result={"classification": "no_known_match"},
    )

    assert result["classification_state"] == "unresolved"
    assert result["eligible_for_unknown_candidate"] is False
    provenance = next(
        condition
        for condition in result["conditions"]
        if condition["condition_id"] == "has_preserved_provenance"
    )
    assert provenance["satisfied"] is None


def test_validated_hit_table_satisfies_detector_threshold_without_duplicate_number(
) -> None:
    candidate = _radio_candidate(hit_count=1)
    candidate = Candidate(
        candidate_id=candidate.candidate_id,
        track=candidate.track,
        features=candidate.features,
        source_ids=candidate.source_ids,
        provenance={
            "source_dataset": "retained-real-data",
            "source_file": "retained.dat",
            "reader_type": "turboSETI_csv",
        },
    )

    result = track_b_unknown_candidate_gate(
        candidate,
        crossmatch_result=_no_known_match_crossmatch(),
        satellite_result={"classification": "no_known_match"},
    )

    threshold = next(
        condition
        for condition in result["conditions"]
        if condition["condition_id"] == "not_below_search_threshold"
    )
    assert threshold["satisfied"] is True
    assert threshold["evidence"]["evidence_basis"] == (
        "validated_hit_bearing_turboseti_dat"
    )
    assert result["classification_state"] == "unknown"


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
    assert provenance_condition["satisfied"] is None
    assert result["classification_state"] == "unresolved"


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


def test_candidate_packet_readiness_reports_missing_evidence_without_guessing() -> None:
    candidate = _radio_candidate(frequency_hz=1_420_000_000.0, ra_deg=83.0, dec_deg=22.0)

    result = track_b_candidate_packet_readiness(candidate)

    assert result["gate_evaluated"] is False
    assert result["track_a_crossmatch"]["status"] == "ready_to_run"
    assert result["track_a_crossmatch"]["missing_candidate_fields"] == []
    assert result["satellite_match"]["status"] == "missing_inputs"
    assert "observation_time_utc" in result["satellite_match"]["missing_candidate_fields"]
    assert "missing_track_a_crossmatch_json" in result["blocking_reason_ids"]
    assert result["eligible_for_unknown_candidate"] is False


def test_candidate_packet_readiness_runs_gate_when_crossmatch_is_supplied() -> None:
    candidate = _radio_candidate(
        frequency_hz=1_420_000_000.0,
        ra_deg=83.0,
        dec_deg=22.0,
        observation_time_utc="2026-01-01T00:00:00Z",
        observer_lat_deg=38.4331,
        observer_lon_deg=-79.8398,
        observer_elevation_m=807.0,
    )

    result = track_b_candidate_packet_readiness(
        candidate,
        crossmatch_result=_no_known_match_crossmatch(),
        satellite_result={"classification": "no_known_match"},
    )

    assert result["gate_evaluated"] is True
    assert result["track_a_crossmatch"]["status"] == "provided"
    assert result["satellite_match"]["status"] == "provided"
    assert result["gate_result"]["unresolved_count"] == 0
    assert result["eligible_for_unknown_candidate"] is True


def test_candidate_packet_readiness_blocks_zero_hit_non_detection() -> None:
    candidate = Candidate(
        candidate_id="zero-hit-realistic",
        track=Track.RADIO,
        features={
            "zero_hit_non_detection": True,
            "rfi_band_overlap_score": 0.0,
            "instrumental_artifact_score": 0.0,
            "abacab_cadence_score": 0.0,
        },
        source_ids=("zero-hit.dat",),
        provenance={"source_file": "zero-hit.dat"},
    )

    result = track_b_candidate_packet_readiness(
        candidate,
        crossmatch_result=_no_known_match_crossmatch(),
    )

    assert "zero_hit_non_detection_is_not_a_track_b_candidate" in result[
        "blocking_reason_ids"
    ]
    assert "semisupervised_anomaly_score" not in result["missing_candidate_feature_ids"]
    assert result["eligible_for_unknown_candidate"] is False
