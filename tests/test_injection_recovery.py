from techno_search.injection_recovery import (
    INJECTION_RECOVERY_DISCLAIMER,
    INJECTION_RECOVERY_SCHEMA_VERSION,
    injection_recovery_summary,
    load_injection_recovery_cases,
)


def test_injection_recovery_fixture_schema_and_tracks_are_loaded() -> None:
    cases = load_injection_recovery_cases()

    assert len(cases) == 6
    assert {case.track.value for case in cases} == {"anomaly", "infrared", "radio"}
    assert {case.outcome for case in cases} == {"false_alarm", "missed", "recovered"}
    assert all(0.0 <= case.recovery_score <= 1.0 for case in cases)


def test_injection_recovery_summary_counts_by_track_and_outcome() -> None:
    summary = injection_recovery_summary()

    assert summary["schema_version"] == INJECTION_RECOVERY_SCHEMA_VERSION
    assert summary["disclaimer"] == INJECTION_RECOVERY_DISCLAIMER
    assert summary["case_count"] == 6
    assert summary["by_track"] == {"anomaly": 2, "infrared": 2, "radio": 2}
    assert summary["by_outcome"] == {"false_alarm": 2, "missed": 1, "recovered": 3}
    assert summary["false_alarm_count"] == 2
    assert summary["missed_count"] == 1
    assert summary["recovered_count"] == 3
    assert summary["synthetic_recovery_rate"] == 0.75
    assert summary["synthetic_false_alarm_fraction"] == 0.333333
    assert summary["by_injection_type"] == {
        "synthetic_archival_disappearance": 2,
        "synthetic_infrared_excess": 2,
        "synthetic_narrowband_signal": 2,
    }
