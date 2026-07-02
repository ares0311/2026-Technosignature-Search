"""Tests for real flat-bottom-vs-V-shape transit discrimination.

Injected light curves here are constructed test fixtures used to verify the
least-squares model comparison is computed correctly -- they are not
training or calibration data (no model is fit to a corpus; c.f. the
existing Fermi FITS regression test's synthetic in-memory astropy.Table).
"""

from __future__ import annotations

import numpy as np

from techno_search.photometry.bls_detection import BlsTransitResult
from techno_search.photometry.transit_shape import classify_transit_shape


def _bls_result(period: float, duration: float, transit_time: float) -> BlsTransitResult:
    return BlsTransitResult(
        period_days=period,
        duration_days=duration,
        transit_time_value=transit_time,
        transit_time_format="btjd",
        max_power=0.01,
        depth=0.01,
        depth_err=0.001,
        depth_odd=0.01,
        depth_odd_err=0.001,
        depth_even=0.01,
        depth_even_err=0.001,
        depth_half=0.0,
        depth_half_err=0.001,
        harmonic_amplitude=0.0,
        harmonic_delta_log_likelihood=-1.0,
        transit_count=10,
        per_transit_log_likelihood_cv=0.05,
    )


def _folded_time_grid(period: float, n_cycles: int, cadence_per_day: int = 200) -> np.ndarray:
    return np.linspace(0.0, period * n_cycles, int(period * n_cycles * cadence_per_day))


def test_box_shaped_dip_scores_flat_bottom_positive() -> None:
    period = 3.0
    duration = 0.2
    depth = 0.02
    time = _folded_time_grid(period, 20)
    flux = np.ones_like(time)
    phase = ((time + period / 2.0) % period) - period / 2.0
    in_transit = np.abs(phase) <= duration / 2.0
    flux[in_transit] -= depth

    result = classify_transit_shape(time, flux, _bls_result(period, duration, 0.0))

    assert result.computable
    assert result.flat_bottom_score() > 0.5
    assert result.grazing_eclipse_score() < 0.1


def test_v_shaped_dip_scores_flat_bottom_negative() -> None:
    period = 3.0
    duration = 0.2
    depth = 0.02
    time = _folded_time_grid(period, 20)
    flux = np.ones_like(time)
    phase = ((time + period / 2.0) % period) - period / 2.0
    half_dur = duration / 2.0
    in_transit = np.abs(phase) <= half_dur
    triangular_depth = depth * (1.0 - np.abs(phase[in_transit]) / half_dur)
    flux[in_transit] -= triangular_depth

    result = classify_transit_shape(time, flux, _bls_result(period, duration, 0.0))

    assert result.computable
    assert result.flat_bottom_score() < -0.5
    assert result.grazing_eclipse_score() > 0.5


def test_too_few_in_transit_points_is_not_computable() -> None:
    time = np.array([0.0, 10.0, 20.0])
    flux = np.array([1.0, 1.0, 1.0])
    result = classify_transit_shape(time, flux, _bls_result(3.0, 0.01, 0.0))

    assert not result.computable
    assert result.reason is not None


def test_invalid_period_is_not_computable() -> None:
    time = np.linspace(0.0, 10.0, 100)
    flux = np.ones_like(time)
    result = classify_transit_shape(time, flux, _bls_result(0.0, 0.2, 0.0))

    assert not result.computable


def test_grazing_eclipse_score_is_clamped_to_unit_interval() -> None:
    period = 3.0
    duration = 0.2
    time = _folded_time_grid(period, 20)
    flux = np.ones_like(time)
    phase = ((time + period / 2.0) % period) - period / 2.0
    half_dur = duration / 2.0
    in_transit = np.abs(phase) <= half_dur
    triangular_depth = 0.05 * (1.0 - np.abs(phase[in_transit]) / half_dur)
    flux[in_transit] -= triangular_depth

    result = classify_transit_shape(time, flux, _bls_result(period, duration, 0.0))

    assert 0.0 <= result.grazing_eclipse_score() <= 1.0
    assert -1.0 <= result.flat_bottom_score() <= 1.0
