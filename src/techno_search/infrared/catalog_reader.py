"""Reader for real Gaia+WISE cross-match catalog CSV files (IRSA TAP format)."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

# Column names as returned by IRSA TAP Gaia+AllWISE cross-match queries
_GAIA_SOURCE_ALIASES = ("source_id", "SOURCE_ID", "gaia_source_id")
_RA_ALIASES = ("ra", "RA", "ra_deg", "ra_j2000")
_DEC_ALIASES = ("dec", "DEC", "dec_deg", "dec_j2000")
_GMAG_ALIASES = ("phot_g_mean_mag", "g_mean_mag", "G_mag")
_W1_ALIASES = ("w1mpro", "W1mpro", "w1_mpro", "mag_w1")
_W2_ALIASES = ("w2mpro", "W2mpro", "w2_mpro", "mag_w2")
_W3_ALIASES = ("w3mpro", "W3mpro", "w3_mpro", "mag_w3")
_W4_ALIASES = ("w4mpro", "W4mpro", "w4_mpro", "mag_w4")
# AllWISE profile-fit photometric uncertainty columns (verified against the
# AllWISE Explanatory Supplement: Source Catalog and Reject Table).
_W3_ERR_ALIASES = ("w3sigmpro", "W3sigmpro", "w3_sigmpro")
_W4_ERR_ALIASES = ("w4sigmpro", "W4sigmpro", "w4_sigmpro")
_PARALLAX_ALIASES = ("parallax", "plx", "parallax_mas")
_PARALLAX_ERR_ALIASES = ("parallax_error", "e_parallax", "parallax_err")


def _get(row: dict[str, str], aliases: tuple[str, ...]) -> str | None:
    for name in aliases:
        v = row.get(name)
        if v is not None and v.strip() not in ("", "null", "NULL", "nan"):
            return v.strip()
    return None


def _float_or_none(v: str | None) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def read_gaia_wise_csv(path: Path) -> list[dict[str, Any]]:
    """Read a Gaia+AllWISE cross-match CSV (IRSA TAP format) into row dicts.

    Returns rows with normalized keys matching InfraredSource field names.
    Handles comment lines starting with '#' and missing WISE photometry.
    """
    rows: list[dict[str, Any]] = []
    with open(path, newline="") as f:
        lines = [ln for ln in f if not ln.startswith("#")]

    reader = csv.DictReader(lines)
    for raw in reader:
        raw = {k.strip(): v.strip() for k, v in raw.items() if k is not None}

        ra = _float_or_none(_get(raw, _RA_ALIASES))
        dec = _float_or_none(_get(raw, _DEC_ALIASES))
        if ra is None or dec is None:
            continue

        rows.append({
            "source_id": _get(raw, _GAIA_SOURCE_ALIASES) or "",
            "ra_deg": ra,
            "dec_deg": dec,
            "g_mag": _float_or_none(_get(raw, _GMAG_ALIASES)),
            "w1_mag": _float_or_none(_get(raw, _W1_ALIASES)),
            "w2_mag": _float_or_none(_get(raw, _W2_ALIASES)),
            "w3_mag": _float_or_none(_get(raw, _W3_ALIASES)),
            "w4_mag": _float_or_none(_get(raw, _W4_ALIASES)),
            "w3_mag_err": _float_or_none(_get(raw, _W3_ERR_ALIASES)),
            "w4_mag_err": _float_or_none(_get(raw, _W4_ERR_ALIASES)),
            "parallax_mas": _float_or_none(_get(raw, _PARALLAX_ALIASES)),
            "parallax_error": _float_or_none(_get(raw, _PARALLAX_ERR_ALIASES)),
        })
    return rows


def catalog_rows_to_infrared_source_dicts(path: Path) -> list[dict[str, Any]]:
    """Read a real Gaia+WISE CSV and return dicts compatible with build_infrared_candidate().

    Maps real catalog column names to InfraredSource field names used by the prototype.
    """
    raw_rows = read_gaia_wise_csv(path)
    out = []
    for r in raw_rows:
        out.append({
            "source_id": r["source_id"],
            "gaia_source_id": r["source_id"],
            "ra": r["ra_deg"],
            "dec": r["dec_deg"],
            "ra_deg": r["ra_deg"],
            "dec_deg": r["dec_deg"],
            "g_mag": r["g_mag"],
            "w1": r["w1_mag"],
            "w2": r["w2_mag"],
            "w3": r["w3_mag"],
            "w4": r["w4_mag"],
            "w3_mag_err": r["w3_mag_err"],
            "w4_mag_err": r["w4_mag_err"],
            "parallax": r["parallax_mas"],
            "parallax_error": r["parallax_error"],
        })
    return out
