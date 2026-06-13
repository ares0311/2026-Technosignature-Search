"""Cross-store candidate deduplication.

Identifies the same astronomical source appearing in multiple data stores
(radio BL/GBT, infrared Gaia/WISE, archival anomaly) by position match
within angular tolerance.  Multi-track corroboration is recorded as a
provenance note, not as increased confidence of a detection claim.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

CROSS_STORE_DEDUP_DISCLAIMER = (
    "Cross-store position matches are provenance records only. "
    "Multi-track corroboration does not constitute a detection claim "
    "and does not authorize external submission."
)

CROSS_STORE_DEDUP_SCHEMA_VERSION = "cross_store_dedup_v1"

_ARCSEC_PER_DEGREE = 3600.0


def _angular_separation_deg(
    ra1: float,
    dec1: float,
    ra2: float,
    dec2: float,
) -> float:
    """Great-circle angular separation in degrees."""
    ra1_r = math.radians(ra1)
    ra2_r = math.radians(ra2)
    dec1_r = math.radians(dec1)
    dec2_r = math.radians(dec2)
    cos_sep = math.sin(dec1_r) * math.sin(dec2_r) + math.cos(dec1_r) * math.cos(
        dec2_r
    ) * math.cos(ra1_r - ra2_r)
    cos_sep = max(-1.0, min(1.0, cos_sep))
    return math.degrees(math.acos(cos_sep))


@dataclass
class CrossStoreMatch:
    """Record of two candidates matched across different data stores."""

    match_id: str
    candidate_id_a: str
    store_a: str
    candidate_id_b: str
    store_b: str
    separation_arcsec: float
    tracks_matched: list[str]
    corroboration_note: str
    schema_version: str = CROSS_STORE_DEDUP_SCHEMA_VERSION
    disclaimer: str = CROSS_STORE_DEDUP_DISCLAIMER

    def as_dict(self) -> dict[str, Any]:
        return {
            "match_id": self.match_id,
            "candidate_id_a": self.candidate_id_a,
            "store_a": self.store_a,
            "candidate_id_b": self.candidate_id_b,
            "store_b": self.store_b,
            "separation_arcsec": self.separation_arcsec,
            "tracks_matched": self.tracks_matched,
            "corroboration_note": self.corroboration_note,
            "schema_version": self.schema_version,
            "disclaimer": self.disclaimer,
        }


def find_cross_store_matches(
    candidate_lists: list[list[dict[str, Any]]],
    store_names: list[str],
    tolerance_arcsec: float = 10.0,
) -> list[CrossStoreMatch]:
    """Find position matches across different data stores.

    Args:
        candidate_lists: One list per store.  Each candidate dict must have
            ``ra_deg``, ``dec_deg``, ``candidate_id``, and ``track`` keys.
            Candidates without ``ra_deg``/``dec_deg`` are skipped silently.
        store_names: Names of each store (parallel to candidate_lists).
        tolerance_arcsec: Angular separation threshold for a position match.

    Returns:
        List of CrossStoreMatch records.  Each pair is reported once.
    """
    if len(candidate_lists) != len(store_names):
        raise ValueError("candidate_lists and store_names must have equal length")

    # Flatten with store labels, skipping candidates without coordinates.
    labelled: list[tuple[str, str, str, float, float]] = []
    for store, cands in zip(store_names, candidate_lists, strict=True):
        for c in cands:
            ra = c.get("ra_deg")
            dec = c.get("dec_deg")
            if ra is None or dec is None:
                continue
            labelled.append((store, c["candidate_id"], c.get("track", "unknown"),
                              float(ra), float(dec)))

    tol_deg = tolerance_arcsec / _ARCSEC_PER_DEGREE
    matches: list[CrossStoreMatch] = []
    seen: set[frozenset[str]] = set()

    for i, (store_a, cid_a, track_a, ra_a, dec_a) in enumerate(labelled):
        for store_b, cid_b, track_b, ra_b, dec_b in labelled[i + 1:]:
            if store_a == store_b:
                continue  # same-store matches are duplicates, not cross-store
            pair_key = frozenset({cid_a, cid_b})
            if pair_key in seen:
                continue
            sep_deg = _angular_separation_deg(ra_a, dec_a, ra_b, dec_b)
            if sep_deg <= tol_deg:
                seen.add(pair_key)
                sep_arcsec = sep_deg * _ARCSEC_PER_DEGREE
                match_id = f"xmatch-{len(matches):04d}"
                tracks = sorted({track_a, track_b})
                note = (
                    f"Position match within {sep_arcsec:.1f} arcsec across "
                    f"{store_a!r} and {store_b!r}. "
                    "Multi-track corroboration recorded for provenance only."
                )
                matches.append(
                    CrossStoreMatch(
                        match_id=match_id,
                        candidate_id_a=cid_a,
                        store_a=store_a,
                        candidate_id_b=cid_b,
                        store_b=store_b,
                        separation_arcsec=sep_arcsec,
                        tracks_matched=tracks,
                        corroboration_note=note,
                    )
                )

    return matches


def cross_store_dedup_summary(
    candidate_lists: list[list[dict[str, Any]]],
    store_names: list[str],
    tolerance_arcsec: float = 10.0,
) -> dict[str, Any]:
    """Summarise cross-store position matches."""
    total = sum(len(c) for c in candidate_lists)
    matches = find_cross_store_matches(candidate_lists, store_names, tolerance_arcsec)
    multi_track = [m for m in matches if len(m.tracks_matched) > 1]
    return {
        "total_candidates": total,
        "stores_compared": len(store_names),
        "store_names": store_names,
        "cross_store_match_count": len(matches),
        "multi_track_corroboration_count": len(multi_track),
        "tolerance_arcsec": tolerance_arcsec,
        "matches": [m.as_dict() for m in matches],
        "schema_version": CROSS_STORE_DEDUP_SCHEMA_VERSION,
        "disclaimer": CROSS_STORE_DEDUP_DISCLAIMER,
    }
