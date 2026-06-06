"""Live catalog cross-match helpers for Gaia TAP and SIMBAD.

These helpers are operational provenance tools only.  A cross-match match
does not confirm or rule out technosignature interest, does not modify
candidate scores except through the `known_object_score` feature, and does
not authorize external submission or constitute a detection claim.

Live queries require TECHNO_SEARCH_ENABLE_LIVE_DATA=1.  When the env var is
not set, all helpers return a stub result with known_object_score=0.0 and
a note explaining that live queries are disabled.
"""
from __future__ import annotations

from typing import Any

CATALOG_CROSSMATCH_DISCLAIMER = (
    "Catalog cross-match results are operational provenance records only. "
    "A catalog match does not confirm or rule out technosignature interest, "
    "does not authorize external submission, and does not constitute a "
    "detection claim or discovery."
)

_STUB: dict[str, Any] = {
    "disclaimer": CATALOG_CROSSMATCH_DISCLAIMER,
    "provider": "none",
    "query_attempted": False,
    "live_data_enabled": False,
    "match_count": 0,
    "known_object_score": 0.0,
    "match_names": [],
    "note": (
        "Live catalog queries disabled. Set TECHNO_SEARCH_ENABLE_LIVE_DATA=1 "
        "to enable Gaia TAP and SIMBAD cross-matching."
    ),
}


def _is_live_enabled() -> bool:
    import os

    from techno_search.live_data import LIVE_DATA_ENV_VAR

    return os.environ.get(LIVE_DATA_ENV_VAR, "").strip().lower() in {"1", "true", "yes"}


# ---------------------------------------------------------------------------
# Gaia TAP cone search
# ---------------------------------------------------------------------------

