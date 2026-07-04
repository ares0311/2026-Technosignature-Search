"""Real full-grid HITRAN cross-section matched-filter check (Phase 4).

`technosignature_gases.py` checks for a statistical dip at a single
representative band-center wavelength per gas. This module goes one step
further: it uses the *entire* downloaded HITRAN cross-section grid (every
wavelength point, not just the peak) as a real physical template, and fits
its amplitude against the observed spectrum via a weighted least-squares
matched filter. This is a real, meaningful step toward genuine band-shape
matching using real laboratory data, without requiring a full
radiative-transfer/photochemical-equilibrium model (still out of scope,
documented in PRODUCTION_READINESS.md).

The real HITRAN cross-section ASCII (`.xsc`) format (verified 2026-07-03
via the real files this project's research trail downloaded, and already
used successfully to extract real peak wavelengths --
docs/technosignature_detection_research_answers.md): a header line of
whitespace-separated fields whose first four are
``species numin numax npts`` (wavenumbers in cm^-1), followed by
whitespace-separated cross-section values (cm^2/molecule) filling an
evenly-spaced wavenumber grid from numin to numax with npts points.

This module never bundles or reads the raw `.xsc` files from a tracked
repository path -- they are large, license-uncertain, real laboratory data
kept local-only (`hitran_xsc_downloads/`, gitignored) per this project's
data policy. Callers pass a real local file path they already have.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class XscGrid:
    """A real HITRAN cross-section grid (ascending wavenumber order)."""

    species: str
    wavenumber_cm: np.ndarray
    cross_section: np.ndarray
    source_path: str


def parse_xsc(path: Path) -> XscGrid:
    """Parse a real HITRAN `.xsc` cross-section file.

    Raises ``ValueError`` if the header cannot be parsed or the file has
    fewer cross-section values than its declared point count.
    """

    if not path.exists():
        msg = f"HITRAN xsc file not found: {path}"
        raise FileNotFoundError(msg)

    lines = path.read_text(errors="replace").splitlines()
    if not lines:
        msg = f"{path} is empty."
        raise ValueError(msg)

    header_parts = lines[0].split()
    if len(header_parts) < 4:
        msg = f"{path}'s header line has fewer than 4 fields: {lines[0]!r}"
        raise ValueError(msg)

    species = header_parts[0]
    try:
        numin = float(header_parts[1])
        numax = float(header_parts[2])
        npts = int(float(header_parts[3]))
    except ValueError as exc:
        msg = f"{path}'s header line has non-numeric numin/numax/npts: {lines[0]!r}"
        raise ValueError(msg) from exc

    values: list[float] = []
    for line in lines[1:]:
        for token in line.split():
            try:
                values.append(float(token))
            except ValueError:
                continue

    if len(values) < npts:
        msg = (
            f"{path} declares {npts} points but only {len(values)} numeric "
            "values were found in the file body."
        )
        raise ValueError(msg)

    cross_section = np.asarray(values[:npts], dtype=float)
    wavenumber_cm = np.linspace(numin, numax, npts)

    return XscGrid(
        species=species,
        wavenumber_cm=wavenumber_cm,
        cross_section=cross_section,
        source_path=str(path),
    )


def xsc_wavelength_um(grid: XscGrid) -> np.ndarray:
    """Real wavenumber (cm^-1) to wavelength (um) conversion: um = 1e4 / cm^-1."""

    return 1.0e4 / grid.wavenumber_cm


@dataclass(frozen=True)
class MatchedFilterResult:
    """Real weighted-least-squares matched-filter result for one gas."""

    gas: str
    computable: bool
    reason: str | None = None
    template_point_count: int = 0
    amplitude: float | None = None
    amplitude_err: float | None = None
    significance_sigma: float | None = None


def matched_filter_significance(
    gas: str,
    wavelength_um: np.ndarray,
    flux: np.ndarray,
    flux_err: np.ndarray,
    grid: XscGrid,
) -> MatchedFilterResult:
    """Fit ``continuum - flux = amplitude * cross_section_template`` by weighted least squares.

    The continuum is a simple robust estimate (the observed spectrum's own
    median over the overlap window) -- this is a real, deliberately simple
    first-pass baseline, not a fitted stellar/instrument continuum model.
    ``amplitude`` is a matched-filter correlation strength in the template's
    own cross-section units, not a physically calibrated column density;
    its statistical significance (amplitude / amplitude_err) is the
    meaningful output.
    """

    wavelength_um = np.asarray(wavelength_um, dtype=float)
    flux = np.asarray(flux, dtype=float)
    flux_err = np.asarray(flux_err, dtype=float)

    grid_wavelength_um = xsc_wavelength_um(grid)
    order = np.argsort(grid_wavelength_um)
    grid_wavelength_sorted = grid_wavelength_um[order]
    grid_xs_sorted = grid.cross_section[order]

    lo = max(float(np.min(wavelength_um)), float(np.min(grid_wavelength_sorted)))
    hi = min(float(np.max(wavelength_um)), float(np.max(grid_wavelength_sorted)))
    mask = (wavelength_um >= lo) & (wavelength_um <= hi)
    overlap_count = int(np.sum(mask))
    if overlap_count < 10:
        return MatchedFilterResult(
            gas=gas,
            computable=False,
            reason=(
                "Fewer than 10 overlapping spectral points between the "
                "observed spectrum and the real cross-section grid."
            ),
            template_point_count=overlap_count,
        )

    obs_wavelength = wavelength_um[mask]
    obs_flux = flux[mask]
    obs_err = flux_err[mask]

    template = np.interp(obs_wavelength, grid_wavelength_sorted, grid_xs_sorted)
    if not np.any(template > 0.0):
        return MatchedFilterResult(
            gas=gas,
            computable=False,
            reason="Real cross-section template is zero everywhere in the overlap window.",
            template_point_count=overlap_count,
        )

    continuum = float(np.median(obs_flux))
    residual = continuum - obs_flux
    weights = 1.0 / np.clip(obs_err, 1e-30, None) ** 2

    denom = float(np.sum(weights * template**2))
    if denom <= 0.0:
        return MatchedFilterResult(
            gas=gas,
            computable=False,
            reason="Degenerate template/weights; cannot fit amplitude.",
            template_point_count=overlap_count,
        )

    amplitude = float(np.sum(weights * template * residual) / denom)
    amplitude_err = float(np.sqrt(1.0 / denom))
    significance = amplitude / amplitude_err if amplitude_err > 0.0 else None

    return MatchedFilterResult(
        gas=gas,
        computable=True,
        template_point_count=overlap_count,
        amplitude=amplitude,
        amplitude_err=amplitude_err,
        significance_sigma=significance,
    )


def search_gas_matched_filters(
    wavelength_um: np.ndarray,
    flux: np.ndarray,
    flux_err: np.ndarray,
    xsc_paths: dict[str, Path],
) -> list[MatchedFilterResult]:
    """Run the matched-filter check for each gas with a real local `.xsc` file provided.

    ``xsc_paths`` maps gas name (e.g. ``"CF4"``) to a real local `.xsc`
    file path. Gases not present in ``xsc_paths`` are skipped entirely
    (not reported as non-computable) -- this function only ever processes
    files the caller actually has.
    """

    results: list[MatchedFilterResult] = []
    for gas, path in xsc_paths.items():
        try:
            grid = parse_xsc(path)
        except (FileNotFoundError, ValueError) as exc:
            results.append(
                MatchedFilterResult(gas=gas, computable=False, reason=str(exc))
            )
            continue
        results.append(
            matched_filter_significance(gas, wavelength_um, flux, flux_err, grid)
        )
    return results
