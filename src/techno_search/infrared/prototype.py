"""Synthetic infrared catalog prototype."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from techno_search.schemas import Candidate, FeatureValue, Track


@dataclass(frozen=True)
class InfraredSource:
    """Normalized synthetic Gaia/WISE-like source row."""

    gaia_source_id: str
    ra: float
    dec: float
    parallax: float
    proper_motion: float
    g_mag: float
    bp_rp: float
    w1: float
    w2: float
    w3: float
    w4: float | None = None
    photometric_quality_score: float = 0.5
    confusion_score: float = 0.0
    galaxy_agn_indicator_score: float = 0.0
    dust_indicator_score: float = 0.0
    catalog_artifact_score: float = 0.0


def build_infrared_candidate(
    candidate_id: str,
    row: Mapping[str, FeatureValue],
    *,
    source_ids: Sequence[str] = (),
    provenance: Mapping[str, FeatureValue] | None = None,
) -> Candidate:
    """Build a shared candidate from a synthetic infrared catalog row."""

    source = _parse_source(row)
    w1_w3 = source.w1 - source.w3
    w2_w3 = source.w2 - source.w3
    w3_w4 = 0.0 if source.w4 is None else source.w3 - source.w4

    features: dict[str, FeatureValue] = {
        "gaia_source_id": source.gaia_source_id,
        "ra": source.ra,
        "dec": source.dec,
        "parallax": source.parallax,
        "proper_motion": source.proper_motion,
        "g_mag": source.g_mag,
        "bp_rp": source.bp_rp,
        "w1": source.w1,
        "w2": source.w2,
        "w3": source.w3,
        "w4": source.w4,
        "ir_excess_score": _score_or(row, "ir_excess_score", _color_excess_score(w1_w3)),
        "sed_fit_residual_score": _score_or(
            row,
            "sed_fit_residual_score",
            _sed_residual_score(w1_w3, w2_w3, w3_w4),
        ),
        "stellar_solution_quality": _score_or(
            row,
            "stellar_solution_quality",
            _stellar_solution_quality(source.parallax, source.proper_motion),
        ),
        "galaxy_agn_indicator_score": source.galaxy_agn_indicator_score,
        "dust_indicator_score": source.dust_indicator_score,
        "confusion_score": source.confusion_score,
        "photometric_quality_score": source.photometric_quality_score,
        "catalog_artifact_score": source.catalog_artifact_score,
        "data_quality_score": source.photometric_quality_score,
        "provenance_completeness_score": 1.0 if provenance else 0.4,
    }

    return Candidate(
        candidate_id=candidate_id,
        track=Track.INFRARED,
        features=features,
        source_ids=tuple(source_ids or (source.gaia_source_id,)),
        provenance=provenance or {},
    )


def _parse_source(row: Mapping[str, FeatureValue]) -> InfraredSource:
    return InfraredSource(
        gaia_source_id=str(row.get("gaia_source_id", "unknown")),
        ra=_float(row.get("ra", 0.0)),
        dec=_float(row.get("dec", 0.0)),
        parallax=_float(row.get("parallax", 0.0)),
        proper_motion=_float(row.get("proper_motion", 0.0)),
        g_mag=_float(row.get("g_mag", 0.0)),
        bp_rp=_float(row.get("bp_rp", 0.0)),
        w1=_required_float(row, "w1"),
        w2=_required_float(row, "w2"),
        w3=_required_float(row, "w3"),
        w4=_optional_float(row.get("w4")),
        photometric_quality_score=_score_or(row, "photometric_quality_score", 0.5),
        confusion_score=_score_or(row, "confusion_score", 0.0),
        galaxy_agn_indicator_score=_score_or(row, "galaxy_agn_indicator_score", 0.0),
        dust_indicator_score=_score_or(row, "dust_indicator_score", 0.0),
        catalog_artifact_score=_score_or(row, "catalog_artifact_score", 0.0),
    )


def _color_excess_score(w1_w3: float) -> float:
    return _clamp((w1_w3 - 0.5) / 2.5)


def _sed_residual_score(w1_w3: float, w2_w3: float, w3_w4: float) -> float:
    return _clamp(((w1_w3 - 0.4) + (w2_w3 - 0.2) + max(w3_w4, 0.0)) / 4.0)


def _stellar_solution_quality(parallax: float, proper_motion: float) -> float:
    parallax_score = _clamp(parallax / 5.0)
    motion_score = _clamp(proper_motion / 50.0)
    return _clamp((0.65 * parallax_score) + (0.35 * motion_score))


def _score_or(row: Mapping[str, FeatureValue], key: str, default: float) -> float:
    if key not in row:
        return _clamp(default)
    return _clamp(_float(row[key]))


def _required_float(row: Mapping[str, FeatureValue], key: str) -> float:
    if key not in row:
        msg = f"Missing required infrared source field: {key}"
        raise ValueError(msg)
    return _float(row[key])


def _optional_float(value: FeatureValue) -> float | None:
    if value is None:
        return None
    return _float(value)


def _float(value: FeatureValue) -> float:
    if isinstance(value, bool) or value is None:
        msg = f"Expected numeric value, got {value!r}"
        raise TypeError(msg)
    if isinstance(value, int | float):
        return float(value)
    return float(value)


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))
