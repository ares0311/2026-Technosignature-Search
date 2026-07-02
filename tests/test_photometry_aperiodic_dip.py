from __future__ import annotations

import numpy as np
import pytest

from techno_search.photometry.aperiodic_dip import detect_aperiodic_dips


def _baseline_flux(n: int) -> np.ndarray:
    # Small deterministic ripple (not random noise) so the median absolute
    # deviation is nonzero without introducing test flakiness.
    return 1.0 + 0.0002 * np.sin(np.arange(n) * 0.7)


def test_detects_a_symmetric_dip_with_low_asymmetry() -> None:
    n = 200
    time = np.arange(n, dtype=float)
    flux = _baseline_flux(n)

    depth = 0.05
    ramp_down = np.linspace(0.0, depth, 10)
    ramp_up = np.linspace(depth, 0.0, 10)[1:]
    dip = np.concatenate([ramp_down, ramp_up])
    flux[50 : 50 + dip.size] -= dip

    events = detect_aperiodic_dips(time, flux, sigma_threshold=5.0, min_consecutive_cadences=3)

    assert len(events) == 1
    event = events[0]
    assert event.depth == pytest.approx(depth, abs=0.01)
    assert event.significance_sigma > 5.0
    assert event.ingress_egress_asymmetry is not None
    assert event.ingress_egress_asymmetry < 0.2


def test_detects_an_asymmetric_dip_with_high_asymmetry() -> None:
    n = 200
    time = np.arange(n, dtype=float)
    flux = _baseline_flux(n)

    depth = 0.05
    steep_ingress = np.linspace(0.0, depth, 3)
    shallow_egress = np.linspace(depth, 0.0, 25)[1:]
    dip = np.concatenate([steep_ingress, shallow_egress])
    flux[80 : 80 + dip.size] -= dip

    events = detect_aperiodic_dips(time, flux, sigma_threshold=5.0, min_consecutive_cadences=3)

    assert len(events) == 1
    event = events[0]
    assert event.ingress_egress_asymmetry is not None
    assert event.ingress_egress_asymmetry > 0.5


def test_flat_lightcurve_has_no_dips() -> None:
    n = 200
    time = np.arange(n, dtype=float)
    flux = _baseline_flux(n)

    events = detect_aperiodic_dips(time, flux, sigma_threshold=5.0, min_consecutive_cadences=3)

    assert events == []


def test_single_point_outlier_is_not_a_dip() -> None:
    n = 200
    time = np.arange(n, dtype=float)
    flux = _baseline_flux(n)
    flux[100] -= 0.2

    events = detect_aperiodic_dips(time, flux, sigma_threshold=5.0, min_consecutive_cadences=3)

    assert events == []
