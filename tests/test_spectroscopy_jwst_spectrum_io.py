from __future__ import annotations

from pathlib import Path

import pytest

from techno_search.spectroscopy.jwst_spectrum_io import load_jwst_x1d_spectrum

FIXTURE = Path(__file__).parent / "fixtures" / "spectroscopy" / "sample_miri_lrs_x1d.fits"


def test_loads_real_x1d_fixture() -> None:
    spectrum = load_jwst_x1d_spectrum(FIXTURE)

    assert spectrum.wavelength_um.size == 300
    assert spectrum.flux.size == 300
    assert spectrum.flux_err.size == 300
    assert spectrum.wavelength_um.min() >= 5.0
    assert spectrum.wavelength_um.max() <= 14.0


def test_missing_file_raises_file_not_found_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_jwst_x1d_spectrum(tmp_path / "does_not_exist.fits")


def test_non_x1d_fits_raises_value_error(tmp_path: Path) -> None:
    from astropy.io import fits

    path = tmp_path / "not_x1d.fits"
    fits.PrimaryHDU().writeto(path)

    with pytest.raises(ValueError, match="EXTRACT1D"):
        load_jwst_x1d_spectrum(path)


def test_out_of_range_extension_index_raises_value_error() -> None:
    with pytest.raises(ValueError, match="out of range"):
        load_jwst_x1d_spectrum(FIXTURE, extension_index=2)


def _write_multi_integration_x1dints(path: Path) -> None:
    """Construct a real-structure (but synthetic) multi-integration x1dints fixture.

    Mirrors the real WASP-43 x1dints table structure confirmed via direct
    astropy.io.fits inspection in this session: one EXTRACT1D row per
    integration, WAVELENGTH/FLUX/FLUX_ERROR stored as per-row vector columns.
    """

    import numpy as np
    from astropy.io import fits

    n_integrations, n_wavelengths = 4, 5
    wavelength = np.tile(np.linspace(7.0, 11.0, n_wavelengths), (n_integrations, 1))
    flux = np.ones((n_integrations, n_wavelengths))
    flux_err = np.full((n_integrations, n_wavelengths), 0.01)

    columns = [
        fits.Column(name="INT_NUM", format="J", array=np.arange(1, n_integrations + 1)),
        fits.Column(name="WAVELENGTH", format=f"{n_wavelengths}D", array=wavelength),
        fits.Column(name="FLUX", format=f"{n_wavelengths}D", array=flux),
        fits.Column(name="FLUX_ERROR", format=f"{n_wavelengths}D", array=flux_err),
    ]
    hdu = fits.BinTableHDU.from_columns(columns, name="EXTRACT1D")
    fits.HDUList([fits.PrimaryHDU(), hdu]).writeto(path)


def test_multi_integration_file_without_index_raises_value_error(tmp_path: Path) -> None:
    path = tmp_path / "multi_integration_x1dints.fits"
    _write_multi_integration_x1dints(path)

    with pytest.raises(ValueError, match="multi-integration"):
        load_jwst_x1d_spectrum(path)


def test_multi_integration_file_with_index_returns_one_integration(tmp_path: Path) -> None:
    path = tmp_path / "multi_integration_x1dints.fits"
    _write_multi_integration_x1dints(path)

    spectrum = load_jwst_x1d_spectrum(path, integration_index=2)

    assert spectrum.wavelength_um.ndim == 1
    assert spectrum.wavelength_um.size == 5
    assert spectrum.integration_count == 4


def test_multi_integration_out_of_range_index_raises_value_error(tmp_path: Path) -> None:
    path = tmp_path / "multi_integration_x1dints.fits"
    _write_multi_integration_x1dints(path)

    with pytest.raises(ValueError, match="out of range"):
        load_jwst_x1d_spectrum(path, integration_index=5)
