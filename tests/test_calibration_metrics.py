from techno_search.calibration_metrics import (
    RELIABILITY_DISCLAIMER,
    RELIABILITY_SCHEMA_VERSION,
    load_reliability_bins,
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
