"""Tests for real BLS transit search wrapping lightkurve/astropy.

The injected light curves here are test fixtures used to verify the code
computes real astropy/lightkurve statistics correctly -- they are not
training or calibration data (no model is fit to them; c.f. the existing
Fermi FITS regression test's synthetic in-memory astropy.Table).
"""

from __future__ import annotations

import numpy as np
import pytest

lightkurve = pytest.importorskip("lightkurve")

from techno_search.photometry.bls_detection import run_bls_transit_search  # noqa: E402


def _injected_transit_lightcurve(
    *,
    period: float = 3.5,
    depth: float = 0.01,
    duration: float = 0.1,
    n_days: float = 27.0,
    cadence_per_day: int = 48,
    noise_sigma: float = 0.0005,
    seed: int = 42,
):
    rng = np.random.default_rng(seed)
    time = np.linspace(0.0, n_days, int(n_days * cadence_per_day))
    flux = np.ones_like(time)
    phase = np.abs(((time + period / 2.0) % period) - period / 2.0)
    in_transit = phase < duration / 2.0
    flux[in_transit] -= depth
    flux += rng.normal(0.0, noise_sigma, size=time.shape)
    return lightkurve.LightCurve(time=time, flux=flux).remove_nans().normalize()


def test_bls_recovers_injected_period_and_depth() -> None:
    lc = _injected_transit_lightcurve(period=3.5, depth=0.01, duration=0.1)

    result = run_bls_transit_search(lc, minimum_period=1.0, maximum_period=10.0)

    assert result.period_days == pytest.approx(3.5, abs=0.05)
    assert result.depth == pytest.approx(0.01, abs=0.004)
    assert result.transit_count >= 6
    assert result.depth_err > 0.0


def test_bls_odd_even_mismatch_is_small_for_a_real_single_period_transit() -> None:
    lc = _injected_transit_lightcurve(period=3.5, depth=0.01, duration=0.1)

    result = run_bls_transit_search(lc, minimum_period=1.0, maximum_period=10.0)

    assert result.odd_even_depth_mismatch() < 1.0


def test_bls_half_period_ratio_is_computed() -> None:
    lc = _injected_transit_lightcurve(period=3.5, depth=0.01, duration=0.1)

    result = run_bls_transit_search(lc, minimum_period=1.0, maximum_period=10.0)

    ratio = result.half_period_depth_ratio()
    assert ratio >= 0.0


def test_bls_flat_lightcurve_has_no_meaningful_depth() -> None:
    time = np.linspace(0.0, 27.0, 27 * 48)
    rng = np.random.default_rng(7)
    flux = np.ones_like(time) + rng.normal(0.0, 0.0002, size=time.shape)
    lc = lightkurve.LightCurve(time=time, flux=flux).remove_nans().normalize()

    result = run_bls_transit_search(lc, minimum_period=1.0, maximum_period=10.0)

    assert abs(result.depth) < 0.005
