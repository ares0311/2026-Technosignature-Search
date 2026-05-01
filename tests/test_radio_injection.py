from techno_search import score_candidate
from techno_search.radio import (
    SyntheticRadioInjection,
    build_radio_candidate,
    injection_recovery_score,
)
from techno_search.schemas import PosteriorClass


def test_injection_recovery_score_rewards_close_recovery() -> None:
    injection = SyntheticRadioInjection(
        frequency_hz=1_420_000_000.0,
        drift_rate_hz_per_sec=2.0,
        snr=30.0,
    )

    recovered = injection_recovery_score(
        injection,
        recovered_frequency_hz=1_420_000_000.5,
        recovered_drift_rate_hz_per_sec=2.05,
    )
    missed = injection_recovery_score(
        injection,
        recovered_frequency_hz=None,
        recovered_drift_rate_hz_per_sec=None,
    )

    assert recovered > 0.8
    assert missed == 0.0


def test_injection_hit_row_flows_into_radio_candidate_features() -> None:
    injection = SyntheticRadioInjection(
        frequency_hz=1_420_000_000.0,
        drift_rate_hz_per_sec=2.0,
        snr=34.0,
    )
    row = injection.as_hit_row(recovered_score=0.91)

    candidate = build_radio_candidate("radio-injection", [row])

    assert candidate.features["injection_recovery_score"] == 0.91


def test_injection_recovery_evidence_improves_candidate_interest_score() -> None:
    base_row = {
        "frequency_hz": 1_420_000_000.0,
        "drift_rate_hz_per_sec": 2.0,
        "snr": 34.0,
        "bandwidth_hz": 1.5,
        "scan_role": "on",
        "target_id": "target-a",
    }
    recovered = build_radio_candidate(
        "radio-injection-recovered",
        [base_row | {"injection_recovery_score": 0.95}],
        provenance={"source_dataset": "synthetic-injection"},
    )
    not_recovered = build_radio_candidate(
        "radio-injection-missed",
        [base_row | {"injection_recovery_score": 0.0}],
        provenance={"source_dataset": "synthetic-injection"},
    )

    recovered_score = score_candidate(recovered)
    missed_score = score_candidate(not_recovered)

    assert (
        recovered_score.posterior[PosteriorClass.TECHNOSIGNATURE_INTEREST]
        > missed_score.posterior[PosteriorClass.TECHNOSIGNATURE_INTEREST]
    )
