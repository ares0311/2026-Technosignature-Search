"""Real Kepler/K2/TESS light curve loading (Phase 2: Transit Photometry).

Loads real, locally present light curve FITS files using lightkurve's public
``lightkurve.read()`` entry point, which auto-detects the Kepler/K2/TESS/
generic light curve format from the FITS header. This module never fabricates
or downloads a light curve on its own -- callers supply a real local file,
typically obtained via ``lightkurve.search_lightcurve(...).download()`` run on
a machine with real NASA MAST network access (this sandbox cannot reach
MAST; verified live, not assumed -- ``https://mast.stsci.edu`` returns a
403 through the sandbox's outbound proxy).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lightkurve import LightCurve


def load_lightcurve_file(path: Path) -> LightCurve:
    """Load a real, locally downloaded Kepler/K2/TESS light curve FITS file."""

    try:
        import lightkurve as lk
    except ImportError as exc:  # pragma: no cover - exercised only without extra installed
        msg = (
            "lightkurve is required to load light curve files. "
            "Install with: .venv/bin/python -m pip install '.[photometry]'"
        )
        raise RuntimeError(msg) from exc

    if not path.exists():
        msg = f"Light curve file not found: {path}"
        raise FileNotFoundError(msg)

    loaded = lk.read(str(path))
    if not isinstance(loaded, lk.LightCurve):
        msg = (
            f"{path} did not load as a LightCurve (got {type(loaded).__name__}). "
            "Target Pixel Files (TPFs) must be converted to a light curve "
            "(e.g. via .to_lightcurve()) before use here."
        )
        raise TypeError(msg)
    return loaded
