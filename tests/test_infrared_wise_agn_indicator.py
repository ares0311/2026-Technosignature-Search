from __future__ import annotations

import pytest

from techno_search.infrared_wise.agn_indicator import wise_agn_indicator


def test_missing_magnitudes_are_not_computable() -> None:
    result = wise_agn_indicator(None, 5.0)
    assert result.computable is False
    assert result.agn_indicator_score() == 0.0


def test_normal_star_color_scores_zero() -> None:
    # A typical stellar photosphere has W1-W2 close to zero.
    result = wise_agn_indicator(w1_mag=8.0, w2_mag=8.02)
    assert result.computable
    assert result.meets_stern_2012_reliable_threshold is False
    assert result.meets_assef_2013_complete_threshold is False
    assert result.agn_indicator_score() == 0.0


def test_stern_2012_reliable_threshold_scores_one() -> None:
    result = wise_agn_indicator(w1_mag=8.0, w2_mag=7.1)
    assert result.computable
    assert result.w1_minus_w2 == pytest.approx(0.9)
    assert result.meets_stern_2012_reliable_threshold is True
    assert result.agn_indicator_score() == 1.0


def test_assef_2013_complete_only_threshold_scores_half() -> None:
    result = wise_agn_indicator(w1_mag=8.0, w2_mag=7.4)
    assert result.computable
    assert result.w1_minus_w2 == pytest.approx(0.6)
    assert result.meets_stern_2012_reliable_threshold is False
    assert result.meets_assef_2013_complete_threshold is True
    assert result.agn_indicator_score() == 0.5


def test_magnitude_reliability_limit_is_reported_when_given() -> None:
    within = wise_agn_indicator(8.0, 7.1, w2_mag_for_reliability_limit=14.0)
    outside = wise_agn_indicator(8.0, 7.1, w2_mag_for_reliability_limit=16.0)

    assert within.within_stern_2012_magnitude_limit is True
    assert outside.within_stern_2012_magnitude_limit is False
