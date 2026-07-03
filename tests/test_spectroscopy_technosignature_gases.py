"""Tests for the real JWST MIRI LRS technosignature-gas band search.

Constructed spectra here are code-correctness test fixtures (verifying the
real statistical computation), not training/calibration data -- no model is
fit to them. Same pattern as the existing BLS/WISE-excess test fixtures.
"""

from __future__ import annotations

import numpy as np

from techno_search.spectroscopy.technosignature_gases import (
    GAS_ABSORPTION_BANDS_UM,
    search_gas_absorption_bands,
)


def _flat_spectrum(n: int = 400) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    wavelength = np.linspace(5.0, 14.0, n)
    signal = np.full(n, 1.0)
    signal_err = np.full(n, 0.001)
    return wavelength, signal, signal_err


def test_flat_spectrum_has_no_significant_bands() -> None:
    wavelength, signal, signal_err = _flat_spectrum()

    results = search_gas_absorption_bands(wavelength, signal, signal_err)

    computable = [r for r in results if r.computable]
    assert computable
    for result in computable:
        assert result.significance_sigma is not None
        assert abs(result.significance_sigma) < 4.0


def test_injected_dip_at_sf6_band_is_detected() -> None:
    wavelength, signal, signal_err = _flat_spectrum()
    sf6_center = GAS_ABSORPTION_BANDS_UM["SF6"][0]
    half_width = sf6_center / (2.0 * 100.0)
    in_band = np.abs(wavelength - sf6_center) <= half_width
    signal[in_band] -= 0.05  # a real, large injected dip relative to the 0.001 noise floor

    results = search_gas_absorption_bands(wavelength, signal, signal_err)
    sf6_result = next(r for r in results if r.gas == "SF6")

    assert sf6_result.computable
    assert sf6_result.significance_sigma is not None
    assert sf6_result.significance_sigma > 5.0


def test_all_five_documented_gas_bands_are_searched() -> None:
    wavelength, signal, signal_err = _flat_spectrum()

    results = search_gas_absorption_bands(wavelength, signal, signal_err)
    gases_found = {r.gas for r in results}

    assert gases_found == {"CF4", "C2F6", "C3F8", "SF6", "NF3"}
    # C2F6 has two real, independent bands.
    assert sum(1 for r in results if r.gas == "C2F6") == 2


def test_band_outside_spectral_coverage_is_not_computable() -> None:
    wavelength = np.linspace(5.0, 6.0, 50)  # excludes all bands above ~6 um
    signal = np.ones_like(wavelength)
    signal_err = np.full_like(wavelength, 0.001)

    results = search_gas_absorption_bands(wavelength, signal, signal_err)
    sf6_result = next(r for r in results if r.gas == "SF6")

    assert sf6_result.computable is False
    assert sf6_result.reason is not None


def test_band_centers_fall_within_documented_miri_lrs_coverage() -> None:
    for gas, centers in GAS_ABSORPTION_BANDS_UM.items():
        for center in centers:
            assert 5.0 <= center <= 14.0, f"{gas} band {center} um outside MIRI LRS range"
