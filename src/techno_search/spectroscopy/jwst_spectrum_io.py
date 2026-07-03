"""Real JWST x1d 1D-extracted-spectrum FITS reader (Phase 4).

The JWST calibration pipeline's ``extract_1d`` step writes spectral data to
an "x1d" (or "x1dints" for time-series) FITS product with an ``EXTRACT1D``
table extension containing ``WAVELENGTH``, ``FLUX``, ``FLUX_ERROR``, and
other columns -- this applies to all JWST spectroscopic modes, including
MIRI LRS. Verified 2026-07-03 via live web search directly against the
official JWST pipeline documentation (jwst-pipeline.readthedocs.io), not
from memory. Real ``astropy.table.Table.read(path, hdu="EXTRACT1D")``
extension-by-name reading confirmed via a live round-trip test in this
session.

Multiple ``EXTRACT1D`` extensions can exist in one file (multiple sources,
segments, spectral orders, or exposures); this reader returns the first by
default and exposes an index parameter for the others.

**Real multi-integration TSO ``x1dints`` structure, confirmed 2026-07-03
against a real downloaded MIRI LRS slitless file** (WASP-43,
jw01366011001_04103_00002-seg003_mirimage_x1dints.fits, verified via direct
``astropy.io.fits`` inspection, not memory): a time-series ``x1dints`` file
stores all integrations in a *single* ``EXTRACT1D`` table with one row per
integration (an ``INT_NUM`` column) and ``WAVELENGTH``/``FLUX``/``FLUX_ERROR``
as per-row *vector* columns (e.g. ``388D`` -- 388 wavelength points per
integration), not one row per wavelength point. Reading that column with
``np.asarray()`` yields a 2D ``(n_integrations, n_wavelengths)`` array; if
this were silently flattened into a 1D array, ``search_gas_absorption_bands``
would treat many real, correlated time-integration samples per wavelength
as independent measurements of one static spectrum -- inflating apparent
significance from real orbital-phase flux variation (physically expected
for a phase-curve target) rather than any true spectral feature. This
reader instead requires the caller to select one integration explicitly via
``integration_index`` for multi-integration files, and raises a clear error
otherwise rather than silently mis-computing a misleading result.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

_JWST_X1D_EXTENSION_NAME = "EXTRACT1D"


@dataclass(frozen=True)
class JwstSpectrum:
    """A real, extracted 1D JWST spectrum (wavelength in microns)."""

    wavelength_um: np.ndarray
    flux: np.ndarray
    flux_err: np.ndarray
    source_path: str
    integration_count: int = 1


def load_jwst_x1d_spectrum(
    path: Path,
    *,
    extension_index: int = 1,
    integration_index: int | None = None,
) -> JwstSpectrum:
    """Load a real JWST x1d/x1dints FITS product's extracted 1D spectrum.

    ``extension_index`` selects which ``EXTRACT1D`` extension to use when a
    file contains more than one (1-indexed among EXTRACT1D extensions,
    matching the order they appear in the file).

    ``integration_index`` (1-indexed) selects a single integration's
    spectrum when the ``EXTRACT1D`` table is a multi-integration time-series
    product (one row per integration, ``WAVELENGTH``/``FLUX``/``FLUX_ERROR``
    stored as per-row vector columns). This is required for such files --
    there is no default, since silently picking one or averaging across
    integrations would hide a real choice about which orbital phase (or
    what kind of time-averaging) the resulting "spectrum" represents. A
    single flat-column (non-time-series) ``x1d`` file ignores this
    parameter.
    """

    from astropy.io import fits
    from astropy.table import Table

    if not path.exists():
        msg = f"JWST spectrum file not found: {path}"
        raise FileNotFoundError(msg)

    with fits.open(path) as hdul:
        extract1d_indices = [
            index
            for index, hdu in enumerate(hdul)
            if str(hdu.name).upper() == _JWST_X1D_EXTENSION_NAME
        ]
    if not extract1d_indices:
        msg = f"{path} has no {_JWST_X1D_EXTENSION_NAME} extension; not a JWST x1d product."
        raise ValueError(msg)
    if extension_index < 1 or extension_index > len(extract1d_indices):
        msg = (
            f"extension_index={extension_index} out of range; "
            f"{path} has {len(extract1d_indices)} {_JWST_X1D_EXTENSION_NAME} extension(s)."
        )
        raise ValueError(msg)

    hdu_index = extract1d_indices[extension_index - 1]
    table = Table.read(path, hdu=hdu_index)

    missing = [col for col in ("WAVELENGTH", "FLUX", "FLUX_ERROR") if col not in table.colnames]
    if missing:
        msg = f"{path} EXTRACT1D table is missing required column(s): {missing}"
        raise ValueError(msg)

    wavelength_col = np.asarray(table["WAVELENGTH"], dtype=float)
    flux_col = np.asarray(table["FLUX"], dtype=float)
    flux_err_col = np.asarray(table["FLUX_ERROR"], dtype=float)

    if wavelength_col.ndim == 2:
        integration_count = wavelength_col.shape[0]
        if integration_index is None:
            msg = (
                f"{path}'s EXTRACT1D table is a multi-integration time-series "
                f"product ({integration_count} integrations per row, "
                f"{wavelength_col.shape[1]} wavelength points each), not a "
                "single static spectrum. Pooling all integrations together "
                "would treat real, correlated time-domain flux variation "
                "(e.g. an orbital phase curve or transit/eclipse) as if it "
                "were independent per-wavelength noise, which can produce a "
                "spuriously significant band result. Pass integration_index "
                "(1-indexed) to select one specific integration's spectrum."
            )
            raise ValueError(msg)
        if integration_index < 1 or integration_index > integration_count:
            msg = (
                f"integration_index={integration_index} out of range; "
                f"{path} has {integration_count} integrations."
            )
            raise ValueError(msg)
        row = integration_index - 1
        return JwstSpectrum(
            wavelength_um=wavelength_col[row],
            flux=flux_col[row],
            flux_err=flux_err_col[row],
            source_path=str(path),
            integration_count=integration_count,
        )

    return JwstSpectrum(
        wavelength_um=wavelength_col,
        flux=flux_col,
        flux_err=flux_err_col,
        source_path=str(path),
        integration_count=1,
    )
