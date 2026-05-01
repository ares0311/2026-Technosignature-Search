from techno_search.calibration import load_calibration_fixtures, summarize_calibration_fixtures
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
