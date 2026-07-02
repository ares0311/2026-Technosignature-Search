"""Real NASA MAST light curve search + download (Phase 2: Transit Photometry).

Wraps lightkurve's public ``search_lightcurve()`` / ``SearchResult.download_all()``
API (verified via direct ``inspect`` introspection of the installed package,
not from memory). This performs real live network access to NASA's MAST
archive and must be run on a machine with real MAST connectivity -- this
project's development sandbox cannot reach MAST (verified live:
``https://mast.stsci.edu`` returns a 403 through the sandbox's outbound
proxy).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

LIGHTCURVE_SEARCH_SCHEMA_VERSION = "photometry_lightcurve_search_v1"
LIGHTCURVE_SEARCH_DISCLAIMER = (
    "A light curve search/download result is provenance evidence only. It "
    "does not constitute a detection, discovery, external validation, or "
    "authorization for external submission."
)


@dataclass(frozen=True)
class LightcurveSearchResult:
    """Real result of a NASA MAST light curve search and download."""

    target: str
    result_count: int
    downloaded_count: int
    downloaded_paths: tuple[str, ...]
    download_dir: str
    search_criteria: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": LIGHTCURVE_SEARCH_SCHEMA_VERSION,
            "disclaimer": LIGHTCURVE_SEARCH_DISCLAIMER,
            "target": self.target,
            "result_count": self.result_count,
            "downloaded_count": self.downloaded_count,
            "downloaded_paths": list(self.downloaded_paths),
            "download_dir": self.download_dir,
            "search_criteria": self.search_criteria,
        }


def search_and_download_lightcurves(
    target: str,
    *,
    download_dir: Path,
    mission: tuple[str, ...] | None = None,
    author: str | None = None,
    sector: int | None = None,
    quarter: int | None = None,
    campaign: int | None = None,
    exptime: float | None = None,
    limit: int | None = 1,
) -> LightcurveSearchResult:
    """Search NASA MAST for real light curves and download up to ``limit``.

    ``limit=None`` downloads every search result -- use with care, since a
    popular target can return hundreds of sector/quarter light curves.
    """

    try:
        import lightkurve as lk
    except ImportError as exc:  # pragma: no cover - exercised only without extra installed
        msg = (
            "lightkurve is required. Install with: "
            ".venv/bin/python -m pip install '.[photometry]'"
        )
        raise RuntimeError(msg) from exc

    search_criteria: dict[str, Any] = {}
    if mission is not None:
        search_criteria["mission"] = mission
    if author is not None:
        search_criteria["author"] = author
    if sector is not None:
        search_criteria["sector"] = sector
    if quarter is not None:
        search_criteria["quarter"] = quarter
    if campaign is not None:
        search_criteria["campaign"] = campaign
    if exptime is not None:
        search_criteria["exptime"] = exptime

    search_result = lk.search_lightcurve(target, **search_criteria)
    result_count = len(search_result)
    if result_count == 0:
        return LightcurveSearchResult(
            target=target,
            result_count=0,
            downloaded_count=0,
            downloaded_paths=(),
            download_dir=str(download_dir),
            search_criteria=search_criteria,
        )

    to_download = search_result if limit is None else search_result[:limit]

    download_dir.mkdir(parents=True, exist_ok=True)
    before = set(download_dir.rglob("*.fits"))
    to_download.download_all(download_dir=str(download_dir))
    after = set(download_dir.rglob("*.fits"))
    new_paths = tuple(sorted(str(p) for p in (after - before)))

    return LightcurveSearchResult(
        target=target,
        result_count=result_count,
        downloaded_count=len(new_paths),
        downloaded_paths=new_paths,
        download_dir=str(download_dir),
        search_criteria=search_criteria,
    )
