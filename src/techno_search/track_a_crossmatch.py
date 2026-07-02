"""Track A Phase 2: deterministic known-source cone-search cross-match.

Given a candidate sky position, searches the normalized ATNF/CHIME-FRB/
Roma-BZCAT/Fermi-4FGL catalogs (see track_a_catalogs.py) for a known source
within a small cone radius. This answers the Track A question from
docs/technosignature_datasets_agent_brief.md:

    Is this candidate plausibly explained by a known pulsar, FRB, blazar/AGN,
    or gamma-ray source?

This is a deterministic rule/cross-match layer, not a claim about candidate
anomaly status. Absence of a match does not mean the candidate is a
technosignature; it means Track A found no known-source explanation from the
catalogs currently loaded locally, which is reported as `low_confidence` when
one or more catalogs are unavailable.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from techno_search.track_a_catalogs import default_normalized_catalog_path

TRACK_A_CROSSMATCH_SCHEMA_VERSION = "track_a_crossmatch_v1"
DEFAULT_RADIUS_ARCSEC = 30.0

ALL_CATALOG_NAMES = ("atnf", "chime_frb", "romabzcat", "fermi_4fgl")

TRACK_A_CROSSMATCH_DISCLAIMER = (
    "Track A catalog cross-match is a deterministic known-source lookup only. "
    "No match does not confirm technosignature interest; it means no loaded "
    "catalog explains the position within the search radius. A `low_confidence` "
    "classification means one or more reference catalogs were not available "
    "locally, not that the candidate has been cleared of known explanations."
)


@dataclass(frozen=True)
class CatalogMatch:
    catalog_name: str
    source_id: str
    object_class: str
    separation_arcsec: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "catalog_name": self.catalog_name,
            "source_id": self.source_id,
            "object_class": self.object_class,
            "separation_arcsec": self.separation_arcsec,
        }


def _load_catalog(
    catalog_name: str,
    *,
    project_root: Path | None,
) -> Any | None:
    import pandas as pd

    path = default_normalized_catalog_path(project_root, name=catalog_name)
    if not path.exists():
        return None
    return pd.read_parquet(path)


def _separation_arcsec(ra1_deg: float, dec1_deg: float, ra2: Any, dec2: Any) -> Any:
    from astropy import units as u
    from astropy.coordinates import SkyCoord

    candidate = SkyCoord(ra=ra1_deg * u.deg, dec=dec1_deg * u.deg)
    catalog = SkyCoord(ra=ra2.to_numpy() * u.deg, dec=dec2.to_numpy() * u.deg)
    return candidate.separation(catalog).arcsec


def cross_match_known_sources(
    ra_deg: float,
    dec_deg: float,
    *,
    radius_arcsec: float = DEFAULT_RADIUS_ARCSEC,
    catalogs: tuple[str, ...] = ALL_CATALOG_NAMES,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Cross-match a candidate position against loaded Track A catalogs.

    Returns a classification of `known_<object_class>` when the closest match
    within radius_arcsec is unambiguous, `low_confidence` when one or more
    requested catalogs are not loaded locally, or `no_known_match` when all
    requested catalogs are loaded but nothing is within radius_arcsec.
    """

    matches: list[CatalogMatch] = []
    missing_catalogs: list[str] = []

    for catalog_name in catalogs:
        df = _load_catalog(catalog_name, project_root=project_root)
        if df is None or df.empty:
            missing_catalogs.append(catalog_name)
            continue
        separations = _separation_arcsec(ra_deg, dec_deg, df["ra_deg"], df["dec_deg"])
        within_radius = separations <= radius_arcsec
        for idx in within_radius.nonzero()[0]:
            row = df.iloc[int(idx)]
            matches.append(
                CatalogMatch(
                    catalog_name=catalog_name,
                    source_id=str(row["source_id"]),
                    object_class=str(row["object_class"]),
                    separation_arcsec=float(separations[idx]),
                )
            )

    matches.sort(key=lambda m: m.separation_arcsec)
    best_match = matches[0] if matches else None

    if best_match is not None:
        classification = f"known_{best_match.object_class}"
    elif missing_catalogs:
        classification = "low_confidence"
    else:
        classification = "no_known_match"

    return {
        "schema_version": TRACK_A_CROSSMATCH_SCHEMA_VERSION,
        "disclaimer": TRACK_A_CROSSMATCH_DISCLAIMER,
        "ra_deg": ra_deg,
        "dec_deg": dec_deg,
        "radius_arcsec": radius_arcsec,
        "catalogs_requested": list(catalogs),
        "catalogs_missing": missing_catalogs,
        "match_count": len(matches),
        "best_match": best_match.as_dict() if best_match else None,
        "all_matches": [m.as_dict() for m in matches],
        "classification": classification,
    }
