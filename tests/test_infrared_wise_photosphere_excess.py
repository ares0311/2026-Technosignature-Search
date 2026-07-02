"""Tests for the real WISE photospheric blackbody excess check.

Test fixtures here forward-model real astropy BlackBody flux at the WISE
effective wavelengths for a chosen real physical temperature, then convert
back to WISE Vega magnitudes using the same verified zero points the module
uses -- this exercises the real code path end-to-end. It is a
code-correctness fixture, not training/calibration data (no model is fit;
c.f. the existing Fermi FITS regression test's synthetic in-memory
astropy.Table).
"""

from __future__ import annotations

import math

import astropy.constants as const
import astropy.units as u
import pytest
from astropy.modeling.physical_models import BlackBody

from techno_search.infrared_wise.photosphere_excess import (
    WISE_ZERO_POINT_JY,
    wise_ir_excess_result,
    wise_vega_mag_to_flux_jy,
)


def _blackbody_wise_mags(temperature_k: float, w1_mag: float = 5.0) -> dict[str, float]:
    bb = BlackBody(temperature=temperature_k * u.K)

    def _flux_at_um(microns: float) -> float:
        nu = (const.c / (microns * u.um)).to(u.Hz)
        return float(bb(nu).value)

    w1_flux_target = WISE_ZERO_POINT_JY["w1"] * 10 ** (-w1_mag / 2.5)
    scale = w1_flux_target / _flux_at_um(3.4)

    mags = {}
    for band, microns in (("w1", 3.4), ("w2", 4.6), ("w3", 12.0), ("w4", 22.0)):
        flux = _flux_at_um(microns) * scale
        mags[band] = -2.5 * math.log10(flux / WISE_ZERO_POINT_JY[band])
    return mags


def test_zero_point_conversion_round_trips() -> None:
    flux = wise_vega_mag_to_flux_jy(0.0, "w1")
    assert flux == pytest.approx(WISE_ZERO_POINT_JY["w1"])


def test_missing_magnitudes_return_not_computable() -> None:
    result = wise_ir_excess_result(None, 5.0, 5.0, 5.0)
    assert result.computable is False
    assert result.reason is not None

    result2 = wise_ir_excess_result(5.0, 5.0, None, None)
    assert result2.computable is False


def test_pure_blackbody_photosphere_has_no_excess() -> None:
    mags = _blackbody_wise_mags(5778.0)

    result = wise_ir_excess_result(mags["w1"], mags["w2"], mags["w3"], mags["w4"])

    assert result.computable
    assert result.photosphere_temperature_k == pytest.approx(5778.0, rel=1e-6)
    assert abs(result.w3_excess_significance) < 1e-6
    assert abs(result.w4_excess_significance) < 1e-6
    assert result.ir_excess_score() == 0.0


def test_injected_w4_excess_is_detected() -> None:
    mags = _blackbody_wise_mags(5778.0)
    w4_flux = wise_vega_mag_to_flux_jy(mags["w4"], "w4")
    excess_flux = w4_flux * 5.0
    w4_mag_excess = -2.5 * math.log10(excess_flux / WISE_ZERO_POINT_JY["w4"])

    result = wise_ir_excess_result(mags["w1"], mags["w2"], mags["w3"], w4_mag_excess)

    assert result.computable
    assert result.w4_excess_significance == pytest.approx(8.0, rel=1e-6)
    assert result.w3_excess_significance is not None
    assert abs(result.w3_excess_significance) < 1e-6
    assert result.ir_excess_score() == pytest.approx(0.8, rel=1e-6)


def test_real_magnitude_uncertainty_narrows_significance() -> None:
    mags = _blackbody_wise_mags(5778.0)
    w4_flux = wise_vega_mag_to_flux_jy(mags["w4"], "w4")
    excess_flux = w4_flux * 1.2
    w4_mag_excess = -2.5 * math.log10(excess_flux / WISE_ZERO_POINT_JY["w4"])

    tight = wise_ir_excess_result(
        mags["w1"], mags["w2"], mags["w3"], w4_mag_excess, w4_mag_err=0.01
    )
    loose = wise_ir_excess_result(
        mags["w1"], mags["w2"], mags["w3"], w4_mag_excess, w4_mag_err=0.5
    )

    assert tight.w4_excess_significance > loose.w4_excess_significance


def test_recovers_a_cooler_photosphere_temperature() -> None:
    mags = _blackbody_wise_mags(3200.0)

    result = wise_ir_excess_result(mags["w1"], mags["w2"], mags["w3"], mags["w4"])

    assert result.computable
    assert result.photosphere_temperature_k == pytest.approx(3200.0, rel=1e-5)
