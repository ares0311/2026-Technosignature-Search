from __future__ import annotations

from techno_search.photometry.aperiodic_dip import DipEvent
from techno_search.photometry.bls_detection import BlsTransitResult
from techno_search.photometry.prototype import build_transit_photometry_candidate
from techno_search.photometry.transit_shape import TransitShapeResult
from techno_search.schemas import Track


def _clean_bls_result() -> BlsTransitResult:
    return BlsTransitResult(
        period_days=3.5,
        duration_days=0.1,
        transit_time_value=1234.5,
        transit_time_format="btjd",
        max_power=0.002,
        depth=0.01,
        depth_err=0.0005,
        depth_odd=0.0101,
        depth_odd_err=0.0007,
        depth_even=0.0099,
        depth_even_err=0.0007,
        depth_half=0.0002,
        depth_half_err=0.0006,
        harmonic_amplitude=0.0002,
        harmonic_delta_log_likelihood=-0.5,
        transit_count=7,
        per_transit_log_likelihood_cv=0.05,
    )


def test_build_candidate_has_transit_photometry_track_and_real_features() -> None:
    candidate = build_transit_photometry_candidate(
        "tic-12345-sector-10",
        bls_result=_clean_bls_result(),
        target_id="TIC 12345",
        ra_deg=10.5,
        dec_deg=-20.1,
        cadence_count=1000,
        finite_cadence_fraction=0.98,
        provenance={"source_file": "tic12345_s10_lc.fits"},
    )

    assert candidate.track == Track.TRANSIT_PHOTOMETRY
    assert candidate.features["bls_period_days"] == 3.5
    assert candidate.features["bls_depth_snr"] == 20.0
    assert candidate.features["blended_eclipsing_binary_score"] < 0.1
    assert candidate.features["sinusoidal_variable_preferred_score"] == 0.0
    assert candidate.features["ra_deg"] == 10.5
    assert candidate.features["dec_deg"] == -20.1
    assert candidate.features["aperiodic_dip_count"] == 0
    assert candidate.features["max_dip_significance_score"] == 0.0


def test_build_candidate_carries_asymmetric_dip_evidence() -> None:
    dip = DipEvent(
        start_time=100.0,
        end_time=100.5,
        duration_days=0.5,
        min_flux=0.9,
        depth=0.1,
        significance_sigma=12.0,
        cadence_count=10,
        ingress_slope=-0.5,
        egress_slope=-0.05,
        ingress_egress_asymmetry=0.8,
    )

    candidate = build_transit_photometry_candidate(
        "tic-99-sector-1",
        bls_result=_clean_bls_result(),
        dip_events=[dip],
        target_id="TIC 99",
    )

    assert candidate.features["aperiodic_dip_count"] == 1
    assert candidate.features["asymmetric_dip_evidence_available"] is True
    assert candidate.features["max_dip_ingress_egress_asymmetry"] == 0.8
    assert candidate.features["asymmetric_ingress_egress_score"] == 0.8


def test_blended_eclipsing_binary_signature_is_flagged() -> None:
    eb_like = BlsTransitResult(
        period_days=2.0,
        duration_days=0.1,
        transit_time_value=1.0,
        transit_time_format="btjd",
        max_power=0.01,
        depth=0.02,
        depth_err=0.001,
        depth_odd=0.03,
        depth_odd_err=0.001,
        depth_even=0.01,
        depth_even_err=0.001,
        depth_half=0.019,
        depth_half_err=0.001,
        harmonic_amplitude=0.0,
        harmonic_delta_log_likelihood=0.2,
        transit_count=10,
        per_transit_log_likelihood_cv=0.05,
    )

    candidate = build_transit_photometry_candidate(
        "tic-eb-1",
        bls_result=eb_like,
        target_id="TIC EB",
    )

    assert candidate.features["blended_eclipsing_binary_score"] > 0.5
    assert candidate.features["sinusoidal_variable_preferred_score"] == 1.0
    assert candidate.features["period_aliasing_score"] > 0.5


def test_transit_shape_features_injected_when_computable() -> None:
    shape_result = TransitShapeResult(
        computable=True,
        in_transit_point_count=42,
        box_model_depth=0.01,
        box_model_rss=0.001,
        triangular_model_depth=0.008,
        triangular_model_rss=0.004,
    )

    candidate = build_transit_photometry_candidate(
        "tic-shape-1",
        bls_result=_clean_bls_result(),
        shape_result=shape_result,
        target_id="TIC Shape",
    )

    assert candidate.features["transit_shape_flat_bottom_score"] == (
        shape_result.flat_bottom_score()
    )
    assert candidate.features["grazing_eclipse_score"] == shape_result.grazing_eclipse_score()
    assert candidate.features["transit_shape_in_transit_point_count"] == 42


def test_transit_shape_features_omitted_when_not_computable() -> None:
    shape_result = TransitShapeResult(computable=False, reason="too few points")

    candidate = build_transit_photometry_candidate(
        "tic-shape-2",
        bls_result=_clean_bls_result(),
        shape_result=shape_result,
        target_id="TIC Shape 2",
    )

    assert "transit_shape_flat_bottom_score" not in candidate.features
    assert "grazing_eclipse_score" not in candidate.features
