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


def load_jwst_x1d_spectrum(path: Path, *, extension_index: int = 1) -> JwstSpectrum:
    """Load a real JWST x1d/x1dints FITS product's extracted 1D spectrum.

    ``extension_index`` selects which ``EXTRACT1D`` extension to use when a
    file contains more than one (1-indexed among EXTRACT1D extensions,
    matching the order they appear in the file).
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

    return JwstSpectrum(
        wavelength_um=np.asarray(table["WAVELENGTH"], dtype=float),
        flux=np.asarray(table["FLUX"], dtype=float),
        flux_err=np.asarray(table["FLUX_ERROR"], dtype=float),
        source_path=str(path),
    )
