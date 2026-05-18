"""ML training data scaffold assembled from calibration fixtures and injection-recovery cases."""

from __future__ import annotations

from typing import Any

ML_TRAINING_DATA_DISCLAIMER = (
    "ML training data summaries are provenance records for model development only. "
    "They do not constitute detections, discoveries, or external validation. "
    "All training cases are synthetic development fixtures."
)

_TRAIN_SPLIT = 0.80


def ml_training_data_summary() -> dict[str, Any]:
    from techno_search.calibration import load_calibration_fixtures
    from techno_search.injection_recovery import load_injection_recovery_cases

    cal_fixtures = load_calibration_fixtures()
    inj_cases = load_injection_recovery_cases()

    calibration_count = len(cal_fixtures)
    injection_count = len(inj_cases)
    total = calibration_count + injection_count

    by_track: dict[str, int] = {}
    pathway_breakdown: dict[str, int] = {}

    for f in cal_fixtures:
        track_key = f.candidate.track.value
        by_track[track_key] = by_track.get(track_key, 0) + 1
        pathway_breakdown[f.expected_pathway] = (
            pathway_breakdown.get(f.expected_pathway, 0) + 1
        )

    for c in inj_cases:
        by_track[c.track] = by_track.get(c.track, 0) + 1

    recommended_train = int(total * _TRAIN_SPLIT)
    recommended_test = total - recommended_train

    return {
        "disclaimer": ML_TRAINING_DATA_DISCLAIMER,
        "total_case_count": total,
        "calibration_case_count": calibration_count,
        "injection_recovery_case_count": injection_count,
        "by_track": by_track,
        "by_source": {
            "calibration": calibration_count,
            "injection_recovery": injection_count,
        },
        "recommended_train_count": recommended_train,
        "recommended_test_count": recommended_test,
        "pathway_breakdown": pathway_breakdown,
    }
