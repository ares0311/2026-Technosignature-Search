"""Transit-photometry candidate packet builder (Phase 2).

Combines real BLS periodic-transit statistics (``bls_detection.py``) and real
aperiodic-dip statistics (``aperiodic_dip.py``) into the shared ``Candidate``
schema used by ``scoring.py``. All numeric features are computed directly
from the caller-supplied real light curve results -- none are synthetic.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from techno_search.photometry.aperiodic_dip import DipEvent
from techno_search.photometry.bls_detection import BlsTransitResult
from techno_search.photometry.transit_shape import TransitShapeResult
from techno_search.schemas import Candidate, FeatureValue, Track

# Heuristic scaling constants for combining real statistics into the
# interpretable v0/v1 scorer's [0, 1] feature range. These are the same kind
# of fixed scaling divisors already used throughout scoring.py (e.g. SNR/50,
# drift/5, bandwidth/9) -- reasonable, documented scale choices for combining
# unbounded real statistics into a bounded score, not calibrated detection
# thresholds and not claims about astrophysical significance.
_DEPTH_SNR_DIVISOR = 20.0
_SHAPE_IRREGULARITY_CV_DIVISOR = 2.0
_DIP_SIGNIFICANCE_DIVISOR = 15.0


def build_transit_photometry_candidate(
    candidate_id: str,
    *,
    bls_result: BlsTransitResult,
    dip_events: Sequence[DipEvent] = (),
    shape_result: TransitShapeResult | None = None,
    target_id: str = "unknown",
    ra_deg: float | None = None,
    dec_deg: float | None = None,
    cadence_count: int = 0,
    finite_cadence_fraction: float = 1.0,
    known_object_score: float = 0.0,
    source_ids: Sequence[str] = (),
    provenance: Mapping[str, FeatureValue] | None = None,
) -> Candidate:
    """Build a transit-photometry candidate from real BLS + dip-detector output."""

    depth_snr = bls_result.depth / bls_result.depth_err if bls_result.depth_err > 0.0 else 0.0

    features: dict[str, FeatureValue] = {
        "target_id": target_id,
        "bls_period_days": bls_result.period_days,
        "bls_duration_days": bls_result.duration_days,
        "bls_transit_time_value": bls_result.transit_time_value,
        "bls_transit_time_format": bls_result.transit_time_format,
        "bls_depth": bls_result.depth,
        "bls_depth_err": bls_result.depth_err,
        "bls_depth_snr": depth_snr,
        "bls_transit_count": bls_result.transit_count,
        "bls_depth_snr_score": _clamp(depth_snr / _DEPTH_SNR_DIVISOR),
        "odd_even_depth_mismatch": bls_result.odd_even_depth_mismatch(),
        "blended_eclipsing_binary_score": _clamp(bls_result.odd_even_depth_mismatch()),
        "half_period_depth_ratio": bls_result.half_period_depth_ratio(),
        "period_aliasing_score": _clamp(bls_result.half_period_depth_ratio()),
        "harmonic_delta_log_likelihood": bls_result.harmonic_delta_log_likelihood,
        "sinusoidal_variable_preferred_score": (
            1.0 if bls_result.harmonic_delta_log_likelihood > 0.0 else 0.0
        ),
        "known_object_score": _clamp(known_object_score),
        "data_quality_score": _clamp(finite_cadence_fraction),
        "provenance_completeness_score": (1.0 if provenance else 0.4),
        "cadence_count": cadence_count,
    }

    if bls_result.per_transit_log_likelihood_cv is not None:
        features["per_transit_log_likelihood_cv"] = bls_result.per_transit_log_likelihood_cv
        features["transit_shape_irregularity_score"] = _clamp(
            bls_result.per_transit_log_likelihood_cv / _SHAPE_IRREGULARITY_CV_DIVISOR
        )

    if ra_deg is not None:
        features["ra_deg"] = ra_deg
    if dec_deg is not None:
        features["dec_deg"] = dec_deg

    if shape_result is not None and shape_result.computable:
        features["transit_shape_flat_bottom_score"] = shape_result.flat_bottom_score()
        features["grazing_eclipse_score"] = shape_result.grazing_eclipse_score()
        features["transit_shape_in_transit_point_count"] = (
            shape_result.in_transit_point_count
        )

    _add_dip_features(features, dip_events)

    return Candidate(
        candidate_id=candidate_id,
        track=Track.TRANSIT_PHOTOMETRY,
        features=features,
        source_ids=tuple(source_ids or (target_id,)),
        provenance=provenance or {},
    )


def _add_dip_features(
    features: dict[str, FeatureValue],
    dip_events: Sequence[DipEvent],
) -> None:
    features["aperiodic_dip_count"] = len(dip_events)
    if not dip_events:
        features["max_dip_significance_sigma"] = 0.0
        features["max_dip_significance_score"] = 0.0
        features["asymmetric_dip_evidence_available"] = False
        return

    most_significant = max(dip_events, key=lambda event: event.significance_sigma)
    features["max_dip_significance_sigma"] = most_significant.significance_sigma
    features["max_dip_significance_score"] = _clamp(
        most_significant.significance_sigma / _DIP_SIGNIFICANCE_DIVISOR
    )
    features["max_dip_depth"] = most_significant.depth
    features["max_dip_duration_days"] = most_significant.duration_days

    if most_significant.ingress_egress_asymmetry is not None:
        features["asymmetric_dip_evidence_available"] = True
        features["max_dip_ingress_egress_asymmetry"] = (
            most_significant.ingress_egress_asymmetry
        )
        features["asymmetric_ingress_egress_score"] = _clamp(
            most_significant.ingress_egress_asymmetry
        )
    else:
        features["asymmetric_dip_evidence_available"] = False


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))
