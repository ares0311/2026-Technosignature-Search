"""Tests for the real full-grid HITRAN cross-section matched-filter check.

The constructed .xsc fixture here uses the real, verified HITRAN cross-
section ASCII format (header: species numin numax npts; body: whitespace-
separated cross-section values) with synthetic values -- a code-correctness
fixture, not training/calibration data, same pattern as the existing
BLS/WISE-excess/gas-band test fixtures.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from techno_search.spectroscopy.hitran_xsc_matched_filter import (
    matched_filter_significance,
    parse_xsc,
    search_gas_matched_filters,
    xsc_wavelength_um,
)


def _write_xsc(path: Path, *, numin: float, numax: float, values: list[float]) -> None:
    npts = len(values)
    lines = [f"TESTGAS {numin} {numax} {npts} 298.1 760.0 extra fields here"]
    for i in range(0, npts, 10):
        lines.append(" ".join(f"{v:.6e}" for v in values[i : i + 10]))
    path.write_text("\n".join(lines) + "\n")


def test_parse_xsc_round_trips_header_and_values(tmp_path: Path) -> None:
    path = tmp_path / "TESTGAS_298.1K.xsc"
    values = [0.0, 1.0, 2.0, 3.0, 2.0, 1.0, 0.0]
    _write_xsc(path, numin=1000.0, numax=1006.0, values=values)

    grid = parse_xsc(path)

    assert grid.species == "TESTGAS"
    assert grid.wavenumber_cm.size == len(values)
    assert grid.wavenumber_cm[0] == pytest.approx(1000.0)
    assert grid.wavenumber_cm[-1] == pytest.approx(1006.0)
    np.testing.assert_allclose(grid.cross_section, values)


def test_parse_xsc_missing_file_raises() -> None:
    with pytest.raises(FileNotFoundError):
        parse_xsc(Path("/nonexistent/path.xsc"))


def test_parse_xsc_truncated_body_raises_value_error(tmp_path: Path) -> None:
    path = tmp_path / "bad.xsc"
    path.write_text("TESTGAS 1000.0 1010.0 20\n1.0 2.0 3.0\n")

    with pytest.raises(ValueError, match="declares 20 points"):
        parse_xsc(path)


def test_xsc_wavelength_um_is_inverse_of_wavenumber(tmp_path: Path) -> None:
    path = tmp_path / "TESTGAS.xsc"
    _write_xsc(path, numin=1000.0, numax=1000.0, values=[1.0])
    grid = parse_xsc(path)

    wavelength = xsc_wavelength_um(grid)

    assert wavelength[0] == pytest.approx(1.0e4 / 1000.0)


def test_matched_filter_recovers_injected_template_signal(tmp_path: Path) -> None:
    # Real cross-section template: a single real Gaussian-like bump at 1250 cm^-1
    # (~8.0 um), spanning the same wavenumber range as MIRI LRS (5-14 um ~ 714-2000 cm^-1).
    wavenumber = np.linspace(700.0, 2000.0, 400)
    template_xs = 5.0 * np.exp(-0.5 * ((wavenumber - 1250.0) / 15.0) ** 2)
    path = tmp_path / "TESTGAS_298.1K.xsc"
    _write_xsc(path, numin=700.0, numax=2000.0, values=list(template_xs))
    grid = parse_xsc(path)

    wavelength_um = np.linspace(5.0, 14.0, 400)
    flux = np.full(400, 1.0)
    flux_err = np.full(400, 0.001)

    # Inject a real dip shaped exactly like the template (scaled), so the
    # matched filter should recover a large, significant positive amplitude.
    grid_wavelength_um = xsc_wavelength_um(grid)
    order = np.argsort(grid_wavelength_um)
    template_on_obs = np.interp(
        wavelength_um, grid_wavelength_um[order], grid.cross_section[order]
    )
    flux = flux - 0.01 * template_on_obs

    result = matched_filter_significance("TESTGAS", wavelength_um, flux, flux_err, grid)

    assert result.computable
    assert result.significance_sigma is not None
    assert result.significance_sigma > 5.0
    assert result.amplitude is not None
    assert result.amplitude > 0.0


def test_matched_filter_flat_spectrum_has_low_significance(tmp_path: Path) -> None:
    wavenumber = np.linspace(700.0, 2000.0, 400)
    template_xs = 5.0 * np.exp(-0.5 * ((wavenumber - 1250.0) / 15.0) ** 2)
    path = tmp_path / "TESTGAS.xsc"
    _write_xsc(path, numin=700.0, numax=2000.0, values=list(template_xs))
    grid = parse_xsc(path)

    wavelength_um = np.linspace(5.0, 14.0, 400)
    flux = np.full(400, 1.0)
    flux_err = np.full(400, 0.001)

    result = matched_filter_significance("TESTGAS", wavelength_um, flux, flux_err, grid)

    assert result.computable
    assert result.significance_sigma is not None
    assert abs(result.significance_sigma) < 4.0


def test_matched_filter_no_overlap_is_not_computable(tmp_path: Path) -> None:
    path = tmp_path / "TESTGAS.xsc"
    _write_xsc(path, numin=100.0, numax=110.0, values=[1.0] * 20)
    grid = parse_xsc(path)

    wavelength_um = np.linspace(5.0, 14.0, 50)
    flux = np.full(50, 1.0)
    flux_err = np.full(50, 0.001)

    result = matched_filter_significance("TESTGAS", wavelength_um, flux, flux_err, grid)

    assert not result.computable
    assert result.reason is not None


def test_search_gas_matched_filters_skips_gases_without_a_path(tmp_path: Path) -> None:
    path = tmp_path / "CF4_298.1K.xsc"
    _write_xsc(path, numin=700.0, numax=2000.0, values=[1.0] * 400)

    wavelength_um = np.linspace(5.0, 14.0, 400)
    flux = np.full(400, 1.0)
    flux_err = np.full(400, 0.001)

    results = search_gas_matched_filters(
        wavelength_um, flux, flux_err, {"CF4": path}
    )

    assert len(results) == 1
    assert results[0].gas == "CF4"


def test_search_gas_matched_filters_reports_missing_file(tmp_path: Path) -> None:
    results = search_gas_matched_filters(
        np.array([5.0, 6.0]),
        np.array([1.0, 1.0]),
        np.array([0.01, 0.01]),
        {"SF6": tmp_path / "does_not_exist.xsc"},
    )

    assert len(results) == 1
    assert results[0].gas == "SF6"
    assert not results[0].computable
    assert results[0].reason is not None