def gaia_cone_search(
    ra_deg: float,
    dec_deg: float,
    *,
    radius_arcsec: float = 5.0,
    timeout_seconds: float = 20.0,
) -> dict[str, Any]:
    """Query Gaia DR3 for sources within radius_arcsec of (ra_deg, dec_deg).

    Returns a cross-match result dict including `known_object_score`.

    Requires TECHNO_SEARCH_ENABLE_LIVE_DATA=1.  Returns a stub with
    known_object_score=0.0 when live data is disabled.
    """
    if not _is_live_enabled():
        return dict(_STUB, provider="gaia")

    try:
        from techno_search.live_data import (
            GaiaAdapter,
            GaiaLiveClient,
            LiveProviderCache,
        )
    except ImportError as exc:
        return dict(_STUB, provider="gaia", note=f"Gaia client not available: {exc}")

    radius_deg = radius_arcsec / 3600.0
    adql = (
        "SELECT source_id, ra, dec, parallax, pmra, pmdec, phot_g_mean_mag, "
        "ruwe, classprob_dsc_combmod_star "
        f"FROM gaiadr3.gaia_source "
        f"WHERE CONTAINS(POINT('ICRS', ra, dec), "
        f"CIRCLE('ICRS', {ra_deg:.8f}, {dec_deg:.8f}, {radius_deg:.8f})) = 1 "
        "ORDER BY phot_g_mean_mag ASC"
    )

    try:
        adapter = GaiaAdapter()
        request = adapter.build_cone_search_request(
            ra_deg=ra_deg,
            dec_deg=dec_deg,
            radius_arcsec=radius_arcsec,
            purpose="catalog-crossmatch-known-object",
        )
        request_with_query = type(request)(
            source_name=request.source_name,
            query=adql,
            purpose=request.purpose,
            parameters=request.parameters,
        )

        cache = LiveProviderCache.from_config()
        client = GaiaLiveClient(timeout_seconds=timeout_seconds)
        meta = client.fetch_metadata(request_with_query)

        rows: list[dict[str, Any]] = list(meta.get("rows", []))
        match_count = len(rows)
        match_names = [f"Gaia DR3 {r.get('source_id', '?')}" for r in rows[:5]]

        known_object_score = _known_object_score_from_match_count(match_count)

        _ = cache  # cache is passed in for future caching support

        return {
            "disclaimer": CATALOG_CROSSMATCH_DISCLAIMER,
            "provider": "gaia",
            "query_attempted": True,
            "live_data_enabled": True,
            "ra_deg": ra_deg,
            "dec_deg": dec_deg,
            "radius_arcsec": radius_arcsec,
            "match_count": match_count,
            "known_object_score": known_object_score,
            "match_names": match_names,
            "adql": adql,
        }

    except Exception as exc:  # noqa: BLE001
        return {
            "disclaimer": CATALOG_CROSSMATCH_DISCLAIMER,
            "provider": "gaia",
            "query_attempted": True,
            "live_data_enabled": True,
            "match_count": 0,
            "known_object_score": 0.0,
            "match_names": [],
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# SIMBAD object lookup
# ---------------------------------------------------------------------------

def simbad_cone_search(
    ra_deg: float,
    dec_deg: float,
    *,
    radius_arcsec: float = 10.0,
    timeout_seconds: float = 20.0,
) -> dict[str, Any]:
    """Query SIMBAD for known objects within radius_arcsec of (ra_deg, dec_deg).

    Returns a cross-match result dict including `known_object_score`.

    Requires TECHNO_SEARCH_ENABLE_LIVE_DATA=1.  Returns a stub with
    known_object_score=0.0 when live data is disabled.
    """
    if not _is_live_enabled():
        return dict(_STUB, provider="simbad")

    try:
        from techno_search.live_data import (
            SimbadAdapter,
            SimbadLiveClient,
        )
    except ImportError as exc:
        return dict(_STUB, provider="simbad", note=f"SIMBAD client not available: {exc}")

    try:
        adapter = SimbadAdapter()
        request = adapter.build_object_lookup_request(
            object_name=f"ICRS {ra_deg:.6f} {dec_deg:.6f}",
            purpose="catalog-crossmatch-known-object",
        )

        client = SimbadLiveClient(timeout_seconds=timeout_seconds)
        meta = client.fetch_metadata(request)

        rows: list[dict[str, Any]] = list(meta.get("rows", []))
        match_count = len(rows)
        match_names = [
            str(r.get("main_id", r.get("MAIN_ID", "?"))) for r in rows[:5]
        ]

        known_object_score = _known_object_score_from_match_count(match_count)

        return {
            "disclaimer": CATALOG_CROSSMATCH_DISCLAIMER,
            "provider": "simbad",
            "query_attempted": True,
            "live_data_enabled": True,
            "ra_deg": ra_deg,
            "dec_deg": dec_deg,
            "radius_arcsec": radius_arcsec,
            "match_count": match_count,
            "known_object_score": known_object_score,
            "match_names": match_names,
        }

    except Exception as exc:  # noqa: BLE001
        return {
            "disclaimer": CATALOG_CROSSMATCH_DISCLAIMER,
            "provider": "simbad",
            "query_attempted": True,
            "live_data_enabled": True,
            "match_count": 0,
            "known_object_score": 0.0,
            "match_names": [],
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# Combined cross-match (tries SIMBAD first, then Gaia)
# ---------------------------------------------------------------------------

def catalog_crossmatch(
    ra_deg: float | None,
    dec_deg: float | None,
    *,
    radius_arcsec: float = 10.0,
    timeout_seconds: float = 20.0,
) -> dict[str, Any]:
    """Run SIMBAD + Gaia cross-match for a position, returning combined result.

    When coordinates are not available, returns a stub with known_object_score=0.0.
    When live data is disabled, returns a stub with a note.

    The returned `known_object_score` is the maximum of both providers and is
    safe to pass directly as a feature to the scoring pipeline.
    """
    if ra_deg is None or dec_deg is None:
        return dict(
            _STUB,
            provider="none",
            note="No RA/DEC available — cross-match skipped.",
        )

    if not _is_live_enabled():
        return dict(_STUB, provider="none")

    simbad = simbad_cone_search(ra_deg, dec_deg, radius_arcsec=radius_arcsec,
                                timeout_seconds=timeout_seconds)
    gaia = gaia_cone_search(ra_deg, dec_deg, radius_arcsec=radius_arcsec / 2.0,
                            timeout_seconds=timeout_seconds)

    combined_score = max(
        float(simbad.get("known_object_score", 0.0)),
        float(gaia.get("known_object_score", 0.0)),
    )

    return {
        "disclaimer": CATALOG_CROSSMATCH_DISCLAIMER,
        "provider": "simbad+gaia",
        "query_attempted": True,
        "live_data_enabled": True,
        "ra_deg": ra_deg,
        "dec_deg": dec_deg,
        "radius_arcsec": radius_arcsec,
        "known_object_score": combined_score,
        "simbad_match_count": int(simbad.get("match_count", 0)),
        "gaia_match_count": int(gaia.get("match_count", 0)),
        "simbad_match_names": list(simbad.get("match_names", [])),
        "gaia_match_names": list(gaia.get("match_names", [])),
        "simbad_error": simbad.get("error"),
        "gaia_error": gaia.get("error"),
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _known_object_score_from_match_count(n: int) -> float:
    """Convert a catalog match count to a known_object_score [0, 1].

    A single catalog match → 0.9 (likely known object — reduces interest score).
    Zero matches → 0.0 (not in catalog — keeps full scoring weight).
    Multiple matches → 1.0 (catalog is dense here → almost certainly known).
    """
    if n == 0:
        return 0.0
    if n == 1:
        return 0.9
    return 1.0
