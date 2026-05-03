from techno_search.calibration_metrics import (
    PRECISION_RECALL_DISCLAIMER,
    PRECISION_RECALL_SCHEMA_VERSION,
    RELIABILITY_DISCLAIMER,
    RELIABILITY_SCHEMA_VERSION,
    load_precision_recall_cases,
    load_reliability_bins,
    precision_recall_summary,
    reliability_summary,
)


def test_reliability_fixture_bins_cover_all_tracks_and_score_ranges() -> None:
    bins = load_reliability_bins()

    assert len(bins) == 9
    assert {item.track.value for item in bins} == {"anomaly", "infrared", "radio"}
    assert {f"{item.score_min:.1f}-{item.score_max:.1f}" for item in bins} == {
        "0.0-0.3",
        "0.3-0.7",
        "0.7-1.0",
    }
    assert all(item.sample_count > 0 for item in bins)
    assert all(0.0 <= item.observed_fraction <= 1.0 for item in bins)


def test_reliability_summary_counts_by_track_and_score_bin() -> None:
    summary = reliability_summary()

    assert summary["schema_version"] == RELIABILITY_SCHEMA_VERSION
    assert summary["disclaimer"] == RELIABILITY_DISCLAIMER
    assert summary["bin_count"] == 9
    assert summary["total_sample_count"] == 150
    assert summary["by_track"] == {"anomaly": 3, "infrared": 3, "radio": 3}
    assert summary["score_bins"] == ["0.0-0.3", "0.3-0.7", "0.7-1.0"]
    assert summary["mean_absolute_calibration_error"] == 0.022933
    assert summary["max_absolute_calibration_error"] == 0.04


def test_precision_recall_fixture_cases_cover_candidate_and_false_positive_classes() -> None:
    cases = load_precision_recall_cases()

    assert len(cases) == 6
    assert {item.track.value for item in cases} == {"anomaly", "infrared", "radio"}
    assert {item.truth_class for item in cases} == {"candidate", "false_positive"}
    assert {item.score_threshold for item in cases} == {0.6}
    assert all(item.true_positive_count > 0 for item in cases)


def test_precision_recall_summary_counts_synthetic_classes() -> None:
    summary = precision_recall_summary()

    assert summary["schema_version"] == PRECISION_RECALL_SCHEMA_VERSION
    assert summary["disclaimer"] == PRECISION_RECALL_DISCLAIMER
    assert summary["case_count"] == 6
    assert summary["by_track"] == {"anomaly": 2, "infrared": 2, "radio": 2}
    assert summary["by_truth_class"] == {"candidate": 3, "false_positive": 3}
    assert summary["true_positive_count"] == 42
    assert summary["false_positive_count"] == 10
    assert summary["false_negative_count"] == 11
    assert summary["synthetic_precision"] == 0.807692
    assert summary["synthetic_recall"] == 0.792453
    assert summary["synthetic_f1_score"] == 0.8
