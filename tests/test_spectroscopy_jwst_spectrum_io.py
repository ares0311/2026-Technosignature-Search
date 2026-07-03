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
