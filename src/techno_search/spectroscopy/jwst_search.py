"""Real NASA MAST search + download for JWST MIRI LRS spectra (Phase 4).

Wraps ``astroquery.mast.Observations``' public ``query_criteria()`` /
``get_product_list()`` / ``download_products()`` API (verified via direct
``inspect``/docstring introspection of the installed package, not from
memory). This performs real live network access to NASA's MAST archive and
must be run on a machine with real MAST connectivity -- this project's
development sandbox cannot reach MAST (verified live:
``https://mast.stsci.edu`` returns a 403 through the sandbox's outbound
proxy), same restriction already documented for
``photometry/lightcurve_search.py``.

The real MAST ``instrument_name`` values for MIRI LRS observations
(``MIRI/SLIT`` and ``MIRI/SLITLESS``) and the ``filters="P750L"`` LRS
prism-disperser filter were confirmed via a real, live
``Observations.query_criteria()`` call by the user's research agent -- see
``docs/technosignature_detection_research_answers.md`` Q4 for the full query
and result counts (1526 and 742 real observations respectively). Nothing
here is guessed: any future MAST criterion not already verified in that
document must be confirmed live before being added as a default.

Downloaded products are filtered to the real ``x1d``/``x1dints`` 1D-extracted
-spectrum filename suffix used by the JWST calibration pipeline's
``extract_1d`` step (the same real, verified naming convention already used
by ``spectroscopy/jwst_spectrum_io.py``, which reads exactly these files) --
this avoids depending on an unverified MAST ``productSubGroupDescription``
column value.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

JWST_SEARCH_SCHEMA_VERSION = "spectroscopy_jwst_search_v1"
JWST_SEARCH_DISCLAIMER = (
    "A JWST MAST search/download result is provenance evidence only. It "
    "does not constitute a detection, discovery, external validation, or "
    "authorization for external submission."
)

# Real, verified MAST instrument_name values for MIRI LRS observations
# (docs/technosignature_detection_research_answers.md Q4). MIRI/LRS,
# MIRI/SLITLESSPRISM, and MIRI/LRS-FIXEDSLIT were live-tested and return
# zero results -- do not use them.
MIRI_LRS_INSTRUMENT_NAMES = ("MIRI/SLIT", "MIRI/SLITLESS")
MIRI_LRS_PRISM_FILTER = "P750L"

_X1D_SUFFIXES = ("_x1d.fits", "_x1dints.fits")


@dataclass(frozen=True)
class JwstSearchResult:
    """Real result of a NASA MAST JWST MIRI LRS spectrum search and download."""

    target: str
    result_count: int
    x1d_product_count: int
    downloaded_count: int
    downloaded_paths: tuple[str, ...]
    download_dir: str
    search_criteria: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": JWST_SEARCH_SCHEMA_VERSION,
            "disclaimer": JWST_SEARCH_DISCLAIMER,
            "target": self.target,
            "result_count": self.result_count,
            "x1d_product_count": self.x1d_product_count,
            "downloaded_count": self.downloaded_count,
            "downloaded_paths": list(self.downloaded_paths),
            "download_dir": self.download_dir,
            "search_criteria": self.search_criteria,
        }


def search_and_download_miri_lrs_spectra(
    target: str,
    *,
    download_dir: Path,
    instrument_name: tuple[str, ...] = MIRI_LRS_INSTRUMENT_NAMES,
    filters: str | None = MIRI_LRS_PRISM_FILTER,
    radius_arcsec: float | None = None,
    limit: int | None = 1,
) -> JwstSearchResult:
    """Search NASA MAST for real JWST MIRI LRS x1d spectra and download up to ``limit``.

    ``instrument_name``/``filters`` default to the real, live-verified MIRI
    LRS values recorded in
    ``docs/technosignature_detection_research_answers.md``. Pass
    ``filters=None`` to search across all MIRI LRS dispersers rather than
    just the P750L prism.

    ``limit=None`` downloads every matching x1d product -- use with care,
    since a well-observed target can return many exposures/segments.
    """

    try:
        from astroquery.mast import Observations
    except ImportError as exc:  # pragma: no cover - exercised only without extra installed
        msg = "astroquery is required. Install with: .venv/bin/python -m pip install astroquery"
        raise RuntimeError(msg) from exc

    search_criteria: dict[str, Any] = {
        "obs_collection": "JWST",
        "instrument_name": list(instrument_name),
    }
    if filters is not None:
        search_criteria["filters"] = filters
    if radius_arcsec is not None:
        search_criteria["radius"] = radius_arcsec / 3600.0

    observations = Observations.query_criteria(objectname=target, **search_criteria)
    result_count = len(observations)
    if result_count == 0:
        return JwstSearchResult(
            target=target,
            result_count=0,
            x1d_product_count=0,
            downloaded_count=0,
            downloaded_paths=(),
            download_dir=str(download_dir),
            search_criteria=search_criteria,
        )

    products = Observations.get_product_list(observations)
    product_names = [str(name) for name in products["productFilename"]]
    x1d_mask = [name.endswith(_X1D_SUFFIXES) for name in product_names]
    x1d_products = products[x1d_mask]
    x1d_product_count = len(x1d_products)

    if x1d_product_count == 0:
        return JwstSearchResult(
            target=target,
            result_count=result_count,
            x1d_product_count=0,
            downloaded_count=0,
            downloaded_paths=(),
            download_dir=str(download_dir),
            search_criteria=search_criteria,
        )

    to_download = x1d_products if limit is None else x1d_products[:limit]

    download_dir.mkdir(parents=True, exist_ok=True)
    manifest = Observations.download_products(to_download, download_dir=str(download_dir))
    downloaded_paths = tuple(sorted(str(p) for p in manifest["Local Path"]))

    return JwstSearchResult(
        target=target,
        result_count=result_count,
        x1d_product_count=x1d_product_count,
        downloaded_count=len(downloaded_paths),
        downloaded_paths=downloaded_paths,
        download_dir=str(download_dir),
        search_criteria=search_criteria,
    )
