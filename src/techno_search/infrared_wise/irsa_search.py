"""Real IRSA AllWISE photometry search + download (Phase 3: WISE Dyson Sphere Candidates).

Wraps ``astroquery.ipac.irsa.Irsa``'s public ``query_region()`` API against
the real AllWISE Source Catalog (``allwise_p3as_psd`` -- the real IRSA TAP
table name for AllWISE, verified via the official astroquery IRSA
documentation, 2026-07-04) and ``astropy.coordinates.SkyCoord.from_name()``
for real target-name resolution. This performs real live network access to
NASA/IPAC's IRSA archive and must be run on a machine with real IRSA
connectivity -- this project's development sandbox cannot reach IRSA
(same live-network restriction already documented for MAST-based tracks).

Unlike Phase 2/4 (which download FITS files), this writes a real CSV in
the same column-name convention ``infrared/catalog_reader.py`` already
parses (``ra``/``dec``/``w1mpro``/``w2mpro``/``w3mpro``/``w4mpro``/
``w3sigmpro``/``w4sigmpro``, the real AllWISE Explanatory Supplement
column names already used elsewhere in this project) -- no new parser is
needed, and no assumption is made about column names beyond what
``catalog_reader.py`` already verifies.

This queries the AllWISE catalog alone, not a pre-joined Gaia+AllWISE
cross-match -- Gaia source_id/G-mag/parallax fields are optional inputs to
the downstream infrared candidate builder and are left absent when not
separately supplied.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

IRSA_SEARCH_SCHEMA_VERSION = "infrared_wise_irsa_search_v1"
IRSA_SEARCH_DISCLAIMER = (
    "A real IRSA AllWISE photometry search/download result is provenance "
    "evidence only. It does not constitute a detection, discovery, external "
    "validation, or authorization for external submission."
)
ALLWISE_SOURCE_CATALOG = "allwise_p3as_psd"


@dataclass(frozen=True)
class IrsaSearchResult:
    """Real result of an IRSA AllWISE photometry search and CSV write."""

    target: str
    result_count: int
    csv_path: str | None
    search_criteria: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": IRSA_SEARCH_SCHEMA_VERSION,
            "disclaimer": IRSA_SEARCH_DISCLAIMER,
            "target": self.target,
            "result_count": self.result_count,
            "csv_path": self.csv_path,
            "search_criteria": self.search_criteria,
        }


def search_and_download_wise_photometry(
    target: str,
    *,
    download_dir: Path,
    radius_arcsec: float = 5.0,
    catalog: str = ALLWISE_SOURCE_CATALOG,
) -> IrsaSearchResult:
    """Resolve ``target`` to real coordinates and query the real AllWISE catalog around it.

    Writes a real CSV file (IRSA's own column names preserved verbatim) to
    ``download_dir/<target>_allwise.csv`` when at least one row is
    returned; leaves ``csv_path`` as ``None`` on a zero-result search.
    """

    try:
        from astropy import units as u
        from astropy.coordinates import SkyCoord
        from astroquery.ipac.irsa import Irsa
    except ImportError as exc:  # pragma: no cover - exercised only without extra installed
        msg = (
            "astroquery and astropy are required. Install with: "
            ".venv/bin/python -m pip install astroquery astropy"
        )
        raise RuntimeError(msg) from exc

    search_criteria: dict[str, Any] = {
        "catalog": catalog,
        "spatial": "Cone",
        "radius_arcsec": radius_arcsec,
    }

    try:
        coord = SkyCoord.from_name(target)
    except Exception as exc:  # noqa: BLE001 - real resolver failures vary by backend
        msg = f"Could not resolve {target!r} to a sky position: {exc}"
        raise RuntimeError(msg) from exc

    table = Irsa.query_region(
        coord, catalog=catalog, spatial="Cone", radius=radius_arcsec * u.arcsec
    )
    result_count = len(table)
    if result_count == 0:
        return IrsaSearchResult(
            target=target,
            result_count=0,
            csv_path=None,
            search_criteria=search_criteria,
        )

    download_dir.mkdir(parents=True, exist_ok=True)
    safe_target = target.replace(" ", "_").replace("/", "_")
    csv_path = download_dir / f"{safe_target}_allwise.csv"

    fieldnames = list(table.colnames)
    with csv_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(fieldnames)
        for row in table:
            writer.writerow([row[name] for name in fieldnames])

    return IrsaSearchResult(
        target=target,
        result_count=result_count,
        csv_path=str(csv_path),
        search_criteria=search_criteria,
    )
