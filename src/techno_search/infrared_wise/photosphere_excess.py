"""Real WISE photospheric blackbody excess check (Phase 3: Infrared).

Estimates a star's photospheric continuum temperature from its real WISE
W1/W2 colors (treating each band as a monochromatic flux measurement at its
WISE effective wavelength -- a standard first-pass simplification, not full
relative-spectral-response bandpass integration), predicts the photosphere's
expected W3/W4 flux from that temperature, and reports how many
sigma the observed W3/W4 flux departs from that prediction.

This is a real, physically grounded (Planck's law via
``astropy.modeling.physical_models.BlackBody``) but deliberately simple
photospheric model -- it is NOT a full Kurucz/BT-Settl stellar-atmosphere
grid fit (`docs/PRODUCTION_READINESS.md` Phase 3's eventual target), which
would require downloading external model grids. A single-temperature
blackbody is the same first-pass approximation widely used in the IR-excess
literature (e.g. Wright et al. 2014) before deeper SED follow-up.

WISE zero-point flux densities and effective wavelengths are the Wright et
al. (2010) WISE mission-paper values, cross-verified 2026-07-02 via live web
search against the WISE explanatory supplement and multiple independent
citing papers, not from memory:
    W1 (3.4 um): 309.54 Jy   W2 (4.6 um): 171.79 Jy
    W3 (12 um):  31.676 Jy   W4 (22 um):  8.3635 Jy
"""

from __future__ import annotations

from dataclasses import dataclass

import astropy.constants as const
import astropy.units as u
import numpy as np
from astropy.modeling.physical_models import BlackBody
from scipy.optimize import brentq

WISE_ZERO_POINT_JY: dict[str, float] = {
    "w1": 309.54,
    "w2": 171.79,
    "w3": 31.676,
    "w4": 8.3635,
}
WISE_EFFECTIVE_WAVELENGTH_UM: dict[str, float] = {
    "w1": 3.4,
    "w2": 4.6,
    "w3": 12.0,
    "w4": 22.0,
}
_MIN_TEMPERATURE_K = 200.0
_MAX_TEMPERATURE_K = 60000.0
_DEFAULT_RELATIVE_FLUX_UNCERTAINTY = 0.10
_EXCESS_SIGNIFICANCE_SCORE_DIVISOR = 10.0


@dataclass(frozen=True)
class WiseExcessResult:
    """Real WISE photospheric excess check result."""

    computable: bool
    reason: str | None = None
    photosphere_temperature_k: float | None = None
    w3_predicted_flux_jy: float | None = None
    w3_observed_flux_jy: float | None = None
    w3_excess_significance: float | None = None
    w4_predicted_flux_jy: float | None = None
    w4_observed_flux_jy: float | None = None
    w4_excess_significance: float | None = None

    def max_excess_significance(self) -> float:
        candidates = [
            value
            for value in (self.w3_excess_significance, self.w4_excess_significance)
            if value is not None
        ]
        return max(candidates) if candidates else 0.0

    def ir_excess_score(self) -> float:
        return _clamp(self.max_excess_significance() / _EXCESS_SIGNIFICANCE_SCORE_DIVISOR)


def wise_vega_mag_to_flux_jy(mag: float | None, band: str) -> float | None:
    """Convert a WISE Vega-system magnitude to a flux density in Jy."""
    if mag is None:
        return None
    return _mag_to_flux_jy(mag, band)


def _mag_to_flux_jy(mag: float, band: str) -> float:
    zero_point = WISE_ZERO_POINT_JY[band]
    return float(zero_point * 10.0 ** (-mag / 2.5))


