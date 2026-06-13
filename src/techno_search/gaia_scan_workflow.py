"""Gaia DR3 infrared anomaly scan workflow.

Queries Gaia DR3 for a list of target coordinates using the live TAP client
(requires TECHNO_SEARCH_ENABLE_LIVE_DATA=1) and scores each source through
the infrared track.  Results are local scheduling aids only.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

GAIA_SCAN_DISCLAIMER = (
    "Gaia DR3 scan results are local scheduling aids only. "
    "No result constitutes a detection claim or authorizes external submission. "
    "All catalog queries require TECHNO_SEARCH_ENABLE_LIVE_DATA=1."
)

GAIA_SCAN_SCHEMA_VERSION = "gaia_scan_workflow_v1"

_LIVE_DATA_ENV = "TECHNO_SEARCH_ENABLE_LIVE_DATA"


@dataclass
class GaiaScanTarget:
    """A sky position to query in Gaia DR3."""

    name: str
    ra_deg: float
    dec_deg: float
    radius_arcsec: float = 30.0


def _live_data_enabled() -> bool:
    return os.environ.get(_LIVE_DATA_ENV, "0").strip() == "1"


def query_gaia_for_targets(
    targets: list[GaiaScanTarget],
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Query Gaia DR3 for each target and return normalised source lists.

    Requires TECHNO_SEARCH_ENABLE_LIVE_DATA=1.  When live data is disabled,
    returns a summary with ``live_data_disabled: true`` and no query results.

    Args:
        targets: List of sky positions to query.
        output_dir: Optional directory to write per-target JSON results.

    Returns:
        Summary dict with per-target source counts and disclaimer.
    """
    if not _live_data_enabled():
        return {
            "live_data_disabled": True,
            "targets_queried": 0,
            "total_sources": 0,
            "target_results": [],
            "schema_version": GAIA_SCAN_SCHEMA_VERSION,
            "disclaimer": GAIA_SCAN_DISCLAIMER,
        }

    from techno_search.live_data import GaiaLiveAdapter  # type: ignore[attr-defined]

    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    target_results: list[dict[str, Any]] = []
    total_sources = 0

    for target in targets:
        try:
            adapter = GaiaLiveAdapter()
            request = adapter.build_cone_search_request(
                ra_deg=target.ra_deg,
                dec_deg=target.dec_deg,
                radius_deg=target.radius_arcsec / 3600.0,
            )
            result = adapter.fetch_metadata(request)
            source_count = result.get("row_count", 0)
            total_sources += source_count
            entry: dict[str, Any] = {
                "target_name": target.name,
                "ra_deg": target.ra_deg,
                "dec_deg": target.dec_deg,
                "radius_arcsec": target.radius_arcsec,
                "source_count": source_count,
                "ok": True,
                "error_msg": None,
            }
            if output_dir is not None:
                out_path = output_dir / f"{target.name}_gaia.json"
                out_path.write_text(json.dumps(entry, indent=2))
        except Exception as exc:  # noqa: BLE001
            entry = {
                "target_name": target.name,
                "ra_deg": target.ra_deg,
                "dec_deg": target.dec_deg,
                "radius_arcsec": target.radius_arcsec,
                "source_count": 0,
                "ok": False,
                "error_msg": str(exc),
            }
        target_results.append(entry)

    return {
        "live_data_disabled": False,
        "targets_queried": len(targets),
        "total_sources": total_sources,
        "target_results": target_results,
        "schema_version": GAIA_SCAN_SCHEMA_VERSION,
        "disclaimer": GAIA_SCAN_DISCLAIMER,
    }


def gaia_scan_summary_disabled() -> dict[str, Any]:
    """Return a summary suitable for use when live data is not enabled."""
    return {
        "live_data_disabled": True,
        "targets_queried": 0,
        "total_sources": 0,
        "target_results": [],
        "schema_version": GAIA_SCAN_SCHEMA_VERSION,
        "disclaimer": GAIA_SCAN_DISCLAIMER,
    }


def load_targets_from_json(path: Path) -> list[GaiaScanTarget]:
    """Load a list of GaiaScanTarget from a JSON file.

    Expected format::

        [
          {"name": "HIP99427", "ra_deg": 302.08, "dec_deg": 6.96,
           "radius_arcsec": 30.0},
          ...
        ]
    """
    data = json.loads(Path(path).read_text())
    return [
        GaiaScanTarget(
            name=entry["name"],
            ra_deg=float(entry["ra_deg"]),
            dec_deg=float(entry["dec_deg"]),
            radius_arcsec=float(entry.get("radius_arcsec", 30.0)),
        )
        for entry in data
    ]
