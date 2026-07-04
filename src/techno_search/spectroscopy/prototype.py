"""Spectroscopy candidate packet builder (Phase 4).

Turns real JWST MIRI LRS technosignature-gas band-search results
(``technosignature_gases.py``) into the shared ``Candidate`` schema used by
``scoring.py``. All numeric features are computed directly from the
caller-supplied real spectrum results -- none are synthetic.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from techno_search.schemas import Candidate, FeatureValue, Track
from techno_search.spectroscopy.hitran_xsc_matched_filter import MatchedFilterResult
from techno_search.spectroscopy.technosignature_gases import BandFeatureResult

# 5-sigma is the standard statistical-significance convention for claiming a
# real detection across physics and astronomy (the same threshold used for,
# e.g., particle-physics discovery claims) -- not a value invented for this
# project.
DETECTION_SIGNIFICANCE_SIGMA = 5.0
# Heuristic scaling divisor for combining an unbounded significance value
# into the interpretable v0/v1 scorer's [0, 1] feature range -- the same
# kind of fixed scaling divisor already used throughout scoring.py (e.g.
# SNR/50, drift/5), not a calibrated detection threshold.
_SIGNIFICANCE_SCORE_DIVISOR = 10.0


def build_spectroscopy_candidate(
    candidate_id: str,
    *,
    band_results: Sequence[BandFeatureResult],
    target_id: str = "unknown",
    ra_deg: float | None = None,
    dec_deg: float | None = None,
    point_count: int = 0,
    known_object_score: float = 0.0,
    source_ids: Sequence[str] = (),
    provenance: Mapping[str, FeatureValue] | None = None,
    matched_filter_results: Sequence[MatchedFilterResult] = (),
) -> Candidate:
    """Build a spectroscopy candidate from real gas absorption-band search results.

    ``matched_filter_results`` (optional): real full-grid HITRAN
    cross-section matched-filter results (see
    ``hitran_xsc_matched_filter.py``), when the caller has real local
    ``.xsc`` files available. These are attached as informational
    features only (``<gas>_matched_filter_significance_sigma`` etc.) --
    they do not currently feed into ``technosignature_gas_score``,
    ``detected_band_count``, or the posterior, since this is a newer,
    less-validated statistic than the single-peak band check. A future
    revision could incorporate it once validated against more real data.
    """

    features: dict[str, FeatureValue] = {
        "target_id": target_id,
        "point_count": point_count,
        "known_object_score": _clamp(known_object_score),
        "provenance_completeness_score": (1.0 if provenance else 0.4),
        "data_quality_score": 1.0 if point_count > 0 else 0.0,
    }

    computable_results = [
        r for r in band_results if r.computable and r.significance_sigma is not None
    ]
    detected = [
        r
        for r in computable_results
        if abs(r.significance_sigma or 0.0) >= DETECTION_SIGNIFICANCE_SIGMA
    ]
    max_significance = max(
        (abs(r.significance_sigma or 0.0) for r in computable_results),
        default=0.0,
    )

    for result in band_results:
        key = _band_feature_key(result)
        features[f"{key}_computable"] = result.computable
        if result.computable and result.significance_sigma is not None:
            features[f"{key}_significance_sigma"] = result.significance_sigma

    features["computable_band_count"] = len(computable_results)
    features["detected_band_count"] = len(detected)
    features["detected_gases"] = ", ".join(sorted({r.gas for r in detected})) or "none"
    features["max_gas_band_significance_sigma"] = max_significance
    features["technosignature_gas_score"] = _clamp(max_significance / _SIGNIFICANCE_SCORE_DIVISOR)

    if ra_deg is not None:
        features["ra_deg"] = ra_deg
    if dec_deg is not None:
        features["dec_deg"] = dec_deg

    computable_matched_filters = [
        r for r in matched_filter_results if r.computable and r.significance_sigma is not None
    ]
    for mf_result in matched_filter_results:
        key = f"{mf_result.gas.lower()}_matched_filter"
        features[f"{key}_computable"] = mf_result.computable
        if mf_result.computable and mf_result.significance_sigma is not None:
            features[f"{key}_significance_sigma"] = mf_result.significance_sigma
    if matched_filter_results:
        features["matched_filter_computable_count"] = len(computable_matched_filters)
        features["matched_filter_max_significance_sigma"] = max(
            (abs(r.significance_sigma or 0.0) for r in computable_matched_filters),
            default=0.0,
        )

    return Candidate(
        candidate_id=candidate_id,
        track=Track.SPECTROSCOPY,
        features=features,
        source_ids=tuple(source_ids or (target_id,)),
        provenance=provenance or {},
    )


def _band_feature_key(result: BandFeatureResult) -> str:
    return f"{result.gas.lower()}_{result.band_center_um:.2f}um".replace(".", "p")


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))
