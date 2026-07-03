"""Real cross-modal candidate matching by sky position (Phase 5).

Uses ``astropy.coordinates.SkyCoord.separation()`` -- the same real, verified
API already used elsewhere in this project for Track A catalog and
satellite-transmitter matching -- to group candidates from different tracks
(radio, transit photometry, infrared) whose reported sky positions are
consistent with the same physical target.

Per AGENTS.md Phase 5: "A target appearing in >= 2 independent modalities
with anomalies is a priority candidate for the adversarial review agent."
This module implements the matching step that identifies those groups; it
does not itself run the adversarial review agent (Phase 5's remaining,
separate, not-yet-built task).

The match radius is a caller-supplied parameter, not a hardcoded
"calibrated" constant: real instrument beam/PSF sizes vary by orders of
magnitude across radio (GBT beam ~ arcminutes), transit photometry
(Kepler/TESS pixel ~4-21 arcsec, though source confusion can be larger), and
infrared (WISE PSF ~6-12 arcsec). No single number is scientifically correct
for every track combination; this module documents a conservative generic
default (60 arcsec) rather than presenting one as calibrated.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

MULTI_MODAL_CROSSMATCH_SCHEMA_VERSION = "multi_modal_crossmatch_v1"
MULTI_MODAL_CROSSMATCH_DISCLAIMER = (
    "Cross-modal sky-position matches are local triage evidence only. A "
    "candidate appearing in multiple tracks within the match radius is not "
    "a detection, discovery, expert review, or external-submission "
    "authorization -- it identifies which candidates should be prioritized "
    "for adversarial review (AGENTS.md Phase 5)."
)
# Conservative generic cross-survey default, not a per-instrument-calibrated
# value. Callers with real per-track beam/PSF sizes should supply their own
# radius instead of relying on this default.
DEFAULT_MATCH_RADIUS_ARCSEC = 60.0


@dataclass(frozen=True)
class CandidatePosition:
    """A minimal real sky position and identity for one scored candidate."""

    candidate_id: str
    track: str
    ra_deg: float
    dec_deg: float
    pathway: str = ""


@dataclass(frozen=True)
class MultiModalGroup:
    """A group of candidates whose sky positions match within the radius."""

    candidate_ids: tuple[str, ...]
    tracks: tuple[str, ...]
    max_separation_arcsec: float

    @property
    def distinct_track_count(self) -> int:
        return len(set(self.tracks))

    @property
    def is_multi_modal(self) -> bool:
        return self.distinct_track_count >= 2

    def as_dict(self) -> dict[str, Any]:
        return {
            "candidate_ids": list(self.candidate_ids),
            "tracks": list(self.tracks),
            "distinct_track_count": self.distinct_track_count,
            "is_multi_modal": self.is_multi_modal,
            "max_separation_arcsec": self.max_separation_arcsec,
        }


def find_multi_modal_groups(
    candidates: Sequence[CandidatePosition],
    *,
    match_radius_arcsec: float = DEFAULT_MATCH_RADIUS_ARCSEC,
) -> list[MultiModalGroup]:
    """Group candidates by real sky-position proximity across tracks.

    Uses union-find over pairwise ``astropy.coordinates.SkyCoord.separation()``
    checks: any two candidates within ``match_radius_arcsec`` of each other
    join the same group (transitively), regardless of track. Returns only
    groups with 2 or more members; single, unmatched candidates are not
    returned since they cannot be multi-modal by definition.
    """

    import astropy.units as u
    from astropy.coordinates import SkyCoord

    n = len(candidates)
    if n < 2:
        return []

    coords = SkyCoord(
        ra=[c.ra_deg for c in candidates] * u.deg,
        dec=[c.dec_deg for c in candidates] * u.deg,
    )
    radius = match_radius_arcsec * u.arcsec

    parent = list(range(n))

    def _find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def _union(i: int, j: int) -> None:
        root_i, root_j = _find(i), _find(j)
        if root_i != root_j:
            parent[root_j] = root_i

    max_separation_arcsec: dict[tuple[int, int], float] = {}
    for i in range(n):
        separations = coords[i].separation(coords[i + 1 :])
        for offset, separation in enumerate(separations):
            j = i + 1 + offset
            if separation <= radius:
                _union(i, j)
                max_separation_arcsec[(i, j)] = float(separation.arcsec)

    groups_by_root: dict[int, list[int]] = {}
    for index in range(n):
        groups_by_root.setdefault(_find(index), []).append(index)

    results: list[MultiModalGroup] = []
    for members in groups_by_root.values():
        if len(members) < 2:
            continue
        member_set = set(members)
        group_max_sep = max(
            (
                sep
                for (i, j), sep in max_separation_arcsec.items()
                if i in member_set and j in member_set
            ),
            default=0.0,
        )
        results.append(
            MultiModalGroup(
                candidate_ids=tuple(candidates[i].candidate_id for i in members),
                tracks=tuple(candidates[i].track for i in members),
                max_separation_arcsec=group_max_sep,
            )
        )
    return results


def candidate_positions_from_reports(
    reports: Sequence[Mapping[str, Any]],
) -> list[CandidatePosition]:
    """Extract real sky positions from candidate report dicts (as_dict() output).

    Skips candidates that lack real ``ra_deg``/``dec_deg`` features -- most
    tracks only populate these when a real coordinate was available (e.g.
    from a FITS header, catalog cross-match, or hit-table row), so silently
    dropping candidates without them avoids fabricating a sky position.
    """

    positions: list[CandidatePosition] = []
    for report in reports:
        features = report.get("features", {})
        ra_deg = features.get("ra_deg")
        dec_deg = features.get("dec_deg")
        if ra_deg is None or dec_deg is None:
            continue
        positions.append(
            CandidatePosition(
                candidate_id=str(report.get("candidate_id", "")),
                track=str(report.get("track", "")),
                ra_deg=float(ra_deg),
                dec_deg=float(dec_deg),
                pathway=str(report.get("recommended_pathway", "")),
            )
        )
    return positions


def multi_modal_crossmatch_summary(
    reports: Sequence[Mapping[str, Any]],
    *,
    match_radius_arcsec: float = DEFAULT_MATCH_RADIUS_ARCSEC,
) -> dict[str, Any]:
    """Real cross-modal candidate matching summary from candidate report dicts."""

    positions = candidate_positions_from_reports(reports)
    groups = find_multi_modal_groups(positions, match_radius_arcsec=match_radius_arcsec)
    multi_modal_groups = [group for group in groups if group.is_multi_modal]

    return {
        "schema_version": MULTI_MODAL_CROSSMATCH_SCHEMA_VERSION,
        "disclaimer": MULTI_MODAL_CROSSMATCH_DISCLAIMER,
        "match_radius_arcsec": match_radius_arcsec,
        "candidate_count_with_position": len(positions),
        "candidate_count_without_position": len(reports) - len(positions),
        "group_count": len(groups),
        "multi_modal_group_count": len(multi_modal_groups),
        "multi_modal_groups": [group.as_dict() for group in multi_modal_groups],
        "single_track_group_count": len(groups) - len(multi_modal_groups),
    }