def wise_ir_excess_result(
    w1_mag: float | None,
    w2_mag: float | None,
    w3_mag: float | None,
    w4_mag: float | None,
    *,
    w3_mag_err: float | None = None,
    w4_mag_err: float | None = None,
) -> WiseExcessResult:
    """Check real WISE W3/W4 flux against the photosphere predicted from W1/W2."""

    if w1_mag is None or w2_mag is None:
        return WiseExcessResult(
            computable=False,
            reason="W1 and W2 magnitudes are both required to estimate photosphere temperature.",
        )
    if w3_mag is None and w4_mag is None:
        return WiseExcessResult(
            computable=False,
            reason="At least one of W3 or W4 magnitude is required to check for excess.",
        )

    w1_flux = _mag_to_flux_jy(w1_mag, "w1")
    w2_flux = _mag_to_flux_jy(w2_mag, "w2")

    temperature_k = _estimate_photosphere_temperature_k(w1_flux, w2_flux)
    if temperature_k is None:
        return WiseExcessResult(
            computable=False,
            reason=(
                "W1/W2 color implies a photosphere temperature outside the "
                f"supported range [{_MIN_TEMPERATURE_K}, {_MAX_TEMPERATURE_K}] K."
            ),
        )

    w3_predicted = _predict_flux_jy(temperature_k, w1_flux, "w1", "w3")
    w4_predicted = _predict_flux_jy(temperature_k, w1_flux, "w1", "w4")

    w3_observed = wise_vega_mag_to_flux_jy(w3_mag, "w3")
    w4_observed = wise_vega_mag_to_flux_jy(w4_mag, "w4")

    w3_significance = None
    if w3_observed is not None:
        w3_significance = _excess_significance(w3_observed, w3_predicted, w3_mag_err)
    w4_significance = None
    if w4_observed is not None:
        w4_significance = _excess_significance(w4_observed, w4_predicted, w4_mag_err)

    return WiseExcessResult(
        computable=True,
        photosphere_temperature_k=temperature_k,
        w3_predicted_flux_jy=w3_predicted,
        w3_observed_flux_jy=w3_observed,
        w3_excess_significance=w3_significance,
        w4_predicted_flux_jy=w4_predicted,
        w4_observed_flux_jy=w4_observed,
        w4_excess_significance=w4_significance,
    )


def _planck_ratio(temperature_k: float, band_a: str, band_b: str) -> float:
    bb = BlackBody(temperature=temperature_k * u.K)
    nu_a = (const.c / (WISE_EFFECTIVE_WAVELENGTH_UM[band_a] * u.um)).to(u.Hz)
    nu_b = (const.c / (WISE_EFFECTIVE_WAVELENGTH_UM[band_b] * u.um)).to(u.Hz)
    return float((bb(nu_a) / bb(nu_b)).value)


def _estimate_photosphere_temperature_k(w1_flux_jy: float, w2_flux_jy: float) -> float | None:
    observed_ratio = w1_flux_jy / w2_flux_jy

    def _residual(temperature_k: float) -> float:
        return _planck_ratio(temperature_k, "w1", "w2") - observed_ratio

    low, high = _residual(_MIN_TEMPERATURE_K), _residual(_MAX_TEMPERATURE_K)
    if np.sign(low) == np.sign(high):
        return None
    return float(brentq(_residual, _MIN_TEMPERATURE_K, _MAX_TEMPERATURE_K))


def _predict_flux_jy(
    temperature_k: float, anchor_flux_jy: float, anchor_band: str, target_band: str
) -> float:
    ratio = _planck_ratio(temperature_k, target_band, anchor_band)
    return anchor_flux_jy * ratio


def _excess_significance(
    observed_flux_jy: float,
    predicted_flux_jy: float,
    mag_err: float | None,
) -> float:
    if mag_err is not None and mag_err > 0.0:
        relative_uncertainty = mag_err * np.log(10.0) / 2.5
    else:
        relative_uncertainty = _DEFAULT_RELATIVE_FLUX_UNCERTAINTY
    flux_uncertainty_jy = observed_flux_jy * relative_uncertainty
    if flux_uncertainty_jy <= 0.0:
        return 0.0
    return float((observed_flux_jy - predicted_flux_jy) / flux_uncertainty_jy)


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))
