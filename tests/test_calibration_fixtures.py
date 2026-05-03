from techno_search.calibration import (
    false_positive_class_summary,
    load_calibration_fixtures,
    summarize_calibration_fixtures,
)
from techno_search.schemas import Pathway
from techno_search.scoring import score_candidate


def test_false_positive_calibration_fixtures_are_suppressed() -> None:
    for fixture in load_calibration_fixtures():
        scored = score_candidate(fixture.candidate)

        assert scored.recommended_pathway == fixture.expected_pathway
        assert scored.scores.false_positive_probability >= 0.8
        assert scored.evidence.negative_evidence


def test_calibration_fixture_summary_counts_expected_classes() -> None:
    summary = summarize_calibration_fixtures(load_calibration_fixtures())

    assert summary.total == 15
    assert summary.by_expected_pathway == {Pathway.DO_NOT_SUBMIT_FALSE_POSITIVE.value: 15}
    assert summary.by_track == {"anomaly": 6, "infrared": 5, "radio": 4}
    assert summary.by_false_positive_class["rfi"] == 1
    assert summary.by_false_positive_class["catalog_mismatch"] == 1
    assert summary.by_false_positive_class["satellite_like_recurrence"] == 1
    assert summary.by_false_positive_class["extragalactic_contaminant"] == 1
    assert summary.by_false_positive_class["variable_star"] == 1


def test_false_positive_class_summary_groups_classes_by_track() -> None:
    summary = false_positive_class_summary()

    assert summary["schema_version"] == "synthetic_false_positive_analysis_v1"
    assert summary["case_count"] == 15
    assert summary["class_count"] == 15
    assert summary["by_track"] == {"anomaly": 6, "infrared": 5, "radio": 4}
    assert summary["by_expected_pathway"] == {
        Pathway.DO_NOT_SUBMIT_FALSE_POSITIVE.value: 15
    }
    assert summary["by_track_and_class"] == {
        "anomaly": {
            "catalog_mismatch": 1,
            "image_artifact": 1,
            "moving_object": 1,
            "proper_motion": 1,
            "survey_depth": 1,
            "variable_star": 1,
        },
        "infrared": {
            "agb_like_colors": 1,
            "agn_blend": 1,
            "bad_photometry": 1,
            "dust_or_yso": 1,
            "extragalactic_contaminant": 1,
        },
        "radio": {
            "radio_band_edge_artifact": 1,
            "radio_instrumental_artifact": 1,
            "rfi": 1,
            "satellite_like_recurrence": 1,
        },
    }
    assert summary["candidate_ids_by_class"]["rfi"] == ["cal-radio-rfi"]
    assert "calibration_false_positives.json" in str(summary["fixture_path"])
